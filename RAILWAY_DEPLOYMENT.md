# Railway 배포 가이드 - GitHub 연동 및 CLI 배포

## ✅ GitHub 저장소 확인 완료

**저장소**: https://github.com/weegoodojb/SCHBC_BBMS.git  
**상태**: 비어있음 (초기 상태)  
**Git Remote**: 설정 완료

---

## 🚀 Railway 배포 방법 (2가지 옵션)

### 옵션 1: GitHub 연동 배포 (권장)

#### Step 1: GitHub에 코드 푸시

**방법 A: GitHub Desktop 사용** (가장 쉬움)
1. GitHub Desktop 실행
2. File → Add Local Repository
3. `c:\code\02_antigravity\PBM` 선택
4. "Publish repository" 클릭
5. Repository name: `SCHBC_BBMS` 확인
6. "Publish repository" 버튼 클릭

**방법 B: Git 명령어 사용**
```bash
cd c:\code\02_antigravity\PBM

# GitHub 인증 (Personal Access Token 필요)
git config --global user.name "your-github-username"
git config --global user.email "your-github-email"

# 푸시 (인증 창이 뜰 수 있음)
git push -u origin main
```

#### Step 2: Railway에서 GitHub 저장소 연결

1. **Railway 접속**: https://railway.app
2. **New Project** 클릭
3. **Deploy from GitHub repo** 선택
4. **SCHBC_BBMS** 저장소 선택
5. **Deploy Now** 클릭

---

### 옵션 2: Railway CLI 직접 배포 (GitHub 우회)

GitHub 푸시 없이 바로 배포 가능합니다.

#### Step 1: Railway CLI 설치

```powershell
# npm이 설치되어 있다면
npm install -g @railway/cli

# 또는 Scoop 사용
scoop install railway
```

#### Step 2: Railway 로그인

```powershell
cd c:\code\02_antigravity\PBM
railway login
```

브라우저가 열리면 Railway 계정으로 로그인하세요.

#### Step 3: 프로젝트 초기화

```powershell
# 새 프로젝트 생성
railway init

# 프로젝트 이름: SCHBC-BBMS
```

#### Step 4: 환경 변수 설정

```powershell
# Railway 대시보드에서 설정하거나 CLI로 설정
railway variables set DATABASE_URL="mysql+pymysql://4Hv47XPrF3C3oHV.root:qcu4ldWPyNVjiMxm@gateway01.ap-northeast-1.prod.aws.tidbcloud.com:4000/test?ssl_ca=&ssl_verify_cert=true&ssl_verify_identity=true"

railway variables set SECRET_KEY="your-secret-key-change-in-production-min-32-chars-long"

railway variables set DEBUG="False"
```

#### Step 5: 배포

```powershell
# 현재 디렉토리 배포
railway up

# 또는 자동 배포 연결
railway link
```

---

## 📋 배포 전 체크리스트

### 로컬 파일 확인
- [x] `Procfile` 존재
- [x] `railway.json` 존재
- [x] `runtime.txt` 존재
- [x] `requirements.txt` 존재
- [x] `app/core/config.py` - DEBUG=False
- [x] `app/gas/code.gs` - 터널 헤더 제거됨

### Railway 설정
- [ ] Railway 계정 생성/로그인
- [ ] 프로젝트 생성
- [ ] 환경 변수 설정
- [ ] 배포 시작

---

## 🎯 배포 후 확인 사항

### 1. Railway URL 확인

배포 완료 후 Railway 대시보드에서:
- **Settings** → **Domains**
- 생성된 URL 복사 (예: `https://schbc-bbms-production.up.railway.app`)

### 2. Health Check

```bash
curl https://your-app-name.up.railway.app/health
```

**예상 응답**:
```json
{
  "status": "healthy",
  "app": "SCHBC BBMS API",
  "version": "1.0.0"
}
```

### 3. API 문서 확인

브라우저에서 접속:
```
https://your-app-name.up.railway.app/docs
```

---

## 🔧 Git 인증 문제 해결

### Personal Access Token 생성

1. **GitHub 접속**: https://github.com/settings/tokens
2. **Generate new token (classic)** 클릭
3. **Note**: "Railway Deployment"
4. **Expiration**: 90 days
5. **Select scopes**: `repo` 체크
6. **Generate token** 클릭
7. **토큰 복사** (한 번만 표시됨!)

### Git 인증 설정

```powershell
# Windows Credential Manager 사용
git config --global credential.helper wincred

# 푸시 시 Username과 Password(Token) 입력
git push -u origin main
# Username: your-github-username
# Password: ghp_xxxxxxxxxxxxxxxxxxxx (복사한 토큰)
```

---

## 📊 권장 배포 방법

### 🥇 **가장 쉬운 방법: Railway CLI**

```powershell
# 1. CLI 설치
npm install -g @railway/cli

# 2. 로그인
railway login

# 3. 배포
cd c:\code\02_antigravity\PBM
railway init
railway up
```

**장점**:
- ✅ GitHub 푸시 불필요
- ✅ 인증 간단 (브라우저 로그인)
- ✅ 즉시 배포 가능

### 🥈 **프로덕션 권장: GitHub 연동**

```powershell
# 1. GitHub Desktop으로 푸시
# 2. Railway에서 저장소 연결
# 3. 자동 배포 활성화
```

**장점**:
- ✅ Git push 시 자동 재배포
- ✅ 버전 관리 용이
- ✅ 협업 가능

---

## 🎉 다음 단계

### Railway CLI 사용 시

1. **CLI 설치 및 로그인**
2. **배포 실행**: `railway up`
3. **URL 확인**: Railway 대시보드
4. **URL 알려주기**: GAS 코드 자동 업데이트

### GitHub 연동 사용 시

1. **GitHub에 푸시** (Desktop 또는 CLI)
2. **Railway 저장소 연결**
3. **배포 시작**
4. **URL 알려주기**: GAS 코드 자동 업데이트

---

**어떤 방법을 선호하시나요?**

- **빠른 배포**: Railway CLI 사용 (`railway up`)
- **장기 운영**: GitHub 연동 후 자동 배포

선택하신 방법으로 진행하겠습니다!
