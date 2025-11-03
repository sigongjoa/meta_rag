import torch
import os
from fastapi import FastAPI, Request
from pydantic import BaseModel
from contextlib import asynccontextmanager
from typing import Dict, Any
import json
import faiss

from problem_parser import ProblemParser
from gcn_model import SimpleGCN
from sentence_transformers import SentenceTransformer
import numpy as np
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
from langchain_community.llms.huggingface_pipeline import HuggingFacePipeline


# --- PoC Sample Data ---


from utils import get_dual_embedding

# --- Model and Client Loading Logic (within lifespan) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load all models and clients on startup
    print("Loading embedding and parsing models...")
    app.state.parser = ProblemParser()
    app.state.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Load trained GCN model
    input_dim = app.state.embedding_model.get_sentence_embedding_dimension() # 384
    app.state.gcn_model = SimpleGCN(input_dim=input_dim, hidden_dim=128, output_dim=64)
    gcn_model_path = os.path.join(os.path.dirname(__file__), 'gcn_model.pth')
    app.state.gcn_model.load_state_dict(torch.load(gcn_model_path))
    app.state.gcn_model.eval() # Set to evaluation mode

    # Load concept to index mapping
    concept_to_idx_path = os.path.join(os.path.dirname(__file__), 'concept_to_idx.json')
    with open(concept_to_idx_path, 'r', encoding='utf-8') as f:
        app.state.concept_to_idx = json.load(f)

    # Pre-calculate GCN concept embeddings
    num_concepts = len(app.state.concept_to_idx)
    concept_features = torch.zeros((num_concepts, input_dim))
    for concept, idx in app.state.concept_to_idx.items():
        concept_features[idx] = torch.tensor(app.state.embedding_model.encode([concept])[0], dtype=torch.float32)
    
    # Build adjacency matrix from knowledge base for GCN concept embeddings
    adj = torch.zeros((num_concepts, num_concepts))
    for item in app.state.knowledge_base:
        item_concepts = item.get('concepts', [])
        for i in range(len(item_concepts)):
            for j in range(i + 1, len(item_concepts)):
                c1_idx = app.state.concept_to_idx.get(item_concepts[i])
                c2_idx = app.state.concept_to_idx.get(item_concepts[j])
                if c1_idx is not None and c2_idx is not None:
                    adj[c1_idx, c2_idx] = 1
                    adj[c2_idx, c1_idx] = 1 # Symmetric

    adj = adj + torch.eye(num_concepts) # Add self-loops
    deg = torch.sum(adj, dim=1)
    deg_inv_sqrt = torch.pow(deg, -0.5)
    deg_inv_sqrt[torch.isinf(deg_inv_sqrt)] = 0.
    adj_normalized = torch.diag(deg_inv_sqrt) @ adj @ torch.diag(deg_inv_sqrt)

    with torch.no_grad():
        app.state.gcn_concept_embeddings = app.state.gcn_model(concept_features, adj_normalized)

    print("Embedding and parsing models loaded.")

    # --- Load Knowledge Base and Build FAISS Index ---
    print("Loading knowledge base and building FAISS index...")
    KNOWLEDGE_BASE_DIR = os.path.join(os.path.dirname(__file__), 'knowledge_base')
    knowledge_base = []
    for filename in os.listdir(KNOWLEDGE_BASE_DIR):
        if filename.endswith('.json'):
            file_path = os.path.join(KNOWLEDGE_BASE_DIR, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                knowledge_base.append(json.load(f))
    app.state.knowledge_base = knowledge_base

    # Build FAISS index
    embeddings = []
    ids = [item['id'] for item in knowledge_base]

    # Prepare adjacency matrix for GCN
    num_concepts = len(app.state.concept_to_idx)
    adj = torch.ones((num_concepts, num_concepts)) # Fully connected for initial concept embeddings
    adj = adj + torch.eye(num_concepts) # Add self-loops
    deg = torch.sum(adj, dim=1)
    deg_inv_sqrt = torch.pow(deg, -0.5)
    deg_inv_sqrt[torch.isinf(deg_inv_sqrt)] = 0.
    adj_normalized = torch.diag(deg_inv_sqrt) @ adj @ torch.diag(deg_inv_sqrt)

    with torch.no_grad():
        gcn_concept_embeddings_for_index = app.state.gcn_model(concept_features, adj_normalized)

    for item in knowledge_base:
        embedding = get_dual_embedding(item, app.state.parser, app.state.embedding_model, app.state.gcn_model, app.state.concept_to_idx, gcn_concept_embeddings_for_index)
        embeddings.append(embedding)
        
    embeddings = np.array(embeddings).astype('float32')
    
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension) # Using L2 distance for this example
    index = faiss.IndexIDMap(index)
    faiss_ids = np.array(range(len(ids)))
    index.add_with_ids(embeddings, faiss_ids)
    
    app.state.faiss_index = index
    app.state.id_map = {i: doc_id for i, doc_id in enumerate(ids)}
    print(f"FAISS index built successfully with {index.ntotal} vectors.")

    print("Loading local LLM...")
    model_id = "google/flan-t5-base"
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_id)
    pipe = pipeline(
        "text2text-generation",
        model=model,
        tokenizer=tokenizer,
        max_length=512
    )
    llm = HuggingFacePipeline(pipeline=pipe)
    app.state.llm = llm
    print("Local LLM loaded.")

    # Create LangChain chain and store it in state
    prompt = ChatPromptTemplate.from_template(
        """You are an expert math tutor. A student asked the following question:
        Question: {question}

        You found a very similar problem that was solved before. Here is the similar problem:
        Similar Problem: {similar_problem}

        Based on the similar problem, provide a step-by-step thinking process to help the student solve their original question. 
        Explain the reasoning at each step. Do not solve the problem directly, but guide them.
        
        Your generated thought process:"""
    )
    app.state.chain = prompt | app.state.llm | StrOutputParser()
    
    yield
    
    # Clean up resources if needed
    print("Cleaning up resources...")


