# 네트워크 및 통신 아키텍처

이 문서는 Meta-RAG 시스템의 전체 네트워크 구성, 트래픽 흐름, 그리고 클라이언트-서버 간의 통신 규약(Protocol)을 정의합니다. 시스템의 보안 경계와 데이터 교환 방식을 명확히 하는 것을 목표로 합니다.

## 1. 사용자-서버 통신 규약 (Client-Server Communication Protocol)

사용자의 클라이언트(웹/모바일 앱)와 Meta-RAG 백엔드 간의 모든 통신은 다음 규칙을 따릅니다.

-   **엔드포인트 (Endpoint)**: 모든 API 요청은 Cloudflare를 통해 관리되는 단일 베이스 URL(예: `https://api.meta-rag.com/v1`)을 통해 이루어집니다.

-   **프로토콜 (Protocol)**: 모든 통신은 **HTTPS (TLS 1.2 이상)**를 통해 암호화되어 전송 중 데이터가 탈취되는 것을 방지합니다.

-   **인증 (Authentication)**:
    -   API는 **JWT(JSON Web Token)** 기반의 Bearer 인증 방식을 사용합니다.
    -   사용자는 로그인 후 발급받은 유효한 JWT를 모든 API 요청의 `Authorization: Bearer <TOKEN>` HTTP 헤더에 포함해야 합니다.
    -   이 토큰은 시스템의 관문인 Cloudflare에서 1차적으로 검증됩니다.

-   **데이터 형식 (Data Format)**:
    -   모든 요청과 응답의 본문(Body)은 **`application/json`** 형식을 사용합니다.
    -   각 엔드포인트의 구체적인 요청/응답 데이터 구조는 프로젝트의 API 명세 파일인 **`openapi.yaml`**에 엄격하게 정의되어 있으며, 모든 통신은 이 명세를 준수해야 합니다.

    -   **`/chat` 엔드포인트 통신 예시**:
        -   **요청 (Client -> Server)**
            ```json
            {
              "query": "What is Spec-driven Development?",
              "path_option": "advanced"
            }
            ```
        -   **응답 (Server -> Client)**
            ```json
            {
              "answer": "Spec-driven Development is a methodology where...",
              "sources": [...],
              "execution_path": "advanced"
            }
            ```

---

## 2. 네트워크 트래픽 흐름 (Network Traffic Flow)

![Network Architecture Diagram](https://gist.github.com/assets/3687397/98025993-32d8-473c-a77c-a411b088405c/raw/0800b3a5383951553a8828901048c7313155d34c/meta-rag-network.svg)

### 가. 인바운드 트래픽 (Inbound: 외부 -> 시스템)

-   **경로**: `사용자 -> 인터넷 -> Cloudflare -> GCP Cloud Run`
-   **원칙**: 모든 인바운드 트래픽은 반드시 **Cloudflare**를 거쳐야 합니다. GCP 리소스(Cloud Run 등)의 공개 IP로 직접 접근하는 것은 네트워크 수준에서 차단됩니다.
-   **흐름 상세**:
    1.  사용자의 HTTPS 요청이 Cloudflare 엣지에 도착합니다.
    2.  Cloudflare는 WAF(웹 방화벽), DDoS 방어 등 보안 위협을 1차적으로 필터링합니다.
    3.  Cloudflare는 `Authorization` 헤더의 JWT를 검증하여 사용자를 인증합니다.
    4.  인증된 요청은 안전한 비공개 연결을 통해 GCP 내부망에 있는 Cloud Run 서비스로 전달됩니다.

### 나. 내부 트래픽 (Internal: GCP 서비스 간)

-   **원칙**: GCP 내 서비스 간의 모든 통신은 **GCP의 비공개 내부망(VPC)**을 통해서만 이루어지며, 절대 공개 인터넷을 경유하지 않습니다.
-   **흐름 상세 (`패스 B` 기준)**:
    1.  Cloud Run 서비스는 **VPC 커넥터(VPC Connector)**를 통해 GCP 내부망(VPC)에 연결됩니다.
    2.  Vertex AI Matching Engine과 LLM Endpoint는 **프라이빗 엔드포인트(Private Endpoint)**로 배포되어, 내부망에서만 접근 가능한 비공개 IP 주소를 갖습니다.
    3.  Cloud Run은 이 비공개 IP를 사용하여 Vertex AI 서비스들을 호출합니다.
    4.  이 통신은 **IAM 서비스 계정**을 통해 다시 한번 강력하게 인증 및 인가됩니다.

### 다. 아웃바운드 트래픽 (Egress: 시스템 -> 외부)

-   **설명**: Cloud Run 서비스가 외부 인터넷(예: 다른 회사의 API 호출, 웹 크롤링)으로 요청을 보내야 할 경우의 통신입니다.
-   **제어**: 기본적으로는 비정기적인 IP를 통해 외부와 통신하지만, 보안 강화나 IP 기반 접근 제어가 필요한 외부 서비스와 연동해야 할 경우 **Cloud NAT**를 구성하여 아웃바운드 IP를 고정하고 트래픽을 제어할 수 있습니다.

---

## 3. 핵심 보안 규칙 요약

-   **Cloud Run 인그레스(Ingress)**: `내부 및 Cloud Load Balancing`으로 설정하여, 허가된 내부 트래픽과 Cloudflare가 연결된 로드 밸런서를 통해서만 요청을 수신합니다.
-   **Vertex AI 접근 제어**: `프라이빗 엔드포인트`로 배포하고, IAM 정책을 통해 특정 서비스 계정의 호출만 허용하도록 제한합니다.
-   **VPC 방화벽 규칙**: 위 원칙들이 네트워크 레벨에서 강제되도록, 불필요한 인바운드 포트를 모두 차단하고 내부 서비스 간의 통신만 허용하는 규칙을 설정합니다.
