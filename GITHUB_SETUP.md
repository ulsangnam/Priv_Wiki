# GitHub 저장소 생성 및 업로드 가이드

## 자동 설정 명령어

다음 명령어들을 순서대로 실행하세요:

### 1. GitHub에서 새 저장소 생성
1. https://github.com/new 방문
2. Repository name: `openNAMU-postgresql`
3. Description: `openNAMU wiki with PostgreSQL support and Render deployment`
4. Public 선택
5. "Create repository" 클릭

### 2. 로컬 저장소와 연결
저장소 생성 후 다음 명령어 실행:

```bash
# 새로운 원격 저장소 추가 (YOUR_USERNAME을 실제 GitHub 사용자명으로 변경)
git remote add origin https://github.com/YOUR_USERNAME/openNAMU-postgresql.git

# 브랜치 이름을 main으로 변경
git branch -M main

# 코드 업로드
git push -u origin main
```

### 3. 자동 설정 스크립트
아래 명령어로 자동 설정 가능:

```bash
# 사용자명 입력 후 실행
$username = Read-Host "GitHub 사용자명을 입력하세요"
git remote add origin "https://github.com/$username/openNAMU-postgresql.git"
git branch -M main
git push -u origin main
```

## 포함된 기능

✅ **PostgreSQL 데이터베이스 지원**
- psycopg2-binary 의존성
- 환경 변수 기반 설정
- 자동 연결 로직

✅ **Render 배포 설정**
- render.yaml 설정 파일
- 자동 시작 스크립트
- PostgreSQL 데이터베이스 연동

✅ **배포 가이드**
- 상세한 Render 배포 가이드
- 환경 변수 설정 방법
- 문제 해결 가이드

## 다음 단계

1. GitHub 저장소 생성
2. 코드 업로드
3. Render에서 배포
4. PostgreSQL 데이터베이스 연결
5. 위키 초기 설정

모든 준비가 완료되어 있습니다! 🎉