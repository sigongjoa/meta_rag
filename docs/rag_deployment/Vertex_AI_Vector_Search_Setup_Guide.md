# 가이드: PoC를 위한 Vertex AI Vector Search 설정

이 문서는 Meta-RAG PoC(Proof of Concept) 환경에서 로컬 FAISS 인덱스를 Vertex AI Vector Search로 전환하는 전체 과정을 안내합니다.

## 주요 개념

Vertex AI Vector Search를 효과적으로 사용하려면 다음 핵심 개념을 이해하는 것이 중요합니다.

*   **색인(Index)**: 벡터 데이터 자체를 담고 있는 데이터 구조입니다. `embeddings.json` 파일과 같은 원본 데이터로부터 생성됩니다. 이는 검색 대상이 되는 실제 데이터 셋입니다.
*   **색인 엔드포인트(Index Endpoint)**: 생성된 '색인'을 배포하여 애플리케이션이 네트워크를 통해 접근하고 쿼리할 수 있도록 하는 공개적인 서비스 주소(HTTP 엔드포인트)입니다. 하나의 엔드포인트에 여러 색인을 배포할 수 있습니다.
*   **`INDEX_ENDPOINT_ID`**: 색인 엔드포인트의 고유 식별자(긴 숫자 ID)입니다. 애플리케이션이 특정 엔드포인트에 연결할 때 사용됩니다.
*   **`DEPLOYED_INDEX_ID`**: 색인 엔드포인트에 배포된 특정 색인의 고유 식별자(문자열 ID)입니다. 애플리케이션이 엔드포인트에 배포된 여러 색인 중 어떤 색인을 사용할지 지정할 때 사용됩니다.

## 1. 개요

현재 PoC는 애플리케이션과 함께 패키징된 `poc_index.faiss` 파일을 사용합니다. 이 방식은 간단하지만, 실제 운영 환경에서는 확장성, 데이터 업데이트, 관리의 어려움이 있습니다.

Vertex AI Vector Search는 Google Cloud가 제공하는 완전 관리형 벡터 검색 서비스로, 이러한 문제를 해결하고 시스템을 한 단계 더 발전시킬 수 있습니다.

**목표:** 로컬 FAISS 검색 로직을 Vertex AI Vector Search 엔드포인트에 실시간으로 쿼리하는 방식으로 변경합니다.

## 2. 사전 준비사항

Vector Search 인덱스를 생성하려면 임베딩 파일이 저장될 GCS(Google Cloud Storage) 버킷이 필요합니다.

**GCP 프로젝트 ID 확인:**

다음 명령어를 터미널에서 실행하여 현재 GCP 프로젝트 ID를 확인합니다:
```bash
gcloud config get-value project
```

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

Vertex AI는 특정 JSON 형식을 사용하여 인덱스를 생성합니다. `main.py`의 샘플 데이터를 읽어 해당 형식의 임베딩 파일을 생성하는 Python 스크립트입니다. 이 스크립트를 실행하면 `embeddings.json` 파일이 생성됩니다.

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

위 스크립트로 생성된 `embeddings.json` 파일을 2단계에서 생성한 GCS 버킷의 특정 폴더로 업로드합니다. 버킷 이름은 `[GCP_PROJECT_ID]-meta-rag-data` 형식으로 사용합니다.

```bash
# embeddings.json 파일을 GCS 버킷의 embeddings 폴더로 업로드
gcloud storage cp ./embeddings.json gs://${BUCKET_NAME}/embeddings/
```

## 5. 3단계: Vertex AI Index 및 Index Endpoint 생성 (수동)

이제 Google Cloud Console을 통해 Vertex AI 색인과 색인 엔드포인트를 생성하고 배포합니다.

### 5.1 색인(Index) 생성

1.  **Google Cloud Console**에 로그인합니다.
2.  **Vertex AI > 벡터 검색(Vector Search)** 페이지로 이동합니다.
3.  **'색인 만들기(Create Index)'**를 클릭합니다.
4.  **표시 이름(Display name)**: `meta-rag-index`와 같이 식별하기 쉬운 이름을 입력합니다.
5.  **콘텐츠(Content)**: 'Cloud Storage URI'를 선택하고, `gs://[YOUR_GCP_PROJECT_ID]-meta-rag-data/embeddings/` 경로를 입력합니다. `[YOUR_GCP_PROJECT_ID]`는 실제 프로젝트 ID로 대체해야 합니다.
6.  **벡터 차원(Vector dimension)**: `384`를 입력합니다.
7.  **거리 측정 유형(Distance measure type)**: **'내적 거리(Dot product distance)'**를 선택합니다.
8.  **업데이트 방법(Update method)**: **'일괄(Batch)'**을 선택합니다.
9.  **'만들기(Create)'**를 클릭하여 색인 생성을 시작합니다. 색인 생성이 완료되고 상태가 **'준비됨(Ready)'**으로 바뀔 때까지 기다립니다.

### 5.2 색인 엔드포인트(Index Endpoint) 생성

1.  **Vertex AI > 벡터 검색(Vector Search)** 페이지에서 **'색인 엔드포인트(Index Endpoints)' 탭**으로 이동합니다.
2.  **'색인 엔드포인트 만들기(Create Index Endpoint)'**를 클릭합니다.
3.  **표시 이름(Display name)**: `meta-rag-endpoint`와 같이 식별하기 쉬운 이름을 입력합니다.
4.  **'만들기(Create)'**를 클릭합니다. 엔드포인트 생성이 완료되고 상태가 **'준비됨(Ready)'**으로 바뀔 때까지 기다립니다.

### 5.3 색인 엔드포인트에 색인 배포

