# ngrok 터널 설정 완료 가이드

## ✅ 완료된 작업

### 1. 공인 IP 확인
```
공인 IP: 59.17.51.1
```
**참고**: 이 IP는 localtunnel 사용 시 패스워드로 요구되는 주소입니다.

### 2. Localtunnel → ngrok 전환
- ✅ Localtunnel 프로세스 종료
- ✅ ngrok 3.3.1 실행 (포트 8000)
- ✅ ngrok 터널 시작됨

---

## 🔍 ngrok URL 확인 방법

### 방법 1: 브라우저에서 확인 (권장)

1. **브라우저에서 접속**:
   ```
   http://localhost:4040
   ```

2. **Tunnels 섹션에서 URL 복사**:
   - "Forwarding" 항목에서 `https://xxxx-xxx-xxx-xxx.ngrok-free.app` URL 확인
   - 이 URL을 복사하세요!

### 방법 2: ngrok 콘솔 창 확인

ngrok이 실행 중인 PowerShell 창을 찾아서 다음 정보를 확인:

```
Session Status                online
Account                       your-email
Version                       3.3.1
Region                        Asia Pacific (ap)
Web Interface                 http://127.0.0.1:4040
Forwarding                    https://xxxx-xxx-xxx-xxx.ngrok-free.app -> http://localhost:8000
```

**중요**: `Forwarding` 줄의 `https://...ngrok-free.app` 주소를 복사하세요!

---

## 📝 GAS 코드 업데이트 필요

ngrok URL을 확인한 후 다음 작업이 필요합니다:

### 1. BACKEND_URL 업데이트
```javascript
// app/gas/code.gs 파일
const BACKEND_URL = 'https://YOUR-NGROK-URL.ngrok-free.app';
```

### 2. ngrok 경고 우회 헤더 추가

모든 API 요청에 다음 헤더 추가:
```javascript
headers: {
  'ngrok-skip-browser-warning': '69420',  // ngrok 경고 우회
  'Bypass-Tunnel-Reminder': 'true'        // 기존 헤더 유지
}
```

---

## 🎯 다음 단계

1. **ngrok URL 확인**:
   - http://localhost:4040 접속
   - Forwarding URL 복사

2. **URL 알려주기**:
   - 확인한 ngrok URL을 알려주시면 자동으로 GAS 코드를 업데이트하겠습니다

3. **테스트**:
   - 업데이트 후 로그인 테스트 진행

---

## ⚠️ ngrok vs localtunnel 비교

| 항목 | ngrok | localtunnel |
|------|-------|-------------|
| 패스워드 | ❌ 없음 | ✅ 있음 (공인 IP) |
| 경고 페이지 | 헤더로 우회 가능 | Continue 클릭 필요 |
| 안정성 | 높음 | 중간 |
| **현재 상태** | ✅ 실행 중 | ❌ 중지됨 |

---

**ngrok URL을 확인하신 후 알려주시면 즉시 GAS 코드를 업데이트하겠습니다!**
