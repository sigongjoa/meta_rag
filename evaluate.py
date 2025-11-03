
import json
import numpy as np
import faiss
import os
from sentence_transformers import SentenceTransformer
from problem_parser import ProblemParser
from main import get_dual_embedding # Assuming get_dual_embedding is accessible

def load_data(knowledge_base_path, golden_queries_path):
    """Loads the knowledge base and golden queries from JSON files."""
    print(f"Loading knowledge base from {knowledge_base_path}...")
    with open(knowledge_base_path, 'r', encoding='utf-8') as f:
        knowledge_base = json.load(f)
    
    print(f"Loading golden queries from {golden_queries_path}...")
    with open(golden_queries_path, 'r', encoding='utf-8') as f:
        golden_queries = json.load(f)
        
    return knowledge_base, golden_queries

def build_index(knowledge_base, embedding_model, parser):
    """Builds a FAISS index from the knowledge base."""
    print("Building FAISS index...")
    
    # Extract embeddings and IDs
    embeddings = []
    ids = [item['id'] for item in knowledge_base]
    
    for item in knowledge_base:
        # This assumes the embedding function takes the full item, or just the text.
        # We might need to adapt this based on the model.
        # For now, let's assume it uses the same logic as the PoC.
        embedding = get_dual_embedding(item['problem_text'], parser, embedding_model)
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

def run_evaluation(index, id_map, golden_queries, embedding_model, parser, k=10):
    """Runs evaluation and calculates P'@k."""
    print(f"Running evaluation for {len(golden_queries)} queries...")
    
    total_precision_at_k = 0
    
    for query in golden_queries:
        query_text = query['query_text']
        ground_truth_ids = set(query['ground_truth_ids'])
        
        # Get embedding for the query
        query_embedding = get_dual_embedding(query_text, parser, embedding_model)
        query_embedding = np.array([query_embedding]).astype('float32')
        
        # Search the index
        distances, indices = index.search(query_embedding, k)
        
        # Map FAISS indices back to our string IDs
        retrieved_ids = [id_map[i] for i in indices[0] if i != -1]
        
        # Calculate precision at k
        retrieved_set = set(retrieved_ids)
        hits = len(ground_truth_ids.intersection(retrieved_set))
        precision_at_k = hits / k
        
        print(f"Query: '{query_text[:50]}...' -> P@{k}: {precision_at_k:.2f}")
        total_precision_at_k += precision_at_k
        
    mean_precision_at_k = total_precision_at_k / len(golden_queries)
    return mean_precision_at_k

def main():
    """Main function to run the evaluation pipeline."""
    
    # --- Configuration ---
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    KNOWLEDGE_BASE_PATH = os.path.join(SCRIPT_DIR, 'knowledge_base.json')
    GOLDEN_QUERIES_PATH = os.path.join(SCRIPT_DIR, 'golden_queries.json')
    K_FOR_METRICS = 10
    
    # --- Load Models ---
    print("Loading models...")
    embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    parser = ProblemParser()
    
    # --- Load Data ---
    # Note: These files need to be created manually first.
    # We will proceed assuming they exist for the script structure.
    try:
        knowledge_base, golden_queries = load_data(KNOWLEDGE_BASE_PATH, GOLDEN_QUERIES_PATH)
    except FileNotFoundError:
        print("\nERROR: Data files not found!")
        print(f"Please create '{KNOWLEDGE_BASE_PATH}' and '{GOLDEN_QUERIES_PATH}' according to the Data_Schema_Guide.md")
        return

    # --- Build Index ---
    index, id_map = build_index(knowledge_base, embedding_model, parser)
    
    # --- Run Evaluation ---
    mean_p_at_k = run_evaluation(index, id_map, golden_queries, embedding_model, parser, k=K_FOR_METRICS)
    
    # --- Print Results ---
    print("\n" + "="*30)
    print("  EVALUATION SUMMARY")
    print("="*30)
    print(f"  Mean P'@{K_FOR_METRICS}: {mean_p_at_k:.4f}")
    print("="*30)

if __name__ == '__main__':
    main()