1.  **Vertex AI > 벡터 검색 > 색인 엔드포인트** 탭에서 방금 만든 엔드포인트(`meta-rag-endpoint`)의 **이름을 클릭**하여 상세 페이지로 이동합니다.
2.  **'색인 배포(Deploy Index)'** 버튼을 클릭합니다.
3.  **색인 선택**: 방금 생성한 `meta-rag-index`를 선택합니다.
4.  **배포된 색인 ID(Deployed index ID)**: `deployed_meta_rag_index`와 같이 식별할 수 있는 ID를 입력합니다. **이 ID는 나중에 애플리케이션 설정에 필요하니 반드시 기억해 두세요.**
5.  머신 유형 및 기타 설정을 완료하고 **'배포(Deploy)'**를 클릭합니다. 배포가 완료되고 상태가 **'준비됨(Ready)'**으로 바뀔 때까지 기다립니다. 이 과정은 시간이 다소 소요될 수 있습니다.

## 6. 4단계: 생성된 ID 확인 및 환경 변수 설정

Vertex AI 색인 및 엔드포인트 생성이 완료되면, 애플리케이션에서 사용할 `INDEX_ENDPOINT_ID`와 `DEPLOYED_INDEX_ID`를 확인해야 합니다.

1.  **`INDEX_ENDPOINT_ID` 확인:**
    *   **Vertex AI > 벡터 검색 > 색인 엔드포인트** 탭으로 이동합니다.
    *   생성한 엔드포인트(`meta-rag-endpoint`)의 **ID (긴 숫자)**를 기록합니다. 이 값이 `INDEX_ENDPOINT_ID`입니다.

2.  **`DEPLOYED_INDEX_ID` 확인:**
    *   **Vertex AI > 벡터 검색 > 색인 엔드포인트** 탭에서 엔드포인트(`meta-rag-endpoint`)의 **이름을 클릭**하여 상세 페이지로 이동합니다.
    *   '배포된 색인' 섹션에서 `meta-rag-index`에 해당하는 **'배포된 색인 ID'**를 기록합니다. 이 값이 `DEPLOYED_INDEX_ID`입니다.

3.  **환경 변수 설정:**
    API 서버를 실행하기 전에, 이 두 ID를 환경 변수로 설정해야 합니다. 예를 들어:

    ```bash
    export INDEX_ENDPOINT_ID="[YOUR_INDEX_ENDPOINT_ID]"
    export DEPLOYED_INDEX_ID="[YOUR_DEPLOYED_INDEX_ID]"
    uvicorn main:app --host 0.0.0.0 --port 8000
    ```

    `[YOUR_INDEX_ENDPOINT_ID]`와 `[YOUR_DEPLOYED_INDEX_ID]`를 실제 값으로 대체합니다.

## 7. 5단계: Terraform 변수 설정

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

## 8. 6단계: 애플리케이션 코드 수정

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

## 9. 7단계: 문제 해결 (Troubleshooting)

Vertex AI Vector Search 설정 및 사용 중 발생할 수 있는 일반적인 문제와 해결 방법입니다.

### 9.1 `Index 'your_deployed_index_id' is not ready: no backends` 오류

*   **원인**: 이 오류는 배포된 색인이 아직 쿼리를 처리할 준비가 되지 않았음을 의미합니다. 콘솔에서 '준비됨'으로 표시되더라도, 내부적으로 리소스 프로비저닝이 완료되지 않았을 수 있습니다.
*   **해결 방법**:
    1.  **대기**: 인덱스 배포 후 완전히 활성화되기까지 시간이 다소 소요될 수 있습니다. 15~30분 정도 기다린 후 다시 시도해 보세요.
    2.  **재배포**: 엔드포인트 상세 페이지에서 해당 배포된 색인을 '배포 취소(Undeploy)'한 후, 다시 '배포(Deploy)'해 보세요. 이 과정에서 문제가 해결될 수 있습니다.
    3.  **색인 데이터 확인**: `embeddings.json` 파일의 형식이나 내용에 문제가 없는지 확인합니다. 필요한 경우 파일을 다시 생성하고 GCS에 업로드한 후, 새로운 색인을 만들어 배포해 보세요.

### 9.2 CORS (Cross-Origin Resource Sharing) 문제

*   **원인**: 웹 프론트엔드에서 API를 호출할 때 브라우저 보안 정책으로 인해 발생하는 문제입니다. API 서버가 프론트엔드의 도메인으로부터의 요청을 허용하지 않을 때 발생합니다.
*   **해결 방법**:
    *   `main.py` 파일의 FastAPI 애플리케이션에 `CORSMiddleware`가 올바르게 설정되어 있는지 확인합니다.
    *   개발 환경에서는 `allow_origins=["*"]`로 설정하여 모든 출처를 허용할 수 있습니다. (예시: `main.py` 참조)
    *   운영 환경에서는 `allow_origins`에 프론트엔드의 정확한 도메인(예: `["https://your-frontend-domain.com"]`)을 지정해야 합니다.

### 9.3 불필요한 리소스 삭제 및 비용 관리

*   **문제**: Vertex AI 색인 및 엔드포인트는 사용량에 따라 비용이 발생합니다. 불필요하게 여러 개를 생성하거나 사용하지 않는 리소스를 방치하면 예상치 못한 비용이 발생할 수 있습니다.
*   **해결 방법**:
    *   **정기적인 확인**: Google Cloud Console의 **Vertex AI > 벡터 검색** 페이지에서 '색인' 및 '색인 엔드포인트' 탭을 정기적으로 확인합니다.
    *   **불필요한 리소스 삭제**: 사용하지 않는 색인과 색인 엔드포인트는 즉시 삭제하여 비용 발생을 중단합니다. 색인을 삭제하기 전에 해당 색인이 배포된 엔드포인트에서 먼저 '배포 취소(Undeploy)'해야 합니다.
