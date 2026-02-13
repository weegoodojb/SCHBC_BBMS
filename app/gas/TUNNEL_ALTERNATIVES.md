# ngrok 문제 해결 및 대안

## 🚨 현재 상황

ngrok 3.3.1이 설치되어 있지만, 설정 파일 버전 호환성 문제로 실행되지 않습니다.

**오류 메시지:**
```
ERROR: configuration file version "3" is not supported by this release
ERROR: upgrade to the latest version at https://ngrok.com/download
```

## 🔧 시도한 해결 방법

1. ✅ ngrok 인증 토큰 설정
2. ✅ 버전 2 호환 설정 파일 생성
3. ✅ 직접 실행 파일 경로 사용
4. ❌ 여전히 버전 오류 발생

## 💡 해결 방법

### 방법 1: localtunnel 사용 (권장 - 빠름)

localtunnel은 ngrok의 대안으로, 설치와 사용이 매우 간단합니다.

```powershell
# 1. localtunnel 설치 (npm 필요)
npm install -g localtunnel

# 2. 터널 시작
lt --port 8000

# 3. 생성된 URL 복사
# 출력 예: https://your-subdomain.loca.lt
```

**장점:**
- 설치 간단
- 인증 불필요
- 즉시 사용 가능

**단점:**
- 첫 접속 시 경고 페이지 표시 (Continue 클릭 필요)

### 방법 2: ngrok 재설치

```powershell
# 1. 기존 ngrok 제거
winget uninstall ngrok.ngrok

# 2. 설정 파일 삭제
Remove-Item -Path "$env:USERPROFILE\.ngrok2" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "$env:LOCALAPPDATA\ngrok" -Recurse -Force -ErrorAction SilentlyContinue

# 3. ngrok 재설치
winget install ngrok.ngrok

# 4. 인증 토큰 재설정
ngrok config add-authtoken 2_39PvLDrlms4or2bQAdOWOtD1ZAz_5djtirREZ7CtzMcMpQ6vB

# 5. 터널 시작
ngrok http 8000
```

### 방법 3: Cloudflare Tunnel (무료, 안정적)

```powershell
# 1. cloudflared 설치
winget install Cloudflare.cloudflared

# 2. 터널 시작 (인증 불필요)
cloudflared tunnel --url http://localhost:8000

# 3. 생성된 URL 복사
```

**장점:**
- 안정적
- 무료
- 인증 불필요

## 🚀 즉시 실행 가능한 명령어

### localtunnel 사용 (가장 빠름)

```powershell
# npm이 설치되어 있다면
npm install -g localtunnel
lt --port 8000
```

### Cloudflare Tunnel 사용

```powershell
winget install Cloudflare.cloudflared
cloudflared tunnel --url http://localhost:8000
```

## 📝 GAS 코드 업데이트

어떤 방법을 사용하든, 생성된 URL을 `code.gs`에 업데이트하세요:

```javascript
// localtunnel 사용 시
const BACKEND_URL = 'https://your-subdomain.loca.lt';

// cloudflare 사용 시
const BACKEND_URL = 'https://xxxx-xxxx-xxxx.trycloudflare.com';

// ngrok 사용 시 (재설치 성공 후)
const BACKEND_URL = 'https://xxxx-xxx-xxx-xxx.ngrok-free.app';
```

## ⚠️ 주의사항

- **localtunnel**: 첫 접속 시 경고 페이지가 나타나지만 "Continue" 클릭하면 정상 작동
- **cloudflare**: URL이 매번 변경됨 (무료 버전)
- **ngrok**: 재설치 후에도 문제가 지속되면 다른 방법 사용 권장

## 🎯 권장 순서

1. **localtunnel 시도** (가장 빠르고 간단)
2. localtunnel이 안되면 **Cloudflare Tunnel**
3. 둘 다 안되면 **ngrok 재설치**
