# ngrok 수동 설정 가이드

## ✅ 완료된 작업
- ngrok 3.3.1 설치 확인
- authtoken 재설정 완료
- ngrok 프로세스 시작

## 🔧 ngrok URL 확인 방법

### 방법 1: ngrok 웹 인터페이스 (권장)

1. **브라우저에서 접속:**
   ```
   http://localhost:4040
   ```

2. **Tunnels 섹션 확인:**
   - "Forwarding" 항목에서 `https://...ngrok-free.app` URL 복사

3. **URL 형식:**
   ```
   https://xxxx-xxx-xxx-xxx.ngrok-free.app
   ```

### 방법 2: ngrok 콘솔 창 확인

ngrok이 실행 중인 PowerShell 창을 찾아서 다음 정보를 확인하세요:

```
Session Status                online
Account                       your-email
Version                       3.3.1
Region                        Asia Pacific (ap)
Latency                       -
Web Interface                 http://127.0.0.1:4040
Forwarding                    https://xxxx-xxx-xxx-xxx.ngrok-free.app -> http://localhost:8000
```

**중요**: `Forwarding` 줄의 `https://...` 주소를 복사하세요!

### 방법 3: 새로 시작 (ngrok이 실행 안되는 경우)

```powershell
# 1. 기존 ngrok 프로세스 종료
Stop-Process -Name "ngrok" -Force -ErrorAction SilentlyContinue

# 2. ngrok 시작
& "C:\Users\Administrator\AppData\Local\Microsoft\WinGet\Links\ngrok.exe" http 8000

# 3. 콘솔에 표시되는 URL 복사
```

## 📝 GAS 코드 업데이트

ngrok URL을 확인한 후:

1. **code.gs 파일 열기**
   - 경로: `c:\code\02_antigravity\PBM\app\gas\code.gs`

2. **BACKEND_URL 수정**
   ```javascript
   // 10-11번째 줄
   const BACKEND_URL = 'https://YOUR_NGROK_URL_HERE.ngrok-free.app';
   
   // 위 줄을 ngrok에서 받은 URL로 변경
   const BACKEND_URL = 'https://1234-567-890-123.ngrok-free.app';
   ```

3. **저장**

## 🚀 빠른 테스트

ngrok URL을 확인한 후 PowerShell에서 테스트:

```powershell
# YOUR_NGROK_URL을 실제 URL로 변경
Invoke-RestMethod -Uri "https://YOUR_NGROK_URL.ngrok-free.app/" -Method GET
```

성공하면 FastAPI 응답이 표시됩니다.

## ⚠️ 문제 해결

### ngrok 프로세스가 없는 경우
```powershell
& "C:\Users\Administrator\AppData\Local\Microsoft\WinGet\Links\ngrok.exe" http 8000
```

### "authentication failed" 오류
```powershell
& "C:\Users\Administrator\AppData\Local\Microsoft\WinGet\Links\ngrok.exe" config add-authtoken 2_39PvLDrlms4or2bQAdOWOtD1ZAz_5djtirREZ7CtzMcMpQ6vB
```

### localhost:4040 접속 안됨
- ngrok이 실제로 실행 중인지 확인
- 방화벽이 4040 포트를 차단하는지 확인
- ngrok 콘솔 창을 직접 확인

## 📋 다음 단계

1. ✅ ngrok URL 확인 (위 방법 중 하나 사용)
2. ✅ code.gs의 BACKEND_URL 업데이트
3. ✅ Google Apps Script에 배포
4. ✅ 모바일에서 테스트

---

**ngrok URL을 확인한 후 알려주시면 code.gs를 자동으로 업데이트해드리겠습니다!**
