# 가이드: Vertex AI Vector Search 인덱스 업데이트 방법

이 문서는 소스 데이터가 변경되었을 때, Vertex AI Vector Search 인덱스를 새로운 데이터로 업데이트하는 절차를 안내합니다.

## 프로세스 개요

Vector Search 인덱스를 업데이트하는 과정은 일반적으로 다음 두 단계로 이루어집니다.

1.  **데이터 준비:** 소스 데이터를 기반으로 새로운 임베딩 파일(`embeddings.json`)을 생성하고 GCS에 업로드합니다.
2.  **인덱스 업데이트:** GCS에 올라간 새로운 데이터셋을 사용하여 기존 Vertex AI 인덱스를 업데이트(리빌드)합니다.

---

## 1단계: 새로운 임베딩 생성 및 업로드

이 과정은 초기 설정 시 사용했던 `create_embeddings.py` 스크립트를 재사용합니다.

### 1.1. 소스 데이터 수정

먼저 `create_embeddings.py` 스크립트 안의 `sample_problems` 딕셔너리나, 스크립트가 읽어들이는 원본 데이터 소스를 원하는 내용으로 수정합니다.

### 1.2. 임베딩 재생성

프로젝트 루트에서 아래 명령어를 실행하여 `embeddings.json` 파일을 새로 생성합니다.

```bash
# 가상환경 활성화
source venv/bin/activate

# 스크립트 실행
python create_embeddings.py
```

### 1.3. GCS에 덮어쓰기

새로 생성된 `embeddings.json` 파일을 기존 GCS 경로에 그대로 덮어쓰기하여 업로드합니다. `gcloud storage cp` 명령어는 기본적으로 덮어쓰기를 수행합니다.

```bash
# 버킷 이름 변수 설정 (실제 사용하는 버킷 이름으로 변경)
export BUCKET_NAME="meta_rag_bucket"

# GCS에 파일 업로드 (덮어쓰기)
gcloud storage cp ./embeddings.json gs://${BUCKET_NAME}/embeddings/
```

---

## 2단계: Vertex AI 인덱스 업데이트

GCS에 새로운 데이터가 준비되면, Terraform을 통해 배포된 Vertex AI Index 리소스가 이 데이터를 사용하도록 업데이트(리빌드)해야 합니다.

**중요:** 현재 Terraform 구성은 인덱스를 **새로 생성**하는 데에만 초점이 맞춰져 있습니다. `contents_delta_uri`의 내용이 바뀌면 Terraform이 인덱스를 교체하려고 시도할 수 있지만, 가장 안정적인 방법은 GCP 콘솔이나 `gcloud` CLI를 통해 직접 업데이트 명령을 내리는 것입니다.

### gcloud를 이용한 업데이트 (권장)

아래 명령어를 사용하여 기존 인덱스를 GCS에 올라간 새 데이터로 업데이트할 수 있습니다.

```bash
# 변수 설정
export GCP_PROJECT_ID="$(gcloud config get-value project)"
export GCP_REGION="asia-northeast3"

# Terraform으로 생성된 인덱스의 ID를 확인해야 합니다.
# (GCP 콘솔 -> Vertex AI -> Vector Search -> INDEXES 에서 확인)
export INDEX_ID="여기에_인덱스_ID_입력"

# GCS에 업로드된 새 데이터 경로
export NEW_DATA_URI="gs://meta_rag_bucket/embeddings/"

# 인덱스 업데이트 명령
gcloud ai indexes update ${INDEX_ID} \
  --project=${GCP_PROJECT_ID} \
  --region=${GCP_REGION} \
  --metadata-file='{"contentsDeltaUri":"'${NEW_DATA_URI}'"}'
```

이 명령은 인덱스 리빌드를 트리거하며, 데이터 크기에 따라 시간이 다소 소요될 수 있습니다. 업데이트가 완료되면, 별도의 애플리케이션 재배포 없이도 Vertex AI 엔드포인트는 자동으로 새로운 데이터를 사용하여 검색 결과를 반환합니다.

