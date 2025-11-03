import torch
import torch.optim as optim
import numpy as np
import json
import os
from gcn_model import SimpleGCN
from problem_parser import ProblemParser
from sentence_transformers import SentenceTransformer

def load_knowledge_base(knowledge_base_dir):
    """Loads the knowledge base from a directory of JSON files."""
    knowledge_base = []
    for filename in os.listdir(knowledge_base_dir):
        if filename.endswith('.json'):
            file_path = os.path.join(knowledge_base_dir, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                knowledge_base.append(json.load(f))
    return knowledge_base

def create_graph_data(knowledge_base, embedding_model):
    """Creates graph data (adjacency matrix, features, and training links) from the knowledge base."""
    parser = ProblemParser()
    concepts = sorted(list(parser.get_all_concepts(knowledge_base)))
    concept_to_idx = {concept: i for i, concept in enumerate(concepts)}
    num_concepts = len(concepts)

    # Create adjacency matrix from concept co-occurrence
    adj = torch.zeros((num_concepts, num_concepts))
    for item in knowledge_base:
        item_concepts = item.get('concepts', [])
        for i in range(len(item_concepts)):
            for j in range(i + 1, len(item_concepts)):
                c1_idx = concept_to_idx.get(item_concepts[i])
                c2_idx = concept_to_idx.get(item_concepts[j])
                if c1_idx is not None and c2_idx is not None:
                    adj[c1_idx, c2_idx] = 1
                    adj[c2_idx, c1_idx] = 1 # Symmetric

    # Add self-loops
    adj = adj + torch.eye(num_concepts)

    # Normalize adjacency matrix (symmetric normalization)
    deg = torch.sum(adj, dim=1)
    deg_inv_sqrt = torch.pow(deg, -0.5)
    deg_inv_sqrt[torch.isinf(deg_inv_sqrt)] = 0.
    adj_normalized = torch.diag(deg_inv_sqrt) @ adj @ torch.diag(deg_inv_sqrt)

    # Use sentence embeddings as features
    features = torch.zeros((num_concepts, embedding_model.get_sentence_embedding_dimension()))
    for concept, idx in concept_to_idx.items():
        features[idx] = torch.tensor(embedding_model.encode([concept])[0], dtype=torch.float32)

    # Create positive and negative training links
    positive_links = adj.nonzero().tolist()
    
    num_negative_samples = len(positive_links) * 2 # Oversample negative links
    negative_links = []
    while len(negative_links) < num_negative_samples:
        u, v = np.random.randint(0, num_concepts, 2)
        if u != v and adj[u, v] == 0:
            negative_links.append([u, v])

    return adj_normalized, features, concept_to_idx, positive_links, negative_links

def train(model, adj, features, positive_links, negative_links, epochs=100, lr=0.01):
    """Trains the GCN model using link prediction."""
    optimizer = optim.Adam(model.parameters(), lr=lr)
    loss_fn = torch.nn.BCEWithLogitsLoss()

    print("Starting GCN model training...")
    for epoch in range(epochs):
        model.train()
        optimizer.zero_grad()

        # Get embeddings for all nodes
        all_embeddings = model(features, adj)

        # Positive examples
        pos_preds = (all_embeddings[torch.tensor([link[0] for link in positive_links])] * all_embeddings[torch.tensor([link[1] for link in positive_links])]).sum(dim=1)
        pos_labels = torch.ones(len(positive_links))

        # Negative examples
        neg_preds = (all_embeddings[torch.tensor([link[0] for link in negative_links])] * all_embeddings[torch.tensor([link[1] for link in negative_links])]).sum(dim=1)
        neg_labels = torch.zeros(len(negative_links))

        # Concatenate and calculate loss
        preds = torch.cat([pos_preds, neg_preds])
        labels = torch.cat([pos_labels, neg_labels])
        
        loss = loss_fn(preds, labels)
        loss.backward()
        optimizer.step()

        if (epoch + 1) % 10 == 0:
            print(f"Epoch {epoch+1}/{epochs}, Loss: {loss.item():.4f}")

    print("Training finished.")

def main():
    """Main function to train the GCN model."""
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    KNOWLEDGE_BASE_DIR = os.path.join(SCRIPT_DIR, 'knowledge_base')
    MODEL_SAVE_PATH = os.path.join(SCRIPT_DIR, 'gcn_model.pth')

    # --- Prepare Data ---
    # Load embedding model to create features
    embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

    knowledge_base = load_knowledge_base(KNOWLEDGE_BASE_DIR)
    adj, features, concept_to_idx, pos_links, neg_links = create_graph_data(knowledge_base, embedding_model)

    # --- Initialize and Train Model ---
    input_dim = embedding_model.get_sentence_embedding_dimension() # GCN input is now sentence embedding dimension
    hidden_dim = 128 
    output_dim = embedding_model.get_sentence_embedding_dimension() # Match text embedding dimension
    gcn_model = SimpleGCN(input_dim=input_dim, hidden_dim=hidden_dim, output_dim=output_dim)
    
    train(gcn_model, adj, features, pos_links, neg_links)

    # --- Save Model ---
    torch.save(gcn_model.state_dict(), MODEL_SAVE_PATH)
    print(f"Trained GCN model saved to {MODEL_SAVE_PATH}")

    # --- Save concept_to_idx mapping ---
    mapping_path = os.path.join(SCRIPT_DIR, 'concept_to_idx.json')
    with open(mapping_path, 'w', encoding='utf-8') as f:
        json.dump(concept_to_idx, f, ensure_ascii=False, indent=4)
    print(f"Concept to index mapping saved to {mapping_path}")

if __name__ == '__main__':
    main()
