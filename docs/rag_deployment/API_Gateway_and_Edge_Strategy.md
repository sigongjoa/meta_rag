# v2 아키텍처: API Gateway 및 Edge 전략

이 문서는 Meta-RAG v2 아키텍처의 진입점(Entrypoint)을 구성하는 **GCP API Gateway**와 **Cloudflare**의 역할과 책임을 명확히 정의합니다. v1의 '중앙 라우터'가 가졌던 복잡성을 해결하고, '관심사 분리(Separation of Concerns)' 원칙을 적용하여 각 계층이 자신의 역할에만 집중하도록 설계합니다.

## 1. 책임의 분리 (Separation of Concerns)

v2 아키텍처는 진입점의 역할을 두 개의 뚜렷한 계층으로 분리합니다.

-   **Edge 계층 (Cloudflare)**: 시스템의 최전방에 위치하며, **보안**과 **글로벌 성능 최적화**를 담당합니다. 똑똑한 비즈니스 로직을 가지지 않습니다.
-   **Gateway 계층 (GCP API Gateway)**: Edge와 백엔드 사이에 위치하며, **인증/인가(Authentication/Authorization)** 를 전담합니다.

![Gateway and Edge Diagram](https://gist.github.com/assets/3687397/52f15939-772a-481b-a12a-100771080843/raw/903010808779112b32a892818b05988935153e40/gateway-edge-v2.svg)

---

## 2. Edge 계층: Cloudflare

-   **핵심 역할**: 똑똑하지 않은, 그러나 매우 강력하고 빠른 글로벌 방패막.
-   **주요 책임**:
    -   **보안 (Security)**: WAF(웹 애플리케이션 방화벽)를 통해 SQL Injection, XSS 등 일반적인 웹 공격을 차단하고, 대규모 DDoS 공격을 방어합니다.
    -   **성능 (Performance)**: 사용자와 가장 가까운 데이터 센터에서 정적 콘텐츠(예: 클라이언트 앱의 JS/CSS 파일)를 캐싱하여 전송 속도를 높입니다. API 응답 자체는 동적이므로 캐싱하지 않습니다.
    -   **TLS 종료 (TLS Termination)**: 사용자와의 HTTPS 통신을 처리하고, GCP 내부망으로 트래픽을 전달하기 전에 암호화를 해독합니다.
    -   **단순 전달 (Request Forwarding)**: 위 처리가 끝난 트래픽을 GCP API Gateway의 엔드포인트로 그대로 전달하는 역할만 수행합니다.
-   **하지 않는 것 (Non-responsibilities)**:
    -   JWT 토큰 검증 또는 내용 분석
    -   사용자 등급에 따른 분기 등 비즈니스 로직 처리
    -   복잡한 경로 재작성(URL Rewriting)

---

## 3. Gateway 계층: GCP API Gateway

-   **핵심 역할**: 백엔드의 문지기. 오직 인가된 사용자만이 백엔드 서비스에 접근할 수 있도록 보장합니다.
-   **주요 책임**:
    -   **인증 (Authentication)**: 모든 수신 요청의 `Authorization: Bearer <TOKEN>` 헤더에서 **JWT를 추출하고, 공개 키를 사용해 서명을 검증**합니다. 위조되거나 만료된 토큰을 가진 요청은 여기서 차단됩니다 (`401 Unauthorized`).
    -   **경로 매핑 (Path Mapping)**: `/chat`과 같은 공개 API 경로를 내부 Cloud Run 서비스의 특정 엔드포인트로 매핑합니다.
    -   **API 키 관리 (Optional)**: 필요한 경우, 특정 클라이언트나 서드파티 개발자에게 발급된 API 키를 검증하는 역할을 추가할 수 있습니다.
-   **하지 않는 것 (Non-responsibilities)**:
    -   WAF, DDoS 방어 등 광범위한 보안 필터링
    -   JWT 토큰의 내용(payload)을 깊게 분석하여 비즈니스 로직을 처리하는 행위 (예: 사용자 등급 확인). 이는 백엔드의 책임입니다.

---

## 4. v1 대비 개선점

-   **단순성 및 유지보수성**: Cloudflare Worker에 있던 복잡한 JavaScript 코드가 사라지고, 각 서비스의 역할이 명확해져 관리가 용이해집니다.
-   **보안 강화**: 민감한 JWT 검증 로직이 외부 엣지가 아닌, GCP의 통제된 환경 내에 있는 API Gateway에서만 수행되어 보안성이 향상됩니다.
-   **표준 준수**: GCP API Gateway는 OpenAPI 명세서를 직접 임포트하여 구성을 자동화할 수 있어, 스펙 주도 개발(Spec-driven Development) 워크플로우와 완벽하게 통합됩니다.