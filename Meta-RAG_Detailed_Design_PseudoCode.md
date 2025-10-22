
## 8. 피드백 및 강화 학습 레이어 (Feedback & Reinforcement Layer)

**역할:** 추론 레이어에서 생성된 사고 과정의 결과와 사용자 피드백을 평가하고, 이를 통해 시스템의 성능을 지속적으로 개선합니다.

### 8.1. 인터페이스: `IRewardCalculator`
생성된 사고 과정에 대한 보상 점수를 계산하는 기능을 추상화합니다.

```python
interface IRewardCalculator:
    method calculate_reward(thought_process: List[Dict], actual_result: Any, expected_result: Any = None, user_feedback: Dict = None) -> float:
        """
        생성된 사고 과정에 대한 보상 점수를 계산합니다.
        Args:
            thought_process (List[Dict]): 생성된 사고 과정.
            actual_result (Any): 사고 과정을 통해 얻은 실제 결과.
            expected_result (Any): 기대하는 결과 (정답).
            user_feedback (Dict): 사용자로부터 받은 피드백.
        Returns:
            float: 계산된 보상 점수.
        """
        pass
```

### 8.2. 클래스: `RewardEvaluator`
다양한 기준(정확성, 효율성, 사용자 만족도)에 따라 보상 점수를 계산합니다. `IRewardCalculator` 인터페이스를 구현합니다.

```python
class RewardEvaluator implements IRewardCalculator:
    method calculate_reward(thought_process: List[Dict], actual_result: Any, expected_result: Any = None, user_feedback: Dict = None) -> float:
        """
        보상 점수를 계산합니다.
        - 정확성: actual_result와 expected_result 비교
        - 효율성: thought_process의 단계 수, LLM 토큰 사용량 등
        - 사용자 만족도: user_feedback (예: 별점, 좋아요/싫어요)
        """
        reward = 0.0
        if expected_result is not None and actual_result == expected_result:
            reward += 1.0 # 정답이면 높은 보상
        else:
            reward -= 0.5 # 오답이면 페널티

        # 사고 과정의 효율성에 따른 보상/페널티
        reward -= len(thought_process) * 0.01 # 단계가 많으면 페널티

        if user_feedback and user_feedback.get("satisfaction") == "high":
            reward += 0.2 # 사용자 만족도 보상

        return reward
```

### 8.3. 클래스: `FeedbackProcessor`
사용자 피드백을 수집, 분석하고, 이를 시스템 개선에 활용할 수 있는 형태로 가공합니다.

```python
class FeedbackProcessor:
    method process_user_feedback(feedback_data: Dict) -> Dict:
        """
        사용자 피드백 데이터를 처리하고 분석합니다.
        Args:
            feedback_data (Dict): 사용자 피드백 (예: {"problem_id": "...", "rating": 5, "comment": "..."}).
        Returns:
            Dict: 분석된 피드백 데이터.
        """
        # 피드백 데이터 저장, 감성 분석 등
        pass

    method get_feedback_for_problem(problem_id: str) -> List[Dict]:
        """
        특정 문제에 대한 모든 피드백을 조회합니다.
        """
        pass
```

### 8.4. 클래스: `ReinforcementLearner`
보상 신호를 바탕으로 추론 전략이나 모델을 업데이트하는 강화 학습 로직을 구현합니다.

```python
class ReinforcementLearner:
    attribute llm_reasoner: LLMReasoner
    attribute data_synchronizer: DataSynchronizer

    constructor(llm_reasoner: LLMReasoner, data_synchronizer: DataSynchronizer):
        self.llm_reasoner = llm_reasoner
        self.data_synchronizer = data_synchronizer

    method update_reasoning_strategy(problem_id: str, thought_process: List[Dict], reward: float) -> None:
        """
        주어진 보상에 따라 LLM의 추론 전략(프롬프트 템플릿, Few-shot 예시 등)을 업데이트합니다.
        Args:
            problem_id (str): 관련 문제 ID.
            thought_process (List[Dict]): 평가된 사고 과정.
            reward (float): 계산된 보상 점수.
        """
        if reward > 0.5: # 긍정적인 보상일 경우
            # 해당 사고 과정을 성공적인 패턴으로 Graph DB에 저장하거나, LLM의 Few-shot 예시로 추가
            self.data_synchronizer.sync_successful_pattern(problem_id, thought_process)
        elif reward < -0.5: # 부정적인 보상일 경우
            # 해당 사고 과정을 실패 패턴으로 기록하거나, LLM의 프롬프트에 개선 지시 추가
            self.data_synchronizer.sync_failed_pattern(problem_id, thought_process)
        pass

    method retrain_embedding_models(new_data: List[Dict]) -> None:
        """
        새로운 데이터로 임베딩 모델을 주기적으로 재학습합니다.
        """
        pass
```

## 9. API 게이트웨이 / 백엔드 서비스 레이어 (API Gateway / Backend Service Layer)

