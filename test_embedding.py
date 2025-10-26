import pytest
import pytest_html
import faiss
import numpy as np
from main import get_dual_embedding, sample_problems, parser, embedding_model, sample_ids, dimension

# Helper function for single embedding, as it's not part of the main logic
def get_single_embedding(problem_text: str, model):
    return model.encode([problem_text])[0].reshape(1, -1)

def test_dual_embedding_effectiveness(extras):
    """ 
    Tests the effectiveness of dual embedding compared to single embedding.
    """
    # --- Setup ---
    test_query = "Find the roots of the polynomial $y^2 - 4 = 0$."
    target_problem_id = 2
    
    # Load the dual embedding FAISS index created by main.py
    dual_index = faiss.read_index("poc_index.faiss")

    # Create a new FAISS index for single embeddings for the baseline test
    single_index = faiss.IndexFlatL2(dimension)
    single_embeddings = np.vstack([get_single_embedding(p, embedding_model) for p in sample_problems.values()])
    single_index.add(single_embeddings)

    # --- Test Dual Embedding ---
    dual_embedding_vector = get_dual_embedding(test_query, parser, embedding_model)
    _, dual_indices = dual_index.search(dual_embedding_vector, 1)
    retrieved_id_dual = sample_ids[dual_indices[0][0]]
    
    # --- Test Single Embedding ---
    single_embedding_vector = get_single_embedding(test_query, embedding_model)
    _, single_indices = single_index.search(single_embedding_vector, 1)
    retrieved_id_single = sample_ids[single_indices[0][0]]

    # --- Add results to HTML report ---
    extras.append(pytest_html.extras.text(f"Test Query: {test_query}"))
    extras.append(pytest_html.extras.text(f"Target Problem (ID {target_problem_id}): {sample_problems[target_problem_id]}"))
    
    html_dual = f"""
        <h2>Dual Embedding Result</h2>
        <p>Retrieved problem ID: {retrieved_id_dual}</p>
        <p>Retrieved problem text: {sample_problems[retrieved_id_dual]}</p>
        <p><b>Correct match: {retrieved_id_dual == target_problem_id}</b></p>
    """
    extras.append(pytest_html.extras.html(html_dual))

    html_single = f"""
        <h2>Single Embedding (Baseline) Result</h2>
        <p>Retrieved problem ID: {retrieved_id_single}</p>
        <p>Retrieved problem text: {sample_problems[retrieved_id_single]}</p>
        <p><b>Correct match: {retrieved_id_single == target_problem_id}</b></p>
    """
    extras.append(pytest_html.extras.html(html_single))

    # --- Assert ---
    # The main assertion is that dual embedding finds the correct match.
    assert retrieved_id_dual == target_problem_id
