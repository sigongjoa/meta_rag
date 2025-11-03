
import torch
import argparse
import json
import numpy as np
import faiss
import os
from sentence_transformers import SentenceTransformer
from problem_parser import ProblemParser
from gcn_model import SimpleGCN
from main import get_dual_embedding # Assuming get_dual_embedding is accessible

def load_data(knowledge_base_dir, golden_queries_path):
    """Loads the knowledge base from a directory of JSON files and golden queries from a JSON file."""
    print(f"Loading knowledge base from {knowledge_base_dir}...")
    knowledge_base = []
    for filename in os.listdir(knowledge_base_dir):
        if filename.endswith('.json'):
            file_path = os.path.join(knowledge_base_dir, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                knowledge_base.append(json.load(f))

    print(f"Loading golden queries from {golden_queries_path}...")
    with open(golden_queries_path, 'r', encoding='utf-8') as f:
        golden_queries = json.load(f)
        
    return knowledge_base, golden_queries

def build_index(knowledge_base, embedding_model, parser, gcn_model, concept_to_idx):
    """Builds a FAISS index from the knowledge base."""
    print("Building FAISS index...")
    
    # Extract embeddings and IDs
    embeddings = []
    ids = [item['id'] for item in knowledge_base]
    
    # Prepare adjacency matrix for GCN
    num_concepts = len(concept_to_idx)
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
    
    # Add self-loops and normalize adjacency matrix
    adj = adj + torch.eye(num_concepts)
    deg = torch.sum(adj, dim=1)
    deg_inv_sqrt = torch.pow(deg, -0.5)
    deg_inv_sqrt[torch.isinf(deg_inv_sqrt)] = 0.
    adj_normalized = torch.diag(deg_inv_sqrt) @ adj @ torch.diag(deg_inv_sqrt)

    # Prepare concept features for GCN
    concept_features = torch.zeros((num_concepts, embedding_model.get_sentence_embedding_dimension()))
    for concept, idx in concept_to_idx.items():
        concept_features[idx] = torch.tensor(embedding_model.encode([concept])[0], dtype=torch.float32)

    # Get GCN embeddings for all concepts
    with torch.no_grad():
        gcn_concept_embeddings = gcn_model(concept_features, adj_normalized)

    for item in knowledge_base:
        embedding = get_dual_embedding(item, parser, embedding_model, gcn_model, concept_to_idx, gcn_concept_embeddings)
        embeddings.append(embedding)
        
    embeddings = np.array(embeddings).astype('float32')
    
    # Build the FAISS index
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension) # Using L2 distance for this example
    index = faiss.IndexIDMap(index)
    
    # We need a mapping from FAISS's internal IDs to our string IDs
    # For simplicity, we'll use integer indices for now and map back.
    faiss_ids = np.array(range(len(ids)))
    index.add_with_ids(embeddings, faiss_ids)
    
    # Create a mapping from faiss_ids back to our string ids
    id_map = {i: doc_id for i, doc_id in enumerate(ids)}
    
    print(f"Index built successfully with {index.ntotal} vectors.")
    return index, id_map

