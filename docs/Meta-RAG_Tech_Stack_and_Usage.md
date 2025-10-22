# Meta-RAG 시스템 기술 스택 및 사용법 가이드

**문서 버전: 1.0**
**작성일: 2025-10-22**

---

## 1. 문서 개요

본 문서는 Meta-RAG 시스템의 각 컴포넌트 구현에 사용될 주요 라이브러리 및 프레임워크를 선정하고, 각 기술 스택의 버전, 호환성 고려사항, 공식 문서 참조 링크 및 핵심 사용법 예시를 제공합니다. 이는 실제 개발 착수를 위한 구체적인 기술 가이드라인 역할을 합니다.

## 2. 기술 스택 선정 원칙 및 호환성 고려사항

-   **최신 안정 버전:** 특별한 이유가 없는 한, 각 라이브러리의 최신 안정 버전을 사용합니다.
-   **활발한 커뮤니티 지원:** 문제 발생 시 해결책을 찾기 용이하도록 커뮤니티 지원이 활발한 라이브러리를 우선합니다.
-   **성능 및 확장성:** Meta-RAG 시스템의 요구사항(대규모 데이터 처리, 실시간 추론)을 충족할 수 있는 성능과 확장성을 고려합니다.
-   **Python 버전:** 모든 라이브러리는 Python 3.9+ 버전과 호환되어야 합니다.
-   **의존성 관리:** `pip-tools` 또는 `Poetry`와 같은 도구를 사용하여 의존성 충돌을 방지하고 버전을 명확히 관리합니다.
-   **호환성 확인:** 새로운 라이브러리 추가 시, `requirements.txt` 또는 `pyproject.toml`에 명시된 다른 라이브러리들과의 호환성을 `pip check` 또는 `poetry check` 명령어로 항상 확인합니다.

## 3. 핵심 컴포넌트별 기술 스택 상세

