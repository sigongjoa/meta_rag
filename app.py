import streamlit as st
import requests
import json

st.set_page_config(layout="wide")

st.title("Meta-RAG Math Tutor")

st.markdown("""
This application demonstrates a Retrieval-Augmented Generation (RAG) system for math problems.
It uses a dual embedding approach (text + graph-based GCN) to retrieve similar problems 
and then generates a step-by-step thought process using a local LLM.
""")

# --- Configuration ---
FASTAPI_URL = "http://localhost:8000/solve"

# --- User Input ---
st.header("Ask a Math Problem")
problem_query = st.text_area("Enter your math problem here:", "이차방정식 $x^2 - 4x + 4 = 0$의 해를 구하시오.", height=150)

if st.button("Get Guidance"):
    if problem_query:
        with st.spinner("Searching for similar problems and generating guidance..."):
            try:
                response = requests.post(FASTAPI_URL, json={"problem_text": problem_query})
                response.raise_for_status() # Raise an exception for HTTP errors
                result = response.json()

                st.subheader("Retrieved Similar Problem")
                if result['retrieved_similar_problem']['id'] != -1:
                    st.write(f"**ID:** {result['retrieved_similar_problem']['id']}")
                    st.latex(result['retrieved_similar_problem']['text'])
                else:
                    st.info("No similar problem found.")

                st.subheader("Generated Thought Process")
                st.markdown(result['generated_thought_process'])

            except requests.exceptions.ConnectionError:
                st.error("Could not connect to the FastAPI backend. Please ensure it is running at `http://localhost:8000`.")
            except requests.exceptions.HTTPError as e:
                st.error(f"HTTP Error: {e}. Response: {e.response.text}")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")
    else:
        st.warning("Please enter a math problem to get guidance.")