**역할:** 프론트엔드 및 외부 시스템과의 통신을 위한 인터페이스를 제공하고, 내부 컴포넌트들의 기능을 통합하여 노출합니다.

### 9.1. 클래스: `MetaRAG_API` (FastAPI 애플리케이션)
FastAPI를 사용하여 RESTful API 엔드포인트를 정의하고, 내부 서비스들을 호출합니다.

```python
class MetaRAG_API:
    attribute app: FastAPI
    attribute reasoning_orchestrator: ReasoningOrchestrator
    attribute feedback_processor: FeedbackProcessor
    attribute reward_evaluator: RewardEvaluator

    constructor(reasoning_orchestrator: ReasoningOrchestrator, feedback_processor: FeedbackProcessor, reward_evaluator: RewardEvaluator):
        self.app = FastAPI()
        self.reasoning_orchestrator = reasoning_orchestrator
        self.feedback_processor = feedback_processor
        self.reward_evaluator = reward_evaluator
        self._register_routes()

    method _register_routes() -> None:
        """
        API 엔드포인트를 등록합니다.
        """
        @self.app.post("/solve")
        async def solve_problem_endpoint(request: Dict) -> Dict:
            # 사용자 문제 입력 처리 및 사고 과정 생성
            result = self.reasoning_orchestrator.solve_problem(request)
            return {"status": "success", "data": result}

        @self.app.post("/feedback")
        async def submit_feedback_endpoint(request: Dict) -> Dict:
            # 사용자 피드백 수집 및 처리
            processed_feedback = self.feedback_processor.process_user_feedback(request)
            # 보상 계산 및 강화 학습 트리거 (비동기 처리 가능)
            # reward = self.reward_evaluator.calculate_reward(...)
            return {"status": "success", "message": "Feedback received", "processed_data": processed_feedback}

        @self.app.get("/problem/{problem_id}/history")
        async def get_problem_history_endpoint(problem_id: str) -> Dict:
            # 특정 문제에 대한 과거 사고 과정 및 피드백 조회
            # history = self.reasoning_orchestrator.get_problem_history(problem_id)
            return {"status": "success", "data": {"problem_id": problem_id, "history": []}}

        # ... 기타 API 엔드포인트 (예: /status, /metrics)

    method run() -> None:
        """
        FastAPI 애플리케이션을 실행합니다.
        """
        # uvicorn.run(self.app, host="0.0.0.0", port=8000)
        pass
```

### 9.2. 클래스: `RequestAuthenticator`
API 요청에 대한 인증 및 인가를 처리합니다.

```python
class RequestAuthenticator:
    method authenticate(token: str) -> bool:
        """
        사용자 토큰을 검증하여 인증합니다.
        """
        pass

    method authorize(user_id: str, resource: str, action: str) -> bool:
        """
        사용자가 특정 리소스에 대한 특정 액션을 수행할 권한이 있는지 확인합니다.
        """
        pass
```

### 9.3. 클래스: `ServiceOrchestrator`
API 요청에 따라 여러 내부 서비스 컴포넌트들을 조정하고 데이터 흐름을 관리합니다. (ReasoningOrchestrator와 유사하지만, 더 고수준의 API 요청 처리)

```python
class ServiceOrchestrator:
    attribute reasoning_orchestrator: ReasoningOrchestrator
    attribute feedback_processor: FeedbackProcessor
    # ... 기타 서비스 컴포넌트

    constructor(reasoning_orchestrator: ReasoningOrchestrator, feedback_processor: FeedbackProcessor):
        self.reasoning_orchestrator = reasoning_orchestrator
        self.feedback_processor = feedback_processor

    method handle_solve_request(request_data: Dict) -> Dict:
        """
        '/solve' API 요청을 처리하기 위해 추론 오케스트레이터를 호출하고 결과를 반환합니다.
        """
        return self.reasoning_orchestrator.solve_problem(request_data)

    method handle_feedback_request(request_data: Dict) -> Dict:
        """
        '/feedback' API 요청을 처리하기 위해 피드백 프로세서를 호출합니다.
        """
        return self.feedback_processor.process_user_feedback(request_data)
```

### 9.4. 클래스: `Logger`
시스템의 모든 활동 및 에러를 기록하고 관리합니다.

```python
class Logger:
    method info(message: str, context: Dict = None) -> None:
        """
        정보성 로그를 기록합니다.
        """
        pass

    method error(message: str, exception: Exception = None, context: Dict = None) -> None:
        """
        에러 로그를 기록합니다.
        """
        pass

    method debug(message: str, context: Dict = None) -> None:
        """
        디버그 로그를 기록합니다.
        """
        pass
```

---

## 10. 결론 및 다음 단계

이로써 Meta-RAG 시스템의 모든 핵심 컴포넌트에 대한 의사 코드 수준의 상세 설계 문서 작성을 완료했습니다. 이 문서는 실제 구현을 위한 청사진 역할을 할 것입니다.

다음 단계는 이 설계 문서를 바탕으로 실제 코드를 작성하거나, PoC 구현을 시작하는 것이 될 수 있습니다.
