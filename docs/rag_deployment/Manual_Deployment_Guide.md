# 수동 배포 가이드 (GCP Cloud Run, Vertex AI, API Gateway)

이 문서는 Meta-RAG 애플리케이션을 Google Cloud Platform (GCP)에 수동으로 배포하는 과정을 안내합니다. 이 가이드는 CI/CD 파이프라인이 구축되기 전 개발 및 테스트 목적으로 사용될 수 있습니다.

## 1. 전제 조건

*   **GCP 프로젝트:** `meta-476400` (또는 사용 중인 프로젝트 ID)
*   **GCP CLI (`gcloud`)**: 설치 및 인증 완료
*   **Docker**: 설치 완료
*   **Terraform**: 설치 완료
*   **애플리케이션 코드:** `meta_rag` 프로젝트 폴더 내에 `Dockerfile`, `requirements.txt`, `main.py` 등 존재
*   **`.dockerignore` 파일:** Docker 이미지 최적화를 위해 프로젝트 루트에 `.dockerignore` 파일이 존재해야 합니다.

## 2. GCP API 활성화 (최초 1회)

Terraform 배포를 시작하기 전에 필요한 GCP API를 활성화해야 합니다.

```bash
gcloud services enable \
    aiplatform.googleapis.com \
    apigateway.googleapis.com \
    iam.googleapis.com \
    run.googleapis.com \
    artifactregistry.googleapis.com \
    --project=meta-476400
```

## 3. Docker 이미지 빌드 및 Artifact Registry 푸시

애플리케이션의 Docker 이미지를 빌드하고 GCP Artifact Registry에 업로드합니다.

### 3.1. Dockerfile 및 `.dockerignore` 최적화 확인

*   **`.dockerignore`**: 프로젝트 루트에 `.dockerignore` 파일이 존재하여 `venv/`, `.git/`, `__pycache__/`, `assets/` 등 불필요한 파일이 이미지에 포함되지 않도록 합니다.
*   **`Dockerfile`**: `torch`와 같은 대용량 라이브러리는 CPU 전용 버전으로 설치되도록 `Dockerfile`이 수정되어 있어야 합니다. (예: `RUN pip install torch --index-url https://download.pytorch.org/whl/cpu`)

### 3.2. Docker 인증

Artifact Registry에 이미지를 푸시하기 위해 Docker를 인증합니다.

```bash
gcloud auth configure-docker asia-northeast3-docker.pkg.dev
```

### 3.3. Docker 이미지 빌드

프로젝트 루트 디렉터리에서 Docker 이미지를 빌드합니다.

```bash
docker build -t meta-rag-backend:latest .
```

### 3.4. Docker 이미지 태그 지정

빌드된 로컬 이미지에 Artifact Registry 경로와 고유한 다이제스트(Digest)를 포함한 태그를 지정합니다.

```bash
docker tag meta-rag-backend:latest asia-northeast3-docker.pkg.dev/meta-476400/meta-rag-repo/meta-rag-backend-v2:9ce7d40ca564f825d96b69bce61ce416b47f3484
```
**참고:** `9ce7d40ca564f825d96b69bce61ce416b47f3484`는 이미지의 태그이며, 실제 배포 시에는 `docker push` 후 출력되는 `sha256:ef778c4ff527dfaec87ab382932d4e1a860f7f1497c31e8a55fae0dfc6e168e2`와 같은 **다이제스트**를 사용하는 것이 좋습니다.

### 3.5. Docker 이미지 푸시

태그가 지정된 이미지를 Artifact Registry로 푸시합니다.

```bash
docker push asia-northeast3-docker.pkg.dev/meta-476400/meta-rag-repo/meta-rag-backend-v2:9ce7d40ca564f825d96b69bce61ce416b47f3484
```
**참고:** 푸시 성공 시 출력되는 `digest: sha256:...` 값을 기록해 둡니다. 이 값이 `terraform apply` 시 `image_name` 변수에 사용됩니다.

## 4. Terraform을 이용한 인프라 배포

Terraform을 사용하여 GCP 인프라(Artifact Registry, Cloud Run, Vertex AI, API Gateway 등)를 배포합니다.

### 4.1. Terraform 초기화

`terraform/gcp` 디렉터리에서 Terraform을 초기화합니다.

```bash
terraform -chdir=terraform/gcp init
```

### 4.2. Terraform 배포 실행

기록해 둔 이미지 다이제스트를 `image_name` 변수에 사용하여 `terraform apply`를 실행합니다.

```bash
terraform -chdir=terraform/gcp apply -auto-approve \
    -var="gcp_project_id=meta-476400" \
    -var="image_name=asia-northeast3-docker.pkg.dev/meta-476400/meta-rag-repo/meta-rag-backend-v2@sha256:ef778c4ff527dfaec87ab382932d4e1a860f7f1497c31e8a55fae0dfc6e168e2"
```

**참고:**
*   `image_name` 변수에는 **반드시 푸시 성공 시 출력된 이미지 다이제스트(`@sha256:...`)**를 사용해야 합니다.
*   배포 과정 중 Vertex AI Index Endpoint 배포는 10분 이상 소요될 수 있습니다.
*   만약 `Resource 'meta-rag-backend-v2' already exists.`와 같은 오류가 발생하면, GCP 콘솔에서 해당 Cloud Run 서비스를 수동으로 삭제한 후 다시 `terraform apply`를 실행해야 합니다.

## 5. 배포 확인

`terraform apply`가 성공적으로 완료되면, GCP 콘솔의 Cloud Run 서비스 페이지에서 `meta-rag-backend-v2` 서비스가 정상적으로 실행 중인지 확인할 수 있습니다. 또한, API Gateway 페이지에서 `meta-rag-gateway`가 생성되었는지 확인합니다.

