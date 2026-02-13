# Railway 환경 변수 설정 가이드

## ⚠️ 현재 상태

Railway 배포는 완료되었으나, **환경 변수가 설정되지 않아** 애플리케이션이 시작되지 않았습니다.

**오류**: `404 Application not found`  
**원인**: 환경 변수 미설정으로 FastAPI 서버 시작 실패

---

## 🔧 해결 방법: Railway 대시보드에서 환경 변수 설정

### Step 1: Railway 대시보드 접속

1. 브라우저에서 https://railway.app 접속
2. 로그인 (위종빈 계정)
3. **outstanding-courage** 프로젝트 클릭

### Step 2: Variables 탭 이동

1. 왼쪽 메뉴에서 **Variables** 클릭
2. **New Variable** 버튼 클릭

### Step 3: 환경 변수 추가

다음 변수를 하나씩 추가하세요:

#### 1. DATABASE_URL (필수)
```
Variable Name: DATABASE_URL
Value: mysql+pymysql://4Hv47XPrF3C3oHV.root:qcu4ldWPyNVjiMxm@gateway01.ap-northeast-1.prod.aws.tidbcloud.com:4000/test?ssl_ca=&ssl_verify_cert=true&ssl_verify_identity=true
```

#### 2. SECRET_KEY (필수)
```
Variable Name: SECRET_KEY
Value: schbc-bbms-production-secret-key-2026-change-this-in-production-env
```

#### 3. DEBUG (권장)
```
Variable Name: DEBUG
Value: False
```

#### 4. APP_NAME (선택)
```
Variable Name: APP_NAME
Value: SCHBC BBMS
```

#### 5. APP_VERSION (선택)
```
Variable Name: APP_VERSION
Value: 1.0.0
```

### Step 4: 자동 재배포 대기

환경 변수를 추가하면:
1. Railway가 자동으로 재배포 시작
2. **Deployments** 탭에서 진행 상황 확인
3. 재배포 완료 대기 (약 1-2분)

### Step 5: 배포 완료 확인

재배포가 완료되면:
- **Deployments** 탭에서 "Success" 상태 확인
- 로그에서 "Application startup complete" 메시지 확인

---

## 🧪 재배포 후 테스트

### 1. Health Check
```bash
curl https://outstanding-courage.up.railway.app/health
```

**예상 응답**:
```json
{
  "status": "healthy",
  "app": "SCHBC BBMS API",
  "version": "1.0.0"
}
```

### 2. RBC 비율 API
```bash
curl https://outstanding-courage.up.railway.app/api/config/rbc-ratio
```

### 3. 로그인 테스트
```bash
curl -X POST https://outstanding-courage.up.railway.app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"emp_id": "TEST001", "password": "test123"}'
```

---

## 📋 체크리스트

### Railway 대시보드 작업
- [ ] Railway 대시보드 접속
- [ ] outstanding-courage 프로젝트 선택
- [ ] Variables 탭 이동
- [ ] DATABASE_URL 추가
- [ ] SECRET_KEY 추가
- [ ] DEBUG 추가 (선택)
- [ ] 자동 재배포 시작 확인
- [ ] Deployments 탭에서 "Success" 확인

### 재배포 후 검증
- [ ] Health endpoint 테스트
- [ ] RBC 비율 API 테스트
- [ ] 로그인 테스트
- [ ] 재고 조회 테스트

---

## 🚀 Railway CLI로 환경 변수 설정 (대안)

대시보드 대신 CLI로도 설정 가능합니다:

```bash
# 서비스 링크 확인
railway service

# 환경 변수 설정
railway variables set DATABASE_URL="mysql+pymysql://4Hv47XPrF3C3oHV.root:qcu4ldWPyNVjiMxm@gateway01.ap-northeast-1.prod.aws.tidbcloud.com:4000/test?ssl_ca=&ssl_verify_cert=true&ssl_verify_identity=true"

railway variables set SECRET_KEY="schbc-bbms-production-secret-key-2026-change-this-in-production-env"

railway variables set DEBUG="False"

# 재배포
railway up
```

---

## ⏱️ 예상 소요 시간

- 환경 변수 설정: 2-3분
- 자동 재배포: 1-2분
- **총 소요 시간**: 약 3-5분

---

**환경 변수 설정 후 재배포가 완료되면 알려주세요!**

그러면 즉시 서버 health check와 첫 데이터 입력 테스트를 진행하겠습니다.