def run_evaluation(index, id_map, golden_queries, embedding_model, parser, gcn_model, concept_to_idx, knowledge_base, k=10):
    """Runs evaluation and calculates multiple metrics."""
    print(f"Running evaluation for {len(golden_queries)} queries with k={k}...")
    
    results = []
    total_precision_at_k = 0
    total_recall_at_k = 0
    total_mrr = 0
    total_map = 0

    # Pre-calculate GCN concept embeddings for queries as well
    # This assumes that all concepts in queries are also present in the training data
    # For a more robust solution, handle unseen concepts gracefully (e.g., zero vector)
    num_concepts = len(concept_to_idx)
    concept_features = torch.zeros((num_concepts, embedding_model.get_sentence_embedding_dimension()))
    for concept, idx in concept_to_idx.items():
        concept_features[idx] = torch.tensor(embedding_model.encode([concept])[0], dtype=torch.float32)

    # Build adjacency matrix from knowledge base for GCN concept embeddings
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

    adj = adj + torch.eye(num_concepts) # Add self-loops
    deg = torch.sum(adj, dim=1)
    deg_inv_sqrt = torch.pow(deg, -0.5)
    deg_inv_sqrt[torch.isinf(deg_inv_sqrt)] = 0.
    adj_normalized = torch.diag(deg_inv_sqrt) @ adj @ torch.diag(deg_inv_sqrt)

    with torch.no_grad():
        gcn_concept_embeddings_for_queries = gcn_model(concept_features, adj_normalized)

    for query in golden_queries:
        query_text = query['query_text']
        ground_truth_ids = set(query['ground_truth_ids'])
        
        query_problem = parser.parse_problem(query_text)
        query_problem['id'] = query['query_id']
        query_problem['problem_text'] = query_text
        query_problem['concepts'] = []

        query_embedding = get_dual_embedding(query_problem, parser, embedding_model, gcn_model, concept_to_idx, gcn_concept_embeddings_for_queries)
        query_embedding = np.array([query_embedding]).astype('float32')
        
        distances, indices = index.search(query_embedding, k)
        retrieved_ids = [id_map[i] for i in indices[0] if i != -1]
        
        retrieved_set = set(retrieved_ids)
        hits = len(ground_truth_ids.intersection(retrieved_set))
        
        # --- Calculate Metrics ---
        precision_at_k = hits / k
        recall_at_k = hits / len(ground_truth_ids) if len(ground_truth_ids) > 0 else 0
        
        # MRR
        mrr_score = 0
        for i, doc_id in enumerate(retrieved_ids):
            if doc_id in ground_truth_ids:
                mrr_score = 1 / (i + 1)
                break
        
        # MAP
        ap_score = 0
        hits_so_far = 0
        for i, doc_id in enumerate(retrieved_ids):
            if doc_id in ground_truth_ids:
                hits_so_far += 1
                ap_score += hits_so_far / (i + 1)
        ap_score = ap_score / len(ground_truth_ids) if len(ground_truth_ids) > 0 else 0

        query_result = {
            'query_id': query['query_id'],
            'query_text': query_text,
            'ground_truth_ids': list(ground_truth_ids),
            'retrieved_ids': retrieved_ids,
            'precision_at_k': precision_at_k,
            'recall_at_k': recall_at_k,
            'mrr': mrr_score,
            'average_precision': ap_score
        }
        results.append(query_result)

        total_precision_at_k += precision_at_k
        total_recall_at_k += recall_at_k
        total_mrr += mrr_score
        total_map += ap_score

        print(f"Query: '{query_text[:30]}...' -> P@{k}: {precision_at_k:.2f}, R@{k}: {recall_at_k:.2f}, MRR: {mrr_score:.2f}, AP: {ap_score:.2f}")

    mean_precision_at_k = total_precision_at_k / len(golden_queries)
    mean_recall_at_k = total_recall_at_k / len(golden_queries)
    mean_mrr = total_mrr / len(golden_queries)
    mean_map = total_map / len(golden_queries)

    summary = {
        'k': k,
        'num_queries': len(golden_queries),
        'mean_precision_at_k': mean_precision_at_k,
        'mean_recall_at_k': mean_recall_at_k,
        'mrr': mean_mrr,
        'map': mean_map
    }

    return summary, results

import argparse

def main():
    """Main function to run the evaluation pipeline."""
    
    parser = argparse.ArgumentParser(description='Run evaluation for the Meta-RAG model.')
    parser.add_argument('-k', type=int, default=10, help='The number of documents to retrieve for each query.')
    parser.add_argument('--output_path', type=str, default='evaluation_results.json', help='Path to save the evaluation results JSON file.')
    args = parser.parse_args()

    # --- Configuration ---
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    KNOWLEDGE_BASE_PATH = os.path.join(SCRIPT_DIR, 'knowledge_base')
    GOLDEN_QUERIES_PATH = os.path.join(SCRIPT_DIR, 'golden_queries.json')
    MODEL_SAVE_PATH = os.path.join(SCRIPT_DIR, 'gcn_model.pth')
    MAPPING_PATH = os.path.join(SCRIPT_DIR, 'concept_to_idx.json')
    K_FOR_METRICS = args.k
    
    # --- Load Models ---
    print("Loading models...")
    embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    parser = ProblemParser()
    
    # Determine input_dim for GCN from the number of unique concepts
    # This requires loading concept_to_idx first to get the number of concepts
    input_dim = embedding_model.get_sentence_embedding_dimension() # Assuming SentenceTransformer output size is 384
    gcn_model = SimpleGCN(input_dim=input_dim, hidden_dim=128, output_dim=embedding_model.get_sentence_embedding_dimension())
    gcn_model.load_state_dict(torch.load(MODEL_SAVE_PATH))
    gcn_model.eval() # Set to evaluation mode

    with open(MAPPING_PATH, 'r', encoding='utf-8') as f:
        concept_to_idx = json.load(f)

    # --- Load Data ---
    try:
        knowledge_base, golden_queries = load_data(KNOWLEDGE_BASE_PATH, GOLDEN_QUERIES_PATH)
    except FileNotFoundError:
        print(f"\nERROR: Data files not found! Please check the paths.")
        return

    # --- Build Index ---
    index, id_map = build_index(knowledge_base, embedding_model, parser, gcn_model, concept_to_idx)
    
    # --- Run Evaluation ---
    summary, results = run_evaluation(index, id_map, golden_queries, embedding_model, parser, gcn_model, concept_to_idx, knowledge_base, k=K_FOR_METRICS)
    
    # --- Save Results ---
    output_data = {
        'summary': summary,
        'results': results
    }
    
    with open(args.output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=4)

    # --- Print Summary ---
    print("\n" + "="*40)
    print("        EVALUATION SUMMARY")
    print("="*40)
    for key, value in summary.items():
        print(f"  {key:<25}: {value:.4f}")
    print("="*40)
    print(f"\nDetailed results saved to: {args.output_path}")

if __name__ == '__main__':
    main()
