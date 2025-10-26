# Meta-RAG: CI/CD 파이프라인 문제 해결 가이드

이 문서는 Meta-RAG 프로젝트의 CI/CD 파이프라인 설정 및 실행 과정에서 발생했던 주요 오류와 해결 방법을 정리합니다.

---

## 오류 1: `pytest` 실행 실패 - `ModuleNotFoundError`

CI/CD 파이프라인의 `test` 작업 중 `pytest`를 실행하는 단계에서 다음과 같은 오류가 발생했습니다.

**에러 로그:**
```
ImportError while importing test module '/home/runner/work/meta_rag/meta_rag/test_embedding.py'.
...
main.py:8: in <module>
    from langchain.prompts import ChatPromptTemplate
E   ModuleNotFoundError: No module named 'langchain.prompts'

main.py:9: in <module>
    from langchain.schema.output_parser import StrOutputParser
E   ModuleNotFoundError: No module named 'langchain.schema'
```

### 원인

이 오류는 `langchain` 라이브러리가 업데이트되면서 내부 모듈 구조가 변경되었기 때문에 발생합니다. `ChatPromptTemplate`와 `StrOutputParser` 같은 핵심 클래스들의 위치(import 경로)가 기존의 `langchain` 패키지에서 `langchain_core` 패키지로 이동했습니다.

로컬 환경에서는 이전 버전의 의존성이 캐시되어 있어 문제가 발생하지 않았을 수 있지만, CI/CD 환경에서는 `requirements.txt`에 따라 라이브러리를 새로 설치하므로 변경된 경로를 찾지 못해 `ModuleNotFoundError`가 발생합니다.

### 해결 방법

`main.py` 파일에서 문제가 된 import 구문을 다음과 같이 수정합니다.

**`ChatPromptTemplate` 경로 수정:**
```python
# 기존
from langchain.prompts import ChatPromptTemplate

# 변경
from langchain_core.prompts import ChatPromptTemplate
```

**`StrOutputParser` 경로 수정:**
```python
# 기존
from langchain.schema.output_parser import StrOutputParser

# 변경
from langchain_core.output_parsers import StrOutputParser
```

### 교훈

- 코드를 수정한 후에는 항상 로컬에서 `pytest`를 실행하여 기본적인 의존성 및 임포트 문제를 확인한 후 원격 저장소에 푸시해야 합니다.

---

## 오류 2: GCP 인증 실패 - `google-github-actions/auth` 오류

`pytest` 문제를 해결한 후, 파이프라인의 `deploy` 작업에서 GCP 인증을 시도하는 중 다음과 같은 오류가 발생했습니다.

**에러 로그:**
```
Error: google-github-actions/auth failed with: retry function failed after 4 attempts: the GitHub Action workflow must specify exactly one of "workload_identity_provider" or "credentials_json"!
```

### 원인

이 오류 메시지는 GCP 인증 액션(`google-github-actions/auth`)이 필요로 하는 `workload_identity_provider` 정보가 제대로 전달되지 않았음을 의미합니다. 

워크플로우 파일(`.github/workflows/ci.yml`)에는 `${{ secrets.GCP_WORKLOAD_IDENTITY_PROVIDER }}`와 같이 GitHub Secret을 사용하도록 명시되어 있습니다. 하지만 **GitHub 저장소에 해당 Secret이 등록되어 있지 않으면** 이 값은 빈 문자열로 처리되어, 인증 액션이 필요한 정보를 받지 못하고 실패하게 됩니다.

### 해결 방법

이 문제는 코드 수정이 아닌, GitHub 저장소의 설정 변경이 필요합니다.

1.  해당 GitHub 저장소의 **Settings** 탭으로 이동합니다.
2.  왼쪽 메뉴에서 **Secrets and variables > Actions**를 선택합니다.
3.  **Repository secrets** 섹션에서 `New repository secret` 버튼을 눌러 다음 3개의 Secret을 모두 등록합니다.

    -   **`GCP_WORKLOAD_IDENTITY_PROVIDER`**: GCP에서 생성한 Workload Identity Provider의 전체 경로.
        -   *예시: `projects/123456789/locations/global/workloadIdentityPools/my-pool/providers/my-provider`*

    -   **`GCP_SERVICE_ACCOUNT`**: GitHub Actions가 사용하도록 권한을 부여한 GCP 서비스 계정의 이메일 주소.
        -   *예시: `github-actions-runner@my-project.iam.gserviceaccount.com`*

    -   **`GCP_PROJECT_ID`**: 배포를 진행할 GCP 프로젝트의 ID.

### 교훈

- CI/CD 파이프라인에서 외부 서비스(GCP, AWS 등)와 연동할 때, 필요한 모든 인증 정보(API 키, Secret 등)가 CI/CD 환경에 올바르게 설정되었는지 반드시 확인해야 합니다.
