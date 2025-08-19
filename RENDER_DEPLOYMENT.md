# Render 배포 가이드

이 가이드는 openNAMU 위키를 Render에 PostgreSQL 데이터베이스와 함께 배포하는 방법을 설명합니다.

## 사전 준비

1. [Render](https://render.com) 계정 생성
2. GitHub 저장소에 코드 푸시
3. PostgreSQL 지원이 추가된 openNAMU 코드

## 배포 단계

### 1. GitHub 저장소 연결

1. Render 대시보드에서 "New +" 클릭
2. "Web Service" 선택
3. GitHub 저장소 연결
4. openNAMU 저장소 선택

### 2. 서비스 설정

- **Name**: `openNAMU` (또는 원하는 이름)
- **Environment**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `chmod +x start.sh && ./start.sh`
- **Plan**: `Free` (또는 원하는 플랜)

### 3. PostgreSQL 데이터베이스 생성

1. Render 대시보드에서 "New +" 클릭
2. "PostgreSQL" 선택
3. 다음 설정 사용:
   - **Name**: `openNAMU-db`
   - **Database Name**: `wiki_db`
   - **User**: `wiki_user`
   - **Plan**: `Free`

### 4. 환경 변수 설정

웹 서비스 설정에서 다음 환경 변수를 추가:

#### 기본 설정
- `NAMU_DB_TYPE`: `postgresql`
- `NAMU_HOST`: `0.0.0.0`
- `NAMU_PORT`: `10000`
- `NAMU_LANG`: `ko-KR`
- `NAMU_MARKUP`: `namumark`
- `NAMU_ENCRYPT`: `sha3`
- `NAMU_DB`: `wiki_db`

#### PostgreSQL 연결 정보
데이터베이스 생성 후 자동으로 설정됩니다:
- `NAMU_POSTGRESQL_HOST`
- `NAMU_POSTGRESQL_PORT`
- `NAMU_POSTGRESQL_USER`
- `NAMU_POSTGRESQL_PASSWORD`
- `DATABASE_URL`

### 5. 배포 확인

1. 웹 서비스가 성공적으로 빌드되고 시작되는지 확인
2. 제공된 URL로 접속하여 위키가 정상 작동하는지 테스트
3. 로그에서 PostgreSQL 연결이 성공했는지 확인

## 주요 파일

- `render.yaml`: Render 배포 설정
- `start.sh`: 시작 스크립트 (데이터베이스 설정 자동 생성)
- `requirements.txt`: Python 의존성 (psycopg2-binary 포함)

## 문제 해결

### 데이터베이스 연결 오류
- PostgreSQL 서비스가 실행 중인지 확인
- 환경 변수가 올바르게 설정되었는지 확인
- 로그에서 연결 오류 메시지 확인

### 빌드 실패
- `requirements.txt`에 모든 필요한 패키지가 포함되어 있는지 확인
- Python 버전 호환성 확인

### 시작 실패
- `start.sh` 스크립트 권한 확인
- 환경 변수 설정 확인
- 포트 설정 확인 (Render는 자동으로 PORT 환경 변수 제공)

## 추가 설정

### 도메인 연결
- Render에서 커스텀 도메인 설정 가능
- SSL 인증서 자동 제공

### 백업
- PostgreSQL 데이터베이스 정기 백업 설정 권장
- 중요한 데이터는 별도 백업 솔루션 사용

### 모니터링
- Render 대시보드에서 서비스 상태 모니터링
- 로그 확인으로 문제 진단

## 비용

- Web Service (Free): 월 750시간 무료
- PostgreSQL (Free): 1GB 저장공간, 월 90일 보관
- 더 많은 리소스가 필요한 경우 유료 플랜 고려

배포 완료 후 위키 관리자 계정을 생성하고 초기 설정을 완료하세요.