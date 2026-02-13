# SCHBC BBMS - Google Apps Script 배포 가이드

## 📋 개요

이 가이드는 Google Apps Script 모바일 UI를 FastAPI 백엔드와 연동하는 방법을 설명합니다.

---

## 🔧 1단계: ngrok 설정 (로컬 개발용)

### ngrok이란?
로컬 서버(localhost:8000)를 인터넷에서 접근 가능한 HTTPS URL로 노출시켜주는 터널링 서비스입니다.

### 설치 확인
ngrok은 이미 설치되어 있습니다 (winget으로 설치 완료).

### ngrok 인증 토큰 설정

1. **ngrok 계정 생성**
   - https://dashboard.ngrok.com/signup 접속
   - 무료 계정 생성 (Google/GitHub 계정으로 가능)

2. **인증 토큰 확인**
   - 로그인 후 https://dashboard.ngrok.com/get-started/your-authtoken 접속
   - "Your Authtoken" 복사

3. **토큰 설정**
   ```powershell
   # PowerShell에서 실행
   $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
   ngrok config add-authtoken YOUR_AUTH_TOKEN_HERE
   ```

### ngrok 터널 시작

1. **FastAPI 서버 실행 확인**
   ```powershell
   # 이미 실행 중이어야 함
   uvicorn app.main:app --reload
   ```

2. **ngrok 터널 시작**
   ```powershell
   # 새 PowerShell 창에서 실행
   $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
   ngrok http 8000
   ```

3. **공개 URL 확인**
   ```
   Forwarding    https://xxxx-xxx-xxx-xxx.ngrok-free.app -> http://localhost:8000
   ```
   
   이 `https://xxxx-xxx-xxx-xxx.ngrok-free.app` 주소를 복사하세요!

---

## 📱 2단계: Google Apps Script 배포

### 프로젝트 생성

1. **Google Apps Script 접속**
   - https://script.google.com 접속
   - "새 프로젝트" 클릭

2. **파일 추가**
   - 기본 `Code.gs` 파일 내용 삭제
   - `c:\code\02_antigravity\PBM\app\gas\code.gs` 내용 복사하여 붙여넣기
   
3. **HTML 파일 추가**
   - 좌측 메뉴에서 `+` 버튼 클릭 → "HTML" 선택
   - 파일명: `index` (확장자 제외)
   - `c:\code\02_antigravity\PBM\app\gas\index.html` 내용 복사하여 붙여넣기

### 백엔드 URL 설정

1. **code.gs 파일 열기**

2. **BACKEND_URL 수정**
   ```javascript
   // 이 부분을 찾아서
   const BACKEND_URL = 'https://YOUR_NGROK_URL_HERE.ngrok-free.app';
   
   // ngrok에서 받은 URL로 변경
   const BACKEND_URL = 'https://xxxx-xxx-xxx-xxx.ngrok-free.app';
   ```

3. **ADMIN_EMAIL 설정**
   ```javascript
   // 알람을 받을 이메일 주소 설정
   const ADMIN_EMAIL = 'your-email@schbc.ac.kr';
   ```

4. **저장** (Ctrl+S)

### 웹 앱으로 배포

1. **배포 버튼 클릭**
   - 우측 상단 "배포" → "새 배포"

2. **배포 설정**
   - 유형: "웹 앱"
   - 설명: "SCHBC BBMS v1.0"
   - 실행 계정: "나"
   - 액세스 권한: "나만" 또는 "모든 사용자"

3. **배포 클릭**
   - 권한 승인 필요 시 승인
   - 배포된 웹 앱 URL 복사

4. **웹 앱 URL 테스트**
   - 복사한 URL을 모바일 브라우저에서 열기
   - 로그인 화면이 나타나면 성공!

---

## 🧪 3단계: 테스트

### 연결 테스트

1. **서버 상태 확인**
   ```powershell
   # FastAPI 서버 실행 중인지 확인
   # ngrok 터널 실행 중인지 확인
   ```

2. **GAS 스크립트 에디터에서 테스트**
   - `code.gs`에서 `testConnection` 함수 선택
   - "실행" 버튼 클릭
   - 로그 확인: "서버 연결 성공" 메시지 확인

### 모바일 UI 테스트

1. **로그인**
   - 사번: `TEST001`
   - 비밀번호: `test123`

2. **재고 입력**
   - A형 PRBC에 `10` 입력
   - 비고에 "테스트 입력" 작성
   - "재고 저장" 버튼 클릭

3. **결과 확인**
   - 성공 메시지 확인
   - FastAPI 서버 로그에서 API 호출 확인
   - 데이터베이스에서 재고 업데이트 확인

### 이메일 알람 테스트