### 3.1. 백엔드 API 프레임워크
-   **선정:** `FastAPI`
-   **버전:** `^0.104.1` (최신 안정 버전)
-   **선정 이유:** 높은 성능(ASGI 기반), 자동 문서화(Swagger UI/ReDoc), 간결한 코드, 비동기 처리 지원.
-   **호환성:** Python 3.8+ 및 `Pydantic`, `Starlette` 등 주요 의존성과의 호환성이 높습니다.
-   **공식 문서:** [https://fastapi.tiangolo.com/](https://fastapi.tiangolo.com/)
-   **핵심 사용법 예시:**
    ```python
    # main.py
    from fastapi import FastAPI
    from pydantic import BaseModel

    app = FastAPI()

    class ProblemInput(BaseModel):
        problem_text: str
        formula_str: str = None

    @app.post("/solve")
    async def solve_problem(input: ProblemInput):
        # 여기에 ReasoningOrchestrator 호출 로직 구현
        return {"message": "Problem received", "input": input.dict()}

    # 실행: uvicorn main:app --reload
    ```

### 3.2. 비동기 웹 서버
-   **선정:** `Uvicorn`
-   **버전:** `^0.23.2` (FastAPI의 권장 ASGI 서버)
-   **선정 이유:** FastAPI와 함께 사용되는 고성능 ASGI 서버.
-   **공식 문서:** [https://www.uvicorn.org/](https://www.uvicorn.org/)

### 3.3. LLM 통합 및 오케스트레이션
-   **선정:** `LangChain`
-   **버전:** `^0.0.330` (최신 안정 버전)
-   **선정 이유:** 다양한 LLM 모델 및 도구(Tools)와의 통합 용이성, 체인(Chains) 및 에이전트(Agents)를 통한 복잡한 추론 흐름 구축 지원.
-   **호환성:** `OpenAI`, `Google Generative AI` 등 주요 LLM 클라이언트 라이브러리와 높은 호환성을 가집니다.
-   **공식 문서:** [https://python.langchain.com/docs/get_started/introduction](https://python.langchain.com/docs/get_started/introduction)
-   **핵심 사용법 예시 (LLMReasoner):**
    ```python
    from langchain.chat_models import ChatOpenAI
    from langchain.prompts import ChatPromptTemplate
    from langchain.schema import HumanMessage, SystemMessage

    # LLM 클라이언트 초기화
    chat = ChatOpenAI(temperature=0.7, model_name="gpt-4")

    # 프롬프트 템플릿 정의
    prompt_template = ChatPromptTemplate.from_messages([
        SystemMessage(content="당신은 문제 해결을 돕는 AI 튜터입니다. 단계별로 명확하게 사고 과정을 제시하세요."),
        HumanMessage(content="문제: {problem_description}\n\n참고할 유사 사고 패턴:\n{retrieved_patterns}\n\n이 문제를 해결하기 위한 단계별 사고 과정을 생성해주세요.")
    ])

    # 체인 구성 및 실행
    chain = prompt_template | chat
    response = chain.invoke({
        "problem_description": "2차 방정식 x^2 - 4x + 4 = 0의 해를 구하시오.",
        "retrieved_patterns": "- 과거에 유사한 완전제곱식 문제를 풀었던 과정"
    })
    print(response.content)
    ```

### 3.4. LLM 클라이언트 (OpenAI / Gemini)
-   **선정:** `openai`, `google-generativeai`
-   **버전:** `^1.3.0` (openai), `^0.3.0` (google-generativeai) (각각 최신 안정 버전)
-   **선정 이유:** 각 LLM 서비스의 공식 Python 클라이언트 라이브러리.
-   **호환성:** LangChain과 높은 호환성을 가집니다.
-   **공식 문서:**
    -   OpenAI: [https://platform.openai.com/docs/api-reference/introduction](https://platform.openai.com/docs/api-reference/introduction)
    -   Google Generative AI: [https://ai.google.dev/tutorials/python_quickstart](https://ai.google.dev/tutorials/python_quickstart)

### 3.5. 벡터 데이터베이스 (PoC용 로컬)
-   **선정:** `FAISS` (CPU 버전)
-   **버전:** `^1.7.4` (최신 안정 버전)
-   **선정 이유:** 로컬 환경에서 고성능 벡터 검색을 위한 효율적인 라이브러리. PoC 및 소규모 데이터셋에 적합.
-   **호환성:** `numpy`와 잘 통합되며, `sentence-transformers` 등 임베딩 라이브러리와 함께 사용됩니다.
-   **공식 문서:** [https://github.com/facebookresearch/faiss](https://github.com/facebookresearch/faiss)
-   **핵심 사용법 예시 (FAISSVectorDBManager):**
    ```python
    import faiss
    import numpy as np

    dimension = 768 # 임베딩 벡터 차원
    index = faiss.IndexFlatL2(dimension) # L2 거리 기반 인덱스

    # 벡터 추가
    vectors = np.array([[0.1, 0.2, ...], [0.3, 0.4, ...]], dtype=np.float32)
    index.add(vectors)

    # 벡터 검색
    query_vector = np.array([[0.15, 0.25, ...]], dtype=np.float32)
    D, I = index.search(query_vector, k=5) # k=5: 상위 5개 검색
    print("Distances:", D)
    print("Indices:", I)
    ```

### 3.6. 그래프 데이터베이스 클라이언트
-   **선정:** `neo4j`
-   **버전:** `^5.15.0` (최신 안정 버전)
-   **선정 이유:** 관계형 데이터 모델링에 최적화된 그래프 DB. 복잡한 사고 패턴 및 개념 관계 저장에 적합.
-   **호환성:** Python 3.8+와 호환되며, `py2neo` 등 다른 클라이언트 라이브러리도 존재합니다.
-   **공식 문서:** [https://neo4j.com/docs/api/python-driver/current/](https://neo4j.com/docs/api/python-driver/current/)
-   **핵심 사용법 예시 (Neo4jGraphDBManager):**
    ```python
    from neo4j import GraphDatabase

    uri = "bolt://localhost:7687"
    username = "neo4j"
    password = "password"

    driver = GraphDatabase.driver(uri, auth=(username, password))

    def add_problem_node(tx, problem_id, description):
        tx.run("CREATE (p:Problem {id: $id, description: $desc})", id=problem_id, desc=description)

    def relate_problem_to_concept(tx, problem_id, concept_id):
        tx.run("MATCH (p:Problem {id: $pid}), (c:Concept {id: $cid}) "
               "CREATE (p)-[:RELATED_TO]->(c)", pid=problem_id, cid=concept_id)

    with driver.session() as session:
        session.write_transaction(add_problem_node, "P001", "2차 방정식 해법")
        session.write_transaction(relate_problem_to_concept, "P001", "C001")

    driver.close()
    ```

### 3.7. 임베딩 모델 라이브러리
-   **선정:** `sentence-transformers`
-   **버전:** `^2.2.2` (최신 안정 버전)
-   **선정 이유:** 다양한 사전 학습된 텍스트 임베딩 모델을 쉽게 로드하고 사용할 수 있습니다. `ContextEncoder`에 활용.
-   **호환성:** `PyTorch`, `transformers` 라이브러리와 함께 작동합니다.
-   **공식 문서:** [https://www.sbert.net/](https://www.sbert.net/)
-   **핵심 사용법 예시 (ContextEncoder):**
    ```python
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer('all-MiniLM-L6-v2')

    sentences = ["This is an example sentence", "Each sentence is converted."]
    embeddings = model.encode(sentences)

    print(embeddings.shape) # (2, 384)
    ```

### 3.8. 데이터 모델링 및 유효성 검사
-   **선정:** `Pydantic`
-   **버전:** `^2.4.2` (FastAPI의 핵심 의존성)
-   **선정 이유:** 데이터 모델 정의 및 런타임 유효성 검사를 위한 강력한 도구. FastAPI와 완벽하게 통합됩니다.
-   **공식 문서:** [https://docs.pydantic.dev/](https://docs.pydantic.dev/)

### 3.9. 프론트엔드 프레임워크 (참고용)
-   **선정:** `Next.js` (React 기반)
-   **버전:** `^14.0.0` (최신 안정 버전)
-   **선정 이유:** 서버 사이드 렌더링(SSR), 정적 사이트 생성(SSG) 지원, 개발자 경험 우수, React 생태계 활용.
-   **공식 문서:** [https://nextjs.org/docs](https://nextjs.org/docs)

### 3.10. 프론트엔드 그래프 시각화 (참고용)
-   **선정:** `D3.js`, `React Flow`
-   **버전:** `^7.8.5` (D3.js), `^11.10.1` (React Flow) (각각 최신 안정 버전)
-   **선정 이유:** 복잡한 데이터 시각화 및 인터랙티브 그래프 구현에 강력한 기능 제공.
-   **공식 문서:**
    -   D3.js: [https://d3js.org/](https://d3js.org/)
    -   React Flow: [https://reactflow.dev/](https://reactflow.dev/)

## 4. 호환성 검증 및 의존성 관리

프로젝트 초기 설정 시 `pyproject.toml` (Poetry 사용 시) 또는 `requirements.txt` (pip 사용 시)에 모든 의존성을 명시하고, 다음 명령어를 통해 호환성을 주기적으로 검증합니다.

-   **Poetry:** `poetry install` 후 `poetry check`
-   **pip-tools:** `pip-compile`로 `requirements.txt` 생성 후 `pip install -r requirements.txt` 및 `pip check`

각 라이브러리의 마이너/패치 버전 업데이트는 일반적으로 호환성 문제가 적지만, 메이저 버전 업데이트 시에는 반드시 변경 로그(Changelog)를 확인하고 테스트를 통해 호환성을 검증해야 합니다.
