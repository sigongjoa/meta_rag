import os
import time
import numpy as np
from google.cloud import aiplatform
from google.cloud.aiplatform_v1.services.index_service import IndexServiceClient
from google.cloud.aiplatform_v1.types import IndexDatapoint, UpsertDatapointsRequest
from sentence_transformers import SentenceTransformer
from problem_parser import ProblemParser
from main import get_dual_embedding

# --- Configuration ---
INDEX_ENDPOINT_ID = os.getenv("INDEX_ENDPOINT_ID", "2761181560601313280")
# This is the ID of the INDEX itself, not the endpoint. Needed for the low-level client.
INDEX_ID = "3828789758985764864"
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "meta-476400")
REGION = "asia-northeast3"

def test_upsert_new_datapoint():
    """Tests adding a completely new datapoint to the index."""
    print("\n--- Testing: Add New Datapoint ---")
    
    # --- Initialize Clients ---
    # High-level client for reading/searching
    aiplatform.init(project=PROJECT_ID, location=REGION)
    index_endpoint_for_reading = aiplatform.MatchingEngineIndexEndpoint(
        index_endpoint_name=INDEX_ENDPOINT_ID
    )
    
    # Low-level client for writing/upserting
    client_options = {"api_endpoint": f"{REGION}-aiplatform.googleapis.com"}
    write_client = IndexServiceClient(client_options=client_options)

    parser = ProblemParser()
    embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

    # --- 1. Define and embed a new data point ---
    new_problem_id = "kb-new-001"
    new_problem_text = "What is the integral of 2x?"
    
    print(f"Creating new datapoint with ID: {new_problem_id}")
    new_embedding = get_dual_embedding(new_problem_text, parser, embedding_model)
    
    new_datapoint = IndexDatapoint(
        datapoint_id=new_problem_id,
        feature_vector=new_embedding.tolist()
    )

    # --- 2. Upsert to the index using the low-level client ---
    print("Upserting new datapoint to the index...")
    upsert_request = UpsertDatapointsRequest(
        index=write_client.index_path(PROJECT_ID, REGION, INDEX_ID),
        datapoints=[new_datapoint]
    )
    write_client.upsert_datapoints(request=upsert_request)
    
    # It takes time for the upsert to be reflected in the index.
    print("Waiting for 20 seconds for the index to update...")
    time.sleep(20)

    # --- 3. Query to verify the new data point using the high-level client ---
    print("Querying the index to verify the new datapoint...")
    
    response = index_endpoint_for_reading.find_neighbors(
        queries=[new_embedding.tolist()],
        num_neighbors=1
    )
    
    # --- 4. Assert the result ---
    assert response, "Query returned no response."
    assert len(response[0]) > 0, "Query returned no neighbors."
    
    retrieved_neighbor = response[0][0]
    print(f"Nearest neighbor found: ID={retrieved_neighbor.id}, Distance={retrieved_neighbor.distance:.4f}")
    
    assert retrieved_neighbor.id == new_problem_id, f"Expected to find ID {new_problem_id}, but found {retrieved_neighbor.id}"
    
    print("✅ Test passed: Successfully added and retrieved a new datapoint.")

if __name__ == '__main__':
    test_upsert_new_datapoint()