1. **수동 알람 체크**
   - GAS 스크립트 에디터에서 `manualAlertCheck` 함수 실행
   - Gmail에서 알람 이메일 수신 확인

2. **자동 알람 설정 (선택사항)**
   - 좌측 메뉴 "트리거" 클릭
   - "트리거 추가" 클릭
   - 함수: `manualAlertCheck`
   - 이벤트 소스: "시간 기반"
   - 시간 간격: "1시간마다" 또는 원하는 주기

---

## 🔄 4단계: ngrok URL 업데이트 (재시작 시)

ngrok 무료 버전은 재시작할 때마다 URL이 변경됩니다.

### URL 변경 시 절차

1. **새 ngrok URL 확인**
   ```powershell
   ngrok http 8000
   # 새로운 https://... URL 복사
   ```

2. **GAS 코드 업데이트**
   - Google Apps Script 에디터 열기
   - `code.gs`에서 `BACKEND_URL` 수정
   - 저장

3. **재배포 (선택사항)**
   - 기존 배포 유지 시: 저장만 하면 자동 반영
   - 새 버전 배포 시: "배포" → "배포 관리" → "새 버전"

---

## 📊 UI 레이아웃

```
┌─────────────────────────────────────────┐
│  🩸 SCHBC BBMS                          │
│  혈액 재고 관리 시스템                   │
├─────────────────────────────────────────┤
│ [사번] [비밀번호] [로그인]              │
├─────────────────────────────────────────┤
│       PRBC Pre-R  PC  SDP  FFP  Cryo   │
│  A    [ ]  [ ]  [ ]  [ ]  [ ]  [ ]     │
│  B    [ ]  [ ]  [ ]  [ ]  [ ]  [ ]     │
│  O    [ ]  [ ]  [ ]  [ ]  [ ]  [ ]     │
│  AB   [ ]  [ ]  [ ]  [ ]  [ ]  [ ]     │
├─────────────────────────────────────────┤
│ 비고: [                              ]  │
│       [초기화] [재고 저장]              │
└─────────────────────────────────────────┘
```

### 특징
- ✅ 4×6 고밀도 그리드 (24개 입력 셀)
- ✅ 모바일 숫자 키패드 자동 표시
- ✅ 컴팩트한 레이아웃 (한 화면에 모두 표시)
- ✅ 터치 친화적 디자인
- ✅ 반응형 레이아웃

---

## 🚨 이메일 알람 형식

```
제목: [SCHBC BBMS] 혈액 재고 부족 알람

다음 혈액 제제의 재고가 부족합니다:

1. A형 PRBC: 현재 3단위 (알람기준: 5단위)
2. B형 FFP: 현재 4단위 (알람기준: 6단위)
3. O형 PC: 현재 6단위 (알람기준: 7단위)

총 3개 항목이 알람 기준 이하입니다.

확인 시간: 2026-02-12 09:00:00
시스템: SCHBC BBMS
RBC 비율: 0.5
```

---

## 🔧 문제 해결

### ngrok 연결 오류
```
ERROR: authentication failed
```
**해결**: ngrok 인증 토큰 재설정
```powershell
ngrok config add-authtoken YOUR_TOKEN
```

### CORS 오류
FastAPI에 CORS 미들웨어가 이미 설정되어 있습니다. 문제 발생 시 `app/main.py` 확인.

### GAS 권한 오류
- Google Apps Script 실행 시 권한 승인 필요
- "고급" → "안전하지 않은 페이지로 이동" 클릭

### 모바일에서 입력 안됨
- 브라우저 캐시 삭제
- 시크릿 모드에서 테스트

---

## 📝 프로덕션 배포 (선택사항)

로컬 개발이 아닌 프로덕션 환경에서는:

1. **FastAPI 서버 배포**
   - Heroku, AWS, GCP 등에 배포
   - 고정 HTTPS URL 확보

2. **GAS BACKEND_URL 업데이트**
   - ngrok URL 대신 프로덕션 URL 사용

3. **환경 변수 설정**
   - `.env` 파일로 SECRET_KEY 등 관리

---

## ✅ 체크리스트

배포 전 확인사항:

- [ ] ngrok 인증 토큰 설정 완료
- [ ] FastAPI 서버 실행 중 (localhost:8000)
- [ ] ngrok 터널 실행 중
- [ ] GAS 프로젝트 생성 및 코드 복사 완료
- [ ] BACKEND_URL에 ngrok URL 설정
- [ ] ADMIN_EMAIL 설정
- [ ] 웹 앱으로 배포 완료
- [ ] 테스트 계정으로 로그인 테스트
- [ ] 재고 입력 및 저장 테스트
- [ ] 이메일 알람 테스트

---

**배포 완료!** 🎉

모바일에서 웹 앱 URL에 접속하여 혈액 재고를 관리하세요.
