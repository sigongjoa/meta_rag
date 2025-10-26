# v2 아키텍처: Terraform을 사용한 인프라 배포 가이드 (IaC)

이 문서는 Meta-RAG v2 아키텍처의 모든 GCP 인프라를 **Terraform**을 사용하여 코드로 관리(IaC, Infrastructure as Code)하고 배포하는 방법을 안내합니다. 이 방식을 통해 인프라 구성을 버전 관리하고, 반복 가능하며, 안전한 배포 파이프라인을 구축할 수 있습니다.

## 1. 왜 Terraform(IaC)을 사용하는가?

-   **선언적 구문**: '무엇을 만들지'만 코드로 정의하면, Terraform이 '어떻게 만들지'는 알아서 처리합니다.
-   **버전 관리**: 모든 인프라 구성이 Git을 통해 버전 관리되므로, 변경 이력을 추적하고 필요시 이전 상태로 롤백하기 용이합니다.
-   **재사용성 및 일관성**: 동일한 코드를 사용하여 개발, 스테이징, 프로덕션 환경을 일관되게 구성할 수 있습니다.
-   **자동화**: CI/CD 파이프라인에 통합하여 인프라 변경을 포함한 전체 배포 과정을 자동화할 수 있습니다.

## 2. 프로젝트 구조 예시

Terraform 코드를 관리하기 위해 프로젝트 루트에 `terraform` 디렉터리를 생성하는 것을 권장합니다.

```
/meta_rag
|-- /docs
|-- /src (FastAPI 소스코드)
|-- /terraform
|   |-- main.tf       # 주요 리소스 정의
|   |-- variables.tf  # 변수 선언
|   |-- outputs.tf    # 결과물 출력 정의
|   |-- terraform.tfvars # 변수 값 할당 (이 파일은 .gitignore에 추가)
|-- Dockerfile
|-- ...
```

## 3. Terraform 코드 작성 예시 (`main.tf`)

다음은 Cloud Run 서비스를 Terraform으로 정의하는 코드의 간략한 예시입니다. 실제로는 Vertex AI, API Gateway 등 모든 리소스가 이 파일에 코드로 정의됩니다.

```terraform
# main.tf

# 1. Terraform 및 GCP Provider 설정
terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

# 2. Cloud Run 서비스 리소스 정의
resource "google_cloud_run_v2_service" "default" {
  name     = var.service_name
  location = var.gcp_region

  template {
    containers {
      image = var.image_name # CI/CD를 통해 동적으로 전달받을 이미지
      ports {
        container_port = 8000
      }
      resources {
        limits = {
          cpu    = var.cpu_limit
          memory = var.memory_limit
        }
      }
    }
    scaling {
      min_instance_count = 1 # 경량화되었지만, 최소 인스턴스 1개 유지는 여전히 유효
    }
  }
}

# 3. 변수 정의 (variables.tf)
variable "gcp_project_id" { type = string }
variable "gcp_region" { type = string, default = "asia-northeast3" }
variable "service_name" { type = string, default = "meta-rag-backend-v2" }
variable "image_name" { type = string }
variable "cpu_limit" { type = string, default = "1000m" } # 1 CPU
variable "memory_limit" { type = string, default = "1Gi" } # v1보다 훨씬 가벼워짐
```

## 4. 로컬 환경에서 수동 배포 절차

CI/CD를 구성하기 전, 로컬에서 Terraform을 사용하여 수동으로 인프라를 배포하는 과정입니다.

```bash
# 1. Terraform 디렉터리로 이동
cd terraform

# 2. Terraform 초기화
# 필요한 프로바이더 플러그인을 다운로드합니다. (프로젝트 당 최초 1회)
terraform init

# 3. 실행 계획 검토 (Dry-run)
# 어떤 리소스가 생성/변경/삭제될지 미리 확인합니다. 매우 중요한 단계입니다.
# -var 옵션으로 CI/CD에서 전달할 이미지 이름을 지정해줍니다.
terraform plan -var="image_name=[Artifact_Registry에_있는_이미지_경로]"

# 4. 인프라 배포 (Apply)
# 검토한 계획을 바탕으로 실제 인프라를 GCP에 생성/변경합니다.
terraform apply -var="image_name=[Artifact_Registry에_있는_이미지_경로]" -auto-approve
```

## 5. 다음 단계: CI/CD 파이프라인과의 통합

이 Terraform 워크플로우는 `CI_CD_Pipeline_Guide.md`에 설명된 대로 GitHub Actions 파이프라인에 통합됩니다. 파이프라인은 애플리케이션 이미지를 빌드하고, 그 이미지 태그를 `image_name` 변수로 하여 `terraform apply`를 실행함으로써 전체 배포를 자동화합니다.