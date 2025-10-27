# Meta-RAG v2: 프로덕션 배포 전략 (GCP)

이 문서는 Meta-RAG 프로젝트의 v2 아키텍처, 즉 프로덕션 환경을 위한 GCP(Google Cloud Platform) 배포 전략을 설명합니다. v1 설계의 한계점(확장성, MLOps, 복잡성)을 해결하고, 안정적이며 확장 가능한 시스템을 구축하는 것을 목표로 합니다.

## 1. 핵심 전략: Managed Service 우선 아키텍처

v2의 핵심 전략은 무거운 연산과 상태(State)를 애플리케이션에서 분리하여, GCP가 제공하는 **완전 관리형 서비스(Fully Managed Service)**에 위임하는 것입니다. 이를 통해 애플리케이션은 가볍고 상태가 없는(Stateless) 오케스트레이터(Orchestrator) 역할에만 집중할 수 있습니다.

-   **느린 모델 로딩 문제 해결**: 애플리케이션 시작 시 모델을 로드하는 대신, 항상 준비되어 있는(Always Hot) Vertex AI 서비스를 API로 호출합니다.
-   **데이터 병목 현상 해결**: FAISS 파일이나 인메모리 그래프 대신, API로 접근 가능한 외부 관리형 데이터베이스를 사용합니다.

## 2. v2 아키텍처 구성 요소

| 구성 요소 | 기술 | 역할 및 선택 이유 |
| :--- | :--- | :--- |
| **Orchestrator** | **Cloud Run** | 사용자의 요청을 받아 각 Managed Service를 순서대로 호출하고, 최종 응답을 조합하는 경량 FastAPI 애플리케이션입니다. Stateless 하므로 수평 확장이 매우 빠르고 효율적입니다. |
| **Embedding Service** | **Vertex AI Endpoint** | `SentenceTransformer` 모델을 서빙하는 전용 엔드포인트입니다. GCP가 직접 확장성, 가용성, 성능을 관리하여, 동시 접속자가 많아져도 안정적인 임베딩 성능을 보장합니다. |
| **Vector Database** | **Vertex AI Matching Engine** | 수십억 개의 벡터를 지원하는 완전 관리형 유사도 검색 서비스입니다. 데이터 업데이트가 API를 통해 실시간으로 가능하여, MLOps 파이프라인 구축의 핵심 요소가 됩니다. |
| **Graph Database** | **Neo4j AuraDB on GCP** | 완전 관리형 그래프 데이터베이스 서비스입니다. 영속성이 보장되며, 데이터 변경이 즉시 모든 애플리케이션 인스턴스에 반영됩니다.<br><br>**[PoC 범위 제외]** 초기 PoC 단계에서는 제외하고, 향후 프로덕션 단계에서 도입 예정. |
| **API Gateway** | **GCP API Gateway** | 시스템의 공식적인 진입점(Entrypoint) 역할을 하며, JWT 기반의 사용자 인증 및 인가를 전담합니다. |
| **Edge Security** | **Cloudflare** | GCP API Gateway 앞단에 위치하여, WAF(웹 방화벽), DDoS 방어, 캐싱 등 글로벌 보안 및 성능 최적화를 담당합니다. |
| **IaC & CI/CD** | **Terraform & GitHub Actions** | 모든 GCP 인프라를 코드로 관리(IaC)하고, 코드 변경 시 자동으로 테스트 및 배포하는 CI/CD 파이프라인을 구축합니다. |

## 3. v1 대비 개선점

-   **확장성**: 50명 이상의 동시 접속자가 발생해도, 경량 Cloud Run 인스턴스와 자동 확장되는 Vertex AI 서비스들이 트래픽을 안정적으로 처리합니다. 더 이상 콜드 스타트가 주요 문제가 아닙니다.
-   **MLOps**: 데이터(벡터, 그래프)가 외부 DB로 분리되어, 애플리케이션 재배포 없이도 실시간 데이터 업데이트가 가능한 MLOps 환경이 마련되었습니다.
-   **단순성 및 관심사 분리**: 각 컴포넌트의 역할이 명확해졌습니다. Cloudflare(보안), API Gateway(인증), Cloud Run(비즈니스 로직), Vertex AI(ML 서빙) 등 각자의 책임에만 집중하여 시스템 전체의 복잡성이 감소하고 유지보수성이 향상됩니다.
-   **유연성**: 인프라 설정이 Terraform 코드로 관리되어, 리소스 변경(메모리, CPU 등)이 필요할 때 코드 수정 및 `terraform apply` 명령어로 쉽고 안전하게 적용할 수 있습니다.