# Meta-RAG 테스트 리포트 배포 프로세스

**문서 버전: 1.0**
**작성일: 2025-10-26**

---

## 개요

이 문서는 `pytest` 테스트 결과를 GitHub Pages에 웹페이지 형태로 배포하는 새로운 프로세스를 설명합니다.

기존에는 CI/CD 파이프라인 내에서 테스트를 실행하고 리포트를 생성했지만, 이제는 로컬 환경에서 생성된 리포트를 직접 커밋하고 푸시하여 배포하는 방식으로 변경되었습니다.

## 배포 절차

다음 단계를 순서대로 따라주세요.

### 1. 로컬에서 테스트 실행 및 리포트 생성

프로젝트의 루트 디렉토리에서 다음 명령어를 실행하여 `pytest`를 실행하고 `report.html` 파일을 생성합니다.

```bash
pytest --html=report.html --self-contained-html
```

`--self-contained-html` 옵션은 모든 스타일(CSS) 정보가 포함된 단일 HTML 파일을 생성하여 깨짐 없이 표시되도록 합니다.

### 2. 생성된 리포트 커밋

테스트 실행 후 생성된 `report.html` 파일을 Git 스테이징 영역에 추가하고 커밋합니다.

```bash
# 1. 변경된 모든 파일을 스테이징
git add .

# 2. 또는 report.html 파일만 특정하여 스테이징
# git add report.html

# 3. 커밋
git commit -m "docs: Update test report"
```

### 3. 원격 저장소에 푸시

커밋을 원격 저장소(`origin`)의 `master` 또는 `main` 브랜치로 푸시합니다.

```bash
git push origin master
```

### 4. 배포 확인

푸시가 완료되면, GitHub Actions가 자동으로 실행되어 `report.html` 파일을 GitHub Pages에 배포합니다.

배포가 완료된 후에는 저장소의 **Settings -> Pages** 탭에 있는 주소 또는 **Actions** 탭의 배포 로그에서 결과 페이지를 확인할 수 있습니다.
