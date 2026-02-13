# ngrok 빠른 설정 가이드

## 🚀 빠른 시작 (3단계)

### 1. ngrok 인증 토큰 받기
1. https://dashboard.ngrok.com/signup 접속
2. 무료 계정 생성 (Google 계정 사용 가능)
3. https://dashboard.ngrok.com/get-started/your-authtoken 에서 토큰 복사

### 2. 토큰 설정
```powershell
# PowerShell에서 실행 (토큰은 한 번만 설정하면 됨)
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
ngrok config add-authtoken YOUR_AUTH_TOKEN_HERE
```

### 3. 터널 시작
```powershell
# FastAPI 서버가 실행 중인지 확인 후
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
ngrok http 8000
```

## 📋 생성된 URL 확인

터널이 시작되면 다음과 같은 화면이 나타납니다:

```
Session Status                online
Account                       your-email@gmail.com
Version                       3.3.1
Region                        Asia Pacific (ap)
Latency                       -
Web Interface                 http://127.0.0.1:4040
Forwarding                    https://xxxx-xxx-xxx-xxx.ngrok-free.app -> http://localhost:8000
```

**중요**: `https://xxxx-xxx-xxx-xxx.ngrok-free.app` 이 주소를 복사하세요!

## 🔄 GAS 코드 업데이트

1. Google Apps Script 에디터 열기
2. `code.gs` 파일에서 다음 부분 수정:

```javascript
// 이 줄을 찾아서
const BACKEND_URL = 'https://YOUR_NGROK_URL_HERE.ngrok-free.app';

// ngrok에서 받은 URL로 변경 (예시)
const BACKEND_URL = 'https://1234-567-890-123.ngrok-free.app';
```

3. 저장 (Ctrl+S)

## ✅ 연결 테스트

GAS 스크립트 에디터에서:
1. `testConnection` 함수 선택
2. "실행" 버튼 클릭
3. 로그에서 "서버 연결 성공" 확인

## 📱 모바일에서 접속

1. GAS 웹 앱 URL을 모바일 브라우저에서 열기
2. 로그인: TEST001 / test123
3. 재고 입력 테스트

## ⚠️ 주의사항

- ngrok 무료 버전은 **재시작할 때마다 URL이 변경**됩니다
- URL이 변경되면 GAS의 `BACKEND_URL`을 다시 업데이트해야 합니다
- 프로덕션 환경에서는 고정 URL을 가진 서버에 배포하세요

## 🔧 문제 해결

### "authentication failed" 오류
→ 토큰 설정을 다시 확인하세요

### ngrok 명령어 인식 안됨
→ PowerShell을 새로 열거나 PATH 새로고침:
```powershell
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
```

### 연결 타임아웃
→ FastAPI 서버가 실행 중인지 확인 (localhost:8000)
