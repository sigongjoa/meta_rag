# Meta-RAG v2: 프로덕션 배포 전략 (AWS)

이 문서는 Meta-RAG 프로젝트의 v2 아키텍처를 AWS(Amazon Web Services)에 배포하는 전략을 설명합니다. 기존 GCP 아키텍처와의 이원화를 통해 멀티 클라우드 환경을 구축하고, 안정성과 확장성을 높이는 것을 목표로 합니다.

## 1. 핵심 전략: Managed Service 우선 아키텍처

GCP 전략과 마찬가지로, AWS에서도 무거운 연산과 상태(State)를 애플리케이션에서 분리하여, AWS가 제공하는 **완전 관리형 서비스(Fully Managed Service)**에 위임하는 것을 핵심 전략으로 삼습니다.

## 2. AWS 아키텍처 구성 요소 (제안)

| 구분 | 기술 | 역할 및 선택 이유 |
| :--- | :--- | :--- |
| **Orchestrator** | **AWS App Runner** 또는 **AWS Fargate** | 사용자의 요청을 받아 각 Managed Service를 순서대로 호출하는 경량 FastAPI 애플리케이션입니다. Stateless 하므로 수평 확장이 매우 빠르고 효율적입니다. |
| **Embedding Service** | **Amazon SageMaker Endpoint** | `SentenceTransformer` 모델을 서빙하는 전용 엔드포인트입니다. AWS가 직접 확장성, 가용성, 성능을 관리하여, 동시 접속자가 많아져도 안정적인 임베딩 성능을 보장합니다. |
| **Vector Database** | **Amazon OpenSearch Service (with k-NN)** | 대규모 벡터 인덱스를 관리하고 유사도 검색을 수행하는 완전 관리형 서비스입니다. |
| **Graph Database** | **Neo4j AuraDB on AWS** | 완전 관리형 그래프 데이터베이스 서비스입니다. GCP와 동일한 Neo4j AuraDB를 사용하여 데이터 일관성을 유지합니다. |
| **API Gateway** | **Amazon API Gateway** | 시스템의 공식적인 진입점(Entrypoint) 역할을 하며, JWT 기반의 사용자 인증 및 인가를 전담합니다. |
| **Edge Security** | **AWS CloudFront + AWS WAF** | 시스템의 최전방에서 WAF(웹 방화벽), DDoS 방어, 캐싱 등 글로벌 보안 및 성능 최적화를 담당합니다. |
| **IaC & CI/CD** | **Terraform & GitHub Actions** | 모든 AWS 인프라를 코드로 관리(IaC)하고, 코드 변경 시 자동으로 테스트 및 배포하는 CI/CD 파이프라인을 구축합니다. |

## 3. 다음 단계

1.  **Terraform 코드 수정:** `terraform/` 디렉토리에 AWS provider를 추가하고, 위 아키텍처에 맞는 리소스를 정의합니다.
2.  **CI/CD 파이프라인 수정:** `.github/workflows/ci.yml` 파일에 AWS 배포를 위한 새로운 job을 추가합니다.
3.  **애플리케이션 코드 수정:** AWS 서비스와 통신하기 위한 클라이언트 라이브러리 (e.g., `boto3`)를 추가하고, 관련 코드를 수정합니다.
