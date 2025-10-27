# create_embeddings.py
import json
import numpy as np
from sentence_transformers import SentenceTransformer
from problem_parser import ProblemParser

# main.py에 정의된 샘플 데이터와 동일
sample_problems = {
    1: "What is the derivative of $x^2$?",
    2: "Solve the equation $x^2 - 4 = 0$.",
    3: "Explain the Pythagorean theorem, which is $a^2 + b^2 = c^2$.",
    4: "What are the roots of the quadratic equation $x^2 - 5x + 6 = 0$?"
}

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
        
    return combined_embedding.tolist() # JSON 직렬화를 위해 tolist() 사용

def main():
    print("Loading models...")
    embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    parser = ProblemParser()
    
    output_data = []
    final_embedding_vector = []
    
    print("Generating embeddings for sample problems...")
    for problem_id, problem_text in sample_problems.items():
        embedding_vector = get_dual_embedding(problem_text, parser, embedding_model)
        final_embedding_vector = embedding_vector # 마지막 벡터를 저장해둠
        
        # Vertex AI가 요구하는 JSON 형식
        record = {
            "id": str(problem_id),
            "embedding": embedding_vector,
            # 검색 결과와 함께 반환받고 싶은 추가 데이터 (선택사항)
            "restricts": [
                {"namespace": "problem_text", "allow": [problem_text]}
            ]
        }
        output_data.append(json.dumps(record) + '\n')

    # 결과를 파일에 저장
    output_file = 'embeddings.json'
    with open(output_file, 'w') as f:
        f.writelines(output_data)
        
    print(f"Successfully created embeddings file: {output_file}")
    if final_embedding_vector:
        print(f"Vector dimension: {len(final_embedding_vector)}")

if __name__ == "__main__":
    main()
