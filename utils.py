import torch
import numpy as np
from typing import Dict, Any
from sentence_transformers import SentenceTransformer
from problem_parser import ProblemParser
from gcn_model import SimpleGCN

def get_dual_embedding(problem: Dict[str, Any], parser: ProblemParser, text_embedding_model: SentenceTransformer, gcn_model: SimpleGCN, concept_to_idx: Dict[str, int], gcn_concept_embeddings: torch.Tensor, alpha: float = 0.5):
    # 1. Get text embedding
    parsed_text = problem.get('parsed_text', problem.get('text', ''))
    text_embedding = text_embedding_model.encode([parsed_text])[0]

    # 2. Get GCN embedding for the problem's concepts
    problem_concepts = problem.get('concepts', [])
    if problem_concepts:
        # Get indices of concepts present in the problem
        concept_indices = [concept_to_idx[c] for c in problem_concepts if c in concept_to_idx]
        if concept_indices:
            # Average the GCN embeddings of the problem's concepts
            graph_embedding = torch.mean(gcn_concept_embeddings[concept_indices], dim=0).detach().numpy()
        else:
            # If no known concepts, use a zero vector
            graph_embedding = np.zeros(gcn_model.output_dim) # Use output_dim from GCN model
    else:
        # If no concepts in the problem, use a zero vector
        graph_embedding = np.zeros(gcn_model.output_dim) # Use output_dim from GCN model

    # 3. Combine embeddings based on alpha
    if alpha == 1.0:
        combined_embedding = text_embedding
    elif alpha == 0.0:
        combined_embedding = graph_embedding
    else:
        # Ensure dimensions match for weighted sum
        if text_embedding.shape[0] != graph_embedding.shape[0]:
            # If dimensions don't match, concatenate as a fallback or raise an error
            # For now, we'll concatenate and log a warning
            print("Warning: Text and graph embedding dimensions do not match for weighted sum. Concatenating instead.")
            combined_embedding = np.concatenate([text_embedding, graph_embedding])
        else:
            combined_embedding = alpha * text_embedding + (1 - alpha) * graph_embedding
    
    return combined_embedding