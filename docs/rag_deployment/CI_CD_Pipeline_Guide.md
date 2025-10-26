# v2 아키텍처: Terraform 기반 CI/CD 파이프라인 가이드

이 문서는 Meta-RAG v2 아키텍처의 CI/CD(Continuous Integration & Continuous Deployment) 파이프라인 구축 방법을 안내합니다. v2 파이프라인의 핵심은 **Terraform**을 사용하여 애플리케이션 배포와 인프라 변경을 통합하고 자동화하는 것입니다.

## 1. v2 CI/CD 파이프라인 개요

v2 파이프라인은 다음과 같이 동작합니다.

1.  개발자가 `main` 브랜치에 코드를 `push`합니다.
2.  GitHub Actions가 파이프라인을 자동으로 실행합니다.
3.  **CI**: `pytest`로 애플리케이션 코드를 테스트합니다.
4.  **Build**: 테스트가 성공하면, 경량화된 FastAPI 오케스트레이터 앱을 Docker 이미지로 빌드하여 Artifact Registry에 푸시합니다. 이미지 태그는 Git Commit SHA로 지정하여 추적이 가능하게 합니다.
5.  **Deploy (CD)**: 파이프라인이 `terraform apply` 명령을 실행합니다. 이때, 방금 빌드한 새 이미지 태그를 변수로 전달합니다. Terraform은 이 정보를 바탕으로 Cloud Run 서비스를 새 이미지로 업데이트하는 등 필요한 모든 인프라 변경을 자동으로 적용합니다.

## 2. 사전 준비

-   **Terraform 코드**: `IaC_with_Terraform_Guide.md` 문서에 따라 Terraform 코드가 프로젝트에 작성되어 있어야 합니다.
-   **GCP-GitHub 연동**: v1 가이드와 동일하게, Workload Identity Federation을 사용하여 GitHub Actions가 GCP 권한을 얻을 수 있도록 설정되어 있어야 합니다. Terraform을 실행해야 하므로, 서비스 계정에 `roles/editor` 또는 더 세분화된 리소스 관리자 역할을 부여해야 할 수 있습니다.

---

## 3. v2 GitHub Actions 워크플로우 (`ci.yml`)

프로젝트의 `.github/workflows/ci.yml` 파일을 아래 내용으로 수정합니다. v1의 `gcloud run deploy` 액션 대신 Terraform을 설정하고 실행하는 단계로 변경된 점이 핵심입니다.

```yaml
name: v2 CI/CD for Meta-RAG Backend (Terraform)

on:
  push:
    branches:
      - main

env:
  GCP_REGION: asia-northeast3
  GAR_REPOSITORY: meta-rag-repo
  SERVICE_NAME: meta-rag-backend-v2
  TERRAFORM_DIR: ./terraform

jobs:
  test:
    name: Run Unit Tests
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run pytest
        run: pytest

  deploy:
    name: Build and Deploy to Cloud Run via Terraform
    needs: test
    runs-on: ubuntu-latest

    permissions:
      contents: 'read'
      id-token: 'write'

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Authenticate to Google Cloud
        uses: google-github-actions/auth@v1
        with:
          workload_identity_provider: ${{ secrets.GCP_WORKLOAD_IDENTITY_PROVIDER }}
          service_account: ${{ secrets.GCP_SERVICE_ACCOUNT }}

      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v1

      - name: Configure Docker
        run: gcloud auth configure-docker ${{ env.GCP_REGION }}-docker.pkg.dev

      - name: Build and Push Docker Image
        id: build-image
        run: |
          IMAGE_TAG=${{ env.GCP_REGION }}-docker.pkg.dev/${{ secrets.GCP_PROJECT_ID }}/${{ env.GAR_REPOSITORY }}/${{ env.SERVICE_NAME }}:${{ github.sha }}
          docker build -t $IMAGE_TAG .
          docker push $IMAGE_TAG
          echo "image_name=$IMAGE_TAG" >> $GITHUB_OUTPUT

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v2
        with:
          terraform_wrapper: false

      - name: Terraform Init
        run: terraform -chdir=${{ env.TERRAFORM_DIR }} init

      - name: Terraform Plan
        run: terraform -chdir=${{ env.TERRAFORM_DIR }} plan -var="image_name=${{ steps.build-image.outputs.image_name }}"

      - name: Terraform Apply
        run: terraform -chdir=${{ env.TERRAFORM_DIR }} apply -auto-approve -var="image_name=${{ steps.build-image.outputs.image_name }}"
```

### v1 워크플로우와의 주요 차이점

-   **Terraform 단계 추가**: `setup-terraform`, `terraform init`, `terraform plan`, `terraform apply` 단계가 추가되었습니다.
-   **`deploy-cloudrun` 액션 제거**: `gcloud run deploy`를 직접 호출하던 액션이 `terraform apply`로 대체되었습니다.
-   **이미지 태그 전달**: `build-image` 단계에서 생성된 이미지 태그(`image_name`)를 `GITHUB_OUTPUT`을 통해 이후의 `terraform` 단계로 전달합니다. Terraform은 이 변수를 받아 Cloud Run 리소스의 이미지 속성을 업데이트합니다.
-   **`permissions` 설정**: Workload Identity Federation을 사용하기 위해 `id-token: 'write'` 권한이 명시적으로 필요합니다.