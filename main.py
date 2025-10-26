import os
from fastapi import FastAPI
from pydantic import BaseModel
from problem_parser import ProblemParser
from sentence_transformers import SentenceTransformer
import numpy as np
import faiss
from langchain.prompts import ChatPromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.schema.output_parser import StrOutputParser

# --- Environment and Setup ---
# Make sure to set your OPENAI_API_KEY in your environment variables
if "OPENAI_API_KEY" not in os.environ:
    print("Warning: OPENAI_API_KEY environment variable not set.")

# --- PoC Sample Data ---
sample_problems = {
    1: "What is the derivative of $x^2$?",
    2: "Solve the equation $x^2 - 4 = 0$.",
    3: "Explain the Pythagorean theorem, which is $a^2 + b^2 = c^2$.",
    4: "What are the roots of the quadratic equation $x^2 - 5x + 6 = 0$?",
}

# --- FastAPI App Setup ---
class ProblemInput(BaseModel):
    problem_text: str

app = FastAPI(
    title="Meta-RAG PoC API",
    version="0.3.0",
)

# --- Models and Data Loading on Startup ---
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
parser = ProblemParser()
# llm = ChatOpenAI() # Moved initialization to where it's used

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
        
    return combined_embedding.reshape(1, -1)

FAISS_INDEX_PATH = "poc_index.faiss"

# --- Pre-compute embeddings and create/load FAISS index ---
dimension = embedding_model.get_sentence_embedding_dimension()
sample_ids = list(sample_problems.keys())

if os.path.exists(FAISS_INDEX_PATH):
    print(f"Loading existing FAISS index from {FAISS_INDEX_PATH}.")
    index = faiss.read_index(FAISS_INDEX_PATH)
else:
    print(f"No FAISS index found. Creating a new one at {FAISS_INDEX_PATH}.")
    index = faiss.IndexFlatL2(dimension)
    all_embeddings = []
    for problem_text in sample_problems.values():
        embedding = get_dual_embedding(problem_text, parser, embedding_model)
        all_embeddings.append(embedding)
    
    sample_embeddings = np.vstack(all_embeddings)
    index.add(sample_embeddings)
    faiss.write_index(index, FAISS_INDEX_PATH)
    print(f"New FAISS index created and saved to {FAISS_INDEX_PATH}.")

print("FAISS index and models loaded.")

# --- LangChain Setup ---
prompt = ChatPromptTemplate.from_template(
    """You are an expert math tutor. A student asked the following question:
    Question: {question}

    You found a very similar problem that was solved before. Here is the similar problem:
    Similar Problem: {similar_problem}

    Based on the similar problem, provide a step-by-step thinking process to help the student solve their original question. 
    Explain the reasoning at each step. Do not solve the problem directly, but guide them.
    
    Your generated thought process:"""
)
# chain = prompt | llm | StrOutputParser() # Moved to solve_problem

# --- API Endpoints ---
@app.get("/")
def read_root():
    return {"status": "Meta-RAG API is running"}

@app.post("/solve")
async def solve_problem(input: ProblemInput):
    llm = ChatOpenAI()
    chain = prompt | llm | StrOutputParser()
    # 1. Parse & 2. Embed (Dual Embedding)
    input_embedding = get_dual_embedding(input.problem_text, parser, embedding_model)
    
    # 3. Retrieve
    k = 1
    distances, indices = index.search(input_embedding, k)
    most_similar_id = sample_ids[indices[0][0]]
    most_similar_problem_text = sample_problems[most_similar_id]
    
    # 4. Generate
    generated_thought_process = chain.invoke({
        "question": input.problem_text,
        "similar_problem": most_similar_problem_text
    })

    return {
        "message": "Successfully generated thought process.",
        "received_problem": input.problem_text,
        "retrieved_similar_problem": {
            "id": most_similar_id,
            "text": most_similar_problem_text,
        },
        "generated_thought_process": generated_thought_process
    }