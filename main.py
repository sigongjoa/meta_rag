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
llm = ChatOpenAI()

# Pre-compute embeddings and create FAISS index
sample_texts = [parser.parse_problem(p)["text"] for p in sample_problems.values()]
sample_embeddings = embedding_model.encode(sample_texts)
sample_ids = list(sample_problems.keys())
dimension = sample_embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(sample_embeddings)

print("FAISS index created and models loaded.")

# --- LangChain Setup ---
prompt = ChatPromptTemplate.from_template(
    """You are an expert math tutor. A student asked the following question:
    Question: {question}

    You found a very similar problem that was solved before. Here is the similar problem:
    Similar Problem: {similar_problem}

    Based on the similar problem, generate a step-by-step thought process to help the student solve their original question. 
    Explain the reasoning at each step. Do not solve the problem directly, but guide them.
    
    Your generated thought process:"""
)
chain = prompt | llm | StrOutputParser()

# --- API Endpoints ---
@app.get("/")
def read_root():
    return {"status": "Meta-RAG API is running"}

@app.post("/solve")
async def solve_problem(input: ProblemInput):
    # 1. Parse
    parsed_input = parser.parse_problem(input.problem_text)
    
    # 2. Embed
    input_embedding = embedding_model.encode([parsed_input["text"]])
    
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
