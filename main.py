import os
from fastapi import FastAPI, Request
from pydantic import BaseModel
from contextlib import asynccontextmanager

from problem_parser import ProblemParser
from sentence_transformers import SentenceTransformer
import numpy as np
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
from langchain_community.llms.huggingface_pipeline import HuggingFacePipeline
from google.cloud import aiplatform
import google.auth

# --- PoC Sample Data ---
sample_problems = {
    1: "What is the derivative of $x^2$?",
    2: "Solve the equation $x^2 - 4 = 0$.",
    3: "Explain the Pythagorean theorem, which is $a^2 + b^2 = c^2$.",
    4: "What are the roots of the quadratic equation $x^2 - 5x + 6 = 0$?",
}

# --- Helper function for Dual Embedding ---
def get_dual_embedding(problem_text: str, parser: ProblemParser, model: SentenceTransformer):
    parsed_problem = parser.parse_problem(problem_text)
    text_embedding = model.encode([parsed_problem["text"]])[0]
    
    formula_embeddings = []
    if parsed_problem["formulas"]:
        formula_embeddings = model.encode(parsed_problem["formulas"])
    
    if len(formula_embeddings) > 0:
        avg_formula_embedding = np.mean(formula_embeddings, axis=0)
        combined_embedding = np.mean([text_embedding, avg_formula_embedding], axis=0)
    else:
        combined_embedding = text_embedding
        
    return combined_embedding

# --- Model and Client Loading Logic (within lifespan) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load all models and clients on startup
    print("Loading embedding and parsing models...")
    app.state.parser = ProblemParser()
    app.state.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    print("Embedding and parsing models loaded.")

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

    print("Initializing Vertex AI Client...")
    INDEX_ENDPOINT_ID = os.getenv("INDEX_ENDPOINT_ID")
    if INDEX_ENDPOINT_ID:
        credentials, project_id = google.auth.default()
        aiplatform.init(project=project_id, location="asia-northeast3")
        app.state.index_endpoint = aiplatform.MatchingEngineIndexEndpoint(
            index_endpoint_name=INDEX_ENDPOINT_ID
        )
        print(f"Vertex AI client initialized for endpoint: {INDEX_ENDPOINT_ID}")
    else:
        app.state.index_endpoint = None
        print("Warning: INDEX_ENDPOINT_ID not set. Vertex AI client not initialized.")

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
app = FastAPI(
    title="Meta-RAG PoC API",
    version="0.5.0", # Version updated for lifespan refactor
    lifespan=lifespan
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
    index_endpoint = request.app.state.index_endpoint
    chain = request.app.state.chain

    if not index_endpoint:
        return {"error": "Vertex AI client is not initialized. Check server configuration."}

    # 1. Parse & 2. Embed (Dual Embedding)
    input_embedding = get_dual_embedding(input.problem_text, parser, embedding_model)
    
    # 3. Retrieve from Vertex AI
    k = 1
    response = index_endpoint.find_neighbors(
        queries=[input_embedding.tolist()],
        num_neighbors=k
    )
    
    # The response structure from Vertex AI is different from FAISS
    if response and response[0]:
        neighbor = response[0][0]
        most_similar_id = int(neighbor.id)
        most_similar_problem_text = sample_problems.get(most_similar_id, "Similar problem text not found.")
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