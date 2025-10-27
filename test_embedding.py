import pytest
import pytest_html
import faiss
import numpy as np

# Imports moved from main to make the test self-contained
from problem_parser import ProblemParser
from sentence_transformers import SentenceTransformer
from main import get_dual_embedding # This function is still valid to import

# Data moved from main to make the test self-contained
sample_problems = {
    1: "What is the derivative of $x^2$?",
    2: "Solve the equation $x^2 - 4 = 0$.",
    3: "Explain the Pythagorean theorem, which is $a^2 + b^2 = c^2$.",
    4: "What are the roots of the quadratic equation $x^2 - 5x + 6 = 0$?",
}
sample_ids = list(sample_problems.keys())

# Helper function for single embedding, as it's not part of the main logic
def get_single_embedding(problem_text: str, model):
    return model.encode([problem_text])[0].reshape(1, -1)

def test_dual_embedding_effectiveness(extras):
    """ 
    Tests the effectiveness of dual embedding compared to single embedding.
    The test now creates its own models and FAISS indices instead of importing them.
    """
    # --- Setup: Instantiate models and create indices inside the test ---
    parser = ProblemParser()
    embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    dimension = embedding_model.get_sentence_embedding_dimension()

    test_query = "Find the roots of the polynomial $y^2 - 4 = 0$."
    target_problem_id = 2
    
    # Create the dual embedding FAISS index for this test run
    dual_index = faiss.IndexFlatL2(dimension)
    dual_embeddings = np.vstack([get_dual_embedding(p, parser, embedding_model).reshape(1, -1) for p in sample_problems.values()])
    dual_index.add(dual_embeddings)

    # Create the single embedding FAISS index for the baseline test
    single_index = faiss.IndexFlatL2(dimension)
    single_embeddings = np.vstack([get_single_embedding(p, embedding_model) for p in sample_problems.values()])
    single_index.add(single_embeddings)

    # --- Test Dual Embedding ---
    dual_embedding_vector = get_dual_embedding(test_query, parser, embedding_model).reshape(1, -1)
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