# --- FastAPI App Setup ---
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Meta-RAG PoC API",
    version="0.5.0", # Version updated for lifespan refactor
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, OPTIONS, etc.)
    allow_headers=["*"],  # Allow all headers
)

class ProblemInput(BaseModel):
    problem_text: str

# --- API Endpoints ---
@app.get("/")
def read_root():
    return {"status": "Meta-RAG API is running"}

@app.post("/solve")
async def solve_problem(input: ProblemInput, request: Request):
    # Access models and clients from the application state
    parser = request.app.state.parser
    embedding_model = request.app.state.embedding_model
    gcn_model = request.app.state.gcn_model
    chain = request.app.state.chain
    # 1. Parse & 2. Embed (Dual Embedding)
    problem_dict = parser.parse_problem(input.problem_text)
    problem_dict['id'] = 'query' # Assign a temporary ID
    problem_dict['problem_text'] = input.problem_text
    problem_dict['concepts'] = [] # No concepts for raw query

    input_embedding = get_dual_embedding(problem_dict, parser, embedding_model, gcn_model, request.app.state.concept_to_idx, request.app.state.gcn_concept_embeddings)
    
    # 3. Retrieve from FAISS
    k = 1
    distances, indices = request.app.state.faiss_index.search(np.array([input_embedding]).astype('float32'), k)
    
    if indices[0][0] != -1:
        most_similar_id = request.app.state.id_map[indices[0][0]]
        # For now, retrieve problem text from sample_problems. In a real scenario, this would come from a knowledge base lookup.
        most_similar_problem_text = next((item['problem_text'] for item in request.app.state.knowledge_base if item['id'] == most_similar_id), "Similar problem text not found.")
    else:
        most_similar_id = -1
        most_similar_problem_text = "No similar problem found."
    # 4. Generate
    generated_thought_process = chain.invoke({
        "question": input.problem_text,
        "similar_problem": most_similar_problem_text
    })

    return {
        "message": "Successfully generated thought process using Vertex AI.",
        "received_problem": input.problem_text,
        "retrieved_similar_problem": {
            "id": most_similar_id,
            "text": most_similar_problem_text,
        },
        "generated_thought_process": generated_thought_process
    }