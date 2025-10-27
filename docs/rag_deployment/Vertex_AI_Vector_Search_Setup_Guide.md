# 가이드: PoC를 위한 Vertex AI Vector Search 설정

이 문서는 Meta-RAG PoC(Proof of Concept) 환경에서 로컬 FAISS 인덱스를 Vertex AI Vector Search로 전환하는 전체 과정을 안내합니다.

## 1. 개요

현재 PoC는 애플리케이션과 함께 패키징된 `poc_index.faiss` 파일을 사용합니다. 이 방식은 간단하지만, 실제 운영 환경에서는 확장성, 데이터 업데이트, 관리의 어려움이 있습니다.

Vertex AI Vector Search는 Google Cloud가 제공하는 완전 관리형 벡터 검색 서비스로, 이러한 문제를 해결하고 시스템을 한 단계 더 발전시킬 수 있습니다.

**목표:** 로컬 FAISS 검색 로직을 Vertex AI Vector Search 엔드포인트에 실시간으로 쿼리하는 방식으로 변경합니다.

## 2. 사전 준비사항

Vector Search 인덱스를 생성하려면 임베딩 파일이 저장될 GCS(Google Cloud Storage) 버킷이 필요합니다.

GCP 프로젝트에서 아래 명령어를 실행하여 버킷을 생성합니다. (이미 버킷이 있다면 이 단계를 건너뛰어도 됩니다.)

```bash
# 변수 설정
export GCP_PROJECT_ID="$(gcloud config get-value project)"
export BUCKET_NAME="${GCP_PROJECT_ID}-meta-rag-data" # 버킷 이름은 전역적으로 고유해야 합니다.
export GCP_REGION="asia-northeast3"

# GCS 버킷 생성
gcloud storage buckets create gs://${BUCKET_NAME} --project=${GCP_PROJECT_ID} --location=${GCP_REGION}
```

## 3. 1단계: 임베딩 데이터 생성

Vertex AI는 특정 JSON 형식을 사용하여 인덱스를 생성합니다. `main.py`의 샘플 데이터를 읽어 해당 형식의 임베딩 파일을 생성하는 Python 스크립트입니다.

이 스크립트를 프로젝트 루트에 `create_embeddings.py` 라는 이름으로 저장하고 실행합니다.

```python
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
    4: "What are the roots of the quadratic equation $x^2 - 5x + 6 = 0$?",
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
    
    print("Generating embeddings for sample problems...")
    for problem_id, problem_text in sample_problems.items():
        embedding_vector = get_dual_embedding(problem_text, parser, embedding_model)
        
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
    print(f"Vector dimension: {len(output_data[0]['embedding'])}")

if __name__ == "__main__":
    main()
```

## 4. 2단계: GCS에 데이터 업로드

위 스크립트로 생성된 `embeddings.json` 파일을 2단계에서 생성한 GCS 버킷의 특정 폴더로 업로드합니다.

```bash
# embeddings.json 파일을 GCS 버킷의 embeddings 폴더로 업로드
gcloud storage cp ./embeddings.json gs://${BUCKET_NAME}/embeddings/
```

## 5. 3단계: Terraform 변수 설정

이제 CI/CD 파이프라인이 Vertex AI 인프라를 생성하도록 설정할 차례입니다. `.github/workflows/ci.yml` 파일의 `deploy-gcp` 작업에 다음 `env` 블록을 추가하여 Terraform에 필요한 변수들을 전달합니다.

**벡터 차원(`TF_VAR_vector_index_dimensions`)** 은 `create_embeddings.py` 실행 결과 출력된 값을 사용합니다. (`all-MiniLM-L6-v2` 모델은 384입니다.)

```yaml
# .github/workflows/ci.yml

  deploy-gcp:
    name: Build and Deploy to GCP Cloud Run
    # ... (기존 설정) ...
    env:
      # Terraform 변수를 설정합니다. TF_VAR_ 접두사를 사용해야 합니다.
      TF_VAR_vector_index_dimensions: 384
      TF_VAR_vector_index_contents_uri: "gs://${{ secrets.GCP_PROJECT_ID }}-meta-rag-data/embeddings/"
```

**참고:** 위 `TF_VAR_vector_index_contents_uri`의 버킷 이름은 2단계에서 생성한 버킷 이름과 일치해야 합니다. 여기서는 GitHub Secret을 사용하여 동적으로 구성하는 예시를 보여줍니다.

## 6. 4단계: 애플리케이션 코드 수정

마지막으로, `main.py`의 API 로직이 로컬 FAISS 대신 Vertex AI 엔드포인트를 사용하도록 수정합니다.

**변경 전 (`main.py`)**
```python
# ... (기존 코드) ...

@app.post("/solve")
async def solve_problem(input: ProblemInput):
    # 1. Parse & 2. Embed (Dual Embedding)
    input_embedding = get_dual_embedding(input.problem_text, parser, embedding_model)
    
    # 3. Retrieve
    k = 1
    distances, indices = index.search(input_embedding, k)
    most_similar_id = sample_ids[indices[0][0]]
    most_similar_problem_text = sample_problems[most_similar_id]
    
    # ... (이하 생략) ...
```

**변경 후 (`main.py`)**
```python
# ... (기존 코드) ...
from google.cloud import aiplatform
import google.auth

# ... (FAISS 관련 코드 삭제 또는 주석 처리) ...

# Vertex AI 클라이언트 초기화
credentials, project_id = google.auth.default()
aiplatform.init(project=project_id, location='asia-northeast3')

# Terraform으로 생성된 엔드포인트 ID를 환경 변수에서 읽어옵니다.
# 이 환경 변수는 Cloud Run에 직접 설정해야 합니다.
INDEX_ENDPOINT_ID = os.getenv("INDEX_ENDPOINT_ID")
index_endpoint = aiplatform.MatchingEngineIndexEndpoint(
    index_endpoint_name=INDEX_ENDPOINT_ID
)


@app.post("/solve")
async def solve_problem(input: ProblemInput):
    # 1. Parse & 2. Embed (Dual Embedding)
    input_embedding = get_dual_embedding(input.problem_text, parser, embedding_model)
    
    # 3. Retrieve from Vertex AI
    k = 1
    response = index_endpoint.find_neighbors(
        queries=[input_embedding.tolist()[0]],
        num_neighbors=k
    )
    
    # 응답 구조가 FAISS와 다릅니다.
    if response and response[0]:
        neighbor = response[0][0]
        most_similar_id = int(neighbor.id)
        # ID를 기반으로 원본 텍스트를 다시 조회해야 합니다.
        most_similar_problem_text = sample_problems[most_similar_id]
    else:
        most_similar_id = -1
        most_similar_problem_text = "No similar problem found."

    # ... (이하 생략) ...
```

이 가이드에 따라 진행하면, PoC 애플리케이션은 확장 가능하고 강력한 Vertex AI Vector Search를 백엔드로 사용하게 됩니다.
