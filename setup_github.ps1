# GitHub 저장소 자동 설정 스크립트

Write-Host "=== openNAMU GitHub 저장소 설정 ===" -ForegroundColor Green
Write-Host ""

# 사용자명 입력
$username = Read-Host "GitHub 사용자명을 입력하세요"

if ([string]::IsNullOrWhiteSpace($username)) {
    Write-Host "사용자명이 입력되지 않았습니다." -ForegroundColor Red
    exit 1
}

# 저장소명 설정
$repoName = "openNAMU-postgresql"
$repoUrl = "https://github.com/$username/$repoName.git"

Write-Host ""
Write-Host "설정 정보:" -ForegroundColor Yellow
Write-Host "- GitHub 사용자명: $username"
Write-Host "- 저장소명: $repoName"
Write-Host "- 저장소 URL: $repoUrl"
Write-Host ""

# 확인
$confirm = Read-Host "위 정보로 진행하시겠습니까? (y/N)"
if ($confirm -ne "y" -and $confirm -ne "Y") {
    Write-Host "취소되었습니다." -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "GitHub 저장소 설정 중..." -ForegroundColor Green

try {
    # 원격 저장소 추가
    Write-Host "1. 원격 저장소 추가 중..."
    git remote add origin $repoUrl
    
    # 브랜치 이름 변경
    Write-Host "2. 브랜치를 main으로 변경 중..."
    git branch -M main
    
    # 코드 업로드
    Write-Host "3. 코드 업로드 중..."
    git push -u origin main
    
    Write-Host ""
    Write-Host "✅ GitHub 저장소 설정 완료!" -ForegroundColor Green
    Write-Host ""
    Write-Host "저장소 URL: https://github.com/$username/$repoName" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "다음 단계:" -ForegroundColor Yellow
    Write-Host "1. 위 URL로 이동하여 저장소 확인"
    Write-Host "2. Render.com에서 이 저장소로 배포"
    Write-Host "3. RENDER_DEPLOYMENT.md 가이드 참조"
    
} catch {
    Write-Host ""
    Write-Host "❌ 오류가 발생했습니다:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "해결 방법:" -ForegroundColor Yellow
    Write-Host "1. GitHub에서 '$repoName' 저장소가 생성되었는지 확인"
    Write-Host "2. GitHub 로그인 상태 확인"
    Write-Host "3. 저장소 권한 확인"
    exit 1
}

Write-Host ""
Write-Host "Press any key to continue..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")