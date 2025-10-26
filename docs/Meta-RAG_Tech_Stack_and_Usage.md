# Meta-RAG v2: 기술 스택 및 주요 라이브러리

이 문서는 Meta-RAG v2 아키텍처를 구성하는 주요 기술 스택, 라이브러리, 그리고 외부 서비스에 대해 설명합니다. 각 구성 요소의 역할과 선택 이유를 명확히 하여 프로젝트에 대한 기술적 이해를 돕는 것을 목표로 합니다.

## 1. 아키텍처 및 인프라 (Architecture & Infrastructure)

| 기술 / 서비스 | 역할 및 사용법 |
| :--- | :--- |
| **GCP Cloud Run** | 사용자의 요청을 받아 다른 서비스들을 조율하는 경량 **오케스트레이터(Orchestrator)** 역할을 수행합니다. Stateless 애플리케이션으로 배포되어 빠른 수평 확장이 가능합니다. |
| **GCP Vertex AI** | 핵심 ML 연산을 담당하는 완전 관리형 AI 플랫폼입니다.<br> - **Endpoint**: `SentenceTransformer`와 같은 커스텀 모델을 서빙합니다.<br> - **Matching Engine**: 대규모 벡터 인덱스를 관리하고 유사도 검색을 수행합니다. |
| **Neo4j AuraDB** | 완전 관리형 그래프 데이터베이스 서비스입니다. 영속성이 보장되며, 실시간으로 그래프 데이터를 읽고 쓸 수 있습니다. |
| **GCP API Gateway** | API의 진입점(Entrypoint)으로, JWT 기반의 사용자 인증/인가를 전담합니다. |
| **Cloudflare** | 글로벌 엣지 네트워크로, 시스템의 최전방에서 WAF(웹 방화벽), DDoS 방어, 캐싱 등 보안 및 성능 최적화를 담당합니다. |
| **Terraform** | **IaC(Infrastructure as Code)** 도구입니다. GCP의 모든 인프라 리소스(Cloud Run, Vertex AI, API Gateway 등)를 코드로 정의하고, 버전 관리하며, 자동으로 프로비저닝합니다. |
| **Docker** | Cloud Run에서 실행될 FastAPI 애플리케이션을 컨테이너 이미지로 패키징하는 데 사용됩니다. |
| **GitHub Actions** | 코드 변경 시 자동으로 테스트, 빌드, 인프라 배포(`terraform apply`)를 수행하는 CI/CD 파이프라인을 구축하는 데 사용됩니다. |

## 2. 백엔드 애플리케이션 (Backend Application)

| 기술 / 라이브러리 | 역할 및 사용법 |
| :--- | :--- |
| **FastAPI** | Python 기반의 고성능 웹 프레임워크입니다. Cloud Run에서 실행될 오케스트레이터 API 서버를 구축하는 데 사용됩니다. |
| **Uvicorn** | FastAPI 애플리케이션을 실행하는 ASGI 서버입니다. |
| **`google-cloud-aiplatform`** | FastAPI 애플리케이션이 GCP의 Vertex AI 서비스(Endpoint, Matching Engine)와 통신하기 위해 사용하는 공식 Python 클라이언트 라이브러리입니다. |
| **`neo4j`** | FastAPI 애플리케이션이 Neo4j AuraDB와 통신하기 위한 공식 Python 드라이버입니다. |

## 3. API 명세 및 테스트 (API Spec & Testing)

| 기술 / 라이브러리 | 역할 및 사용법 |
| :--- | :--- |
| **OpenAPI (Swagger)** | API의 '계약서' 역할을 하는 명세서를 작성하는 표준입니다. `openapi.yaml` 파일을 통해 API의 모든 것을 정의합니다. |
| **Pytest (`pytest`)** | Python 코드의 정확성과 무결성을 검증하기 위한 테스트 프레임워크입니다. CI 파이프라인에서 자동으로 실행됩니다. |

## 4. 프로토타입 및 초기 개발용 기술

| 기술 / 라이브러리 | 역할 및 사용법 |
| :--- | :--- |
| **FAISS (`faiss-cpu`)** | 로컬 환경이나 초기 PoC 단계에서 벡터 검색 기능을 빠르게 구현하기 위해 사용되었던 라이브러리입니다. v2 아키텍처에서는 **Vertex AI Matching Engine**으로 대체됩니다. |
| **NetworkX (`networkx`)** | 로컬 환경이나 초기 PoC 단계에서 인메모리 그래프를 다루기 위해 사용되었던 라이브러리입니다. v2 아키텍처에서는 **Neo4j AuraDB**로 대체됩니다. |
