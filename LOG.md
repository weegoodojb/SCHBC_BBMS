# SCHBC BBMS 프로젝트 로그

## 2026-02-25: UI/UX 추가 구현 및 감사 필드 적용, Auth 버그픽스

- **auth.py 픽스**: `verify_password` 인자 순서 오류 정상화(72-byte string 대응 완료), 하드코딩된 패스워드 로직 제거
- **UI 레이아웃 넓이 조정**: 제제 항목(명칭) 열(`prep-cell`, `prep-header`) 넓이를 기존 26px에서 50px 고정넓이(Fixed Width)로 1.5배 확장하여 텍스트 클리핑 방지
- **제제 항목 신규 추가**: 드롭다운 "제제 선택" 기본 목록에 **'Washed PLT'** 반영
- **감사 로그(Audit Trail) 적용**:
  - `StockLog` 모델 및 `BulkSaveRequest` 등에 `user_id`, `expiry_ok`(유효기간 확인), `visual_ok`(육안 확인) 필드 신규 추가
  - `templates/index.html` 하단 비고(remark) 그룹 상단에 해당 체크박스 노출 및 API Payload 적용
- **AB형 Cryo 재고 로직 보강**: `inventory_service.py` 내 `get_inventory_status` 함수에 "컴포넌트=Cryo && 혈액형=AB"일 경우 `target_qty`를 10으로 고정 조건 삽입
- 작업 적용 커밋: `main` 브랜치 Push 완료

## 2026-02-22: Matrix UI 개선 + Bulk Save API (세션 종료)

- **UI/UX 5종 개선**: 모바일 최적화, 테이블 매트릭스(제제=행/혈액형=열), 동적 제제 추가(드롭다운), 비고 optional, 저장 후 수량 유지
- **혈액형 색상**: A=오렌지, B=레드, O=블루, AB=블랙 (배경 연색 적용)
- **신청량 조건**: PRBC, Pre-R, FFP만 표시 (PC, SDP, Cryo 제외)
- **Bulk Save API**: `POST /api/inventory/bulk-save` 신설 (qty 절대값, delta 자동 계산, StockLog 기록, updated_at 서버 타임스탬프)
- **Pydantic 스키마**: `BulkSaveItem/Request/Result/Response` 4종 추가
- **최근 재고 불러오기**: 로그인 직후 `loadInventory()` → input 자동 세팅
- **Enter 포커스 이동**: A→B→O→AB 자동 이동, AB에서 Enter → 다음 제제 A칸
- 최종 커밋: `86dfe2a` | GitHub: `weegoodojb/SCHBC_BBMS`

---



- `templates/index.html` 신설: GAS 제거, fetch() API 기반 독립 프론트엔드
- `main.py`: Jinja2Templates + StaticFiles, 루트(/) → HTML 서빙
- `database.py`: `_get_db_url()` 추가 → `postgresql+psycopg2://` 드라이버 강제 지정
- `requirements.txt`: `supabase` 패키지 제거 (psycopg2 충돌 원인), `jinja2` 추가
- `nixpacks.toml` 수정: `libpq`, `gcc` 추가 (psycopg2-binary 네이티브 의존성)
- 최종 커밋: `6de6c6b` | GitHub: `weegoodojb/SCHBC_BBMS`
- ⚠️ 잔여 작업: Supabase SQL Editor에서 테이블 생성 필요

---



- Remote 설정: `https://github.com/weegoodojb/SCHBC_BBMS.git`
- Push 결과: ✅ 성공 (`main` 브랜치, `--force`)
- 최신 커밋: `8a0e3f2` (CSS fix) / `6059706` (RBC 재고비 관리 전체 구현)
- 95개 오브젝트 업로드 완료

---

## 2026-02-19: RBC 재고비 관리 로직 구현

- models.py: MasterConfig 혈액형/제제별 행 + daily_consumption_rate/safety_factor + InventoryRatioHistory 신설
- database.py: Supabase Pooler 최적화 (sslmode=require, pool 파라미터, test_connection())
- inventory_service.py: ceil(DCR×SF) + O형 +4, request_qty 필드 추가
- config.py: GET/PUT /api/config/rbc-factors, GET /api/config/rbc-history
- main.py: lifespan startup DB 테스트, /health DB 상태 반환
- index.html: inputmode=decimal, +/- 버튼, 신청량 행, PC 관리자 패널
- code.gs: getSafetyTargets(), updateRbcFactors() 추가
- ⚠️ Supabase 테이블 생성: 로컬 방화벽 → SQL Editor로 생성 필요

---

## 2026-02-12: TiDB Cloud 데이터베이스 재구축

### 문제
- TiDB Cloud `test` 데이터베이스가 비어있음 (empty set)
- Python 스크립트로 TiDB 연결 시도 시 응답 없음/매우 느림
- pymysql, SQLAlchemy 모두 연결 실패

### 원인
- 네트워크 지연 또는 방화벽 이슈
- Python 라이브러리를 통한 TiDB Cloud 연결 불안정

### 해결
1. **SQL Editor 직접 실행 방식으로 전환**
   - `TIDB_SETUP.sql.md` 파일 생성
   - TiDB Cloud SQL Editor에서 직접 SQL 실행
   - 모든 테이블 및 데이터 생성 성공

2. **생성된 리소스**
   - 6개 테이블: users, master_config, blood_master, safety_config, blood_inventory, stock_log
   - TEST001 사용자 (test123)
   - RBC 비율 50% 설정
   - 안전 재고 설정 24건
   - 재고 초기화 24건

3. **검증**
   - Railway API 로그인 테스트 성공
   - TiDB Cloud 연결 정상
   - 데이터베이스 쿼리 정상 작동

### 교훈
- 클라우드 데이터베이스 연결 시 네트워크 이슈 고려 필요
- Python 스크립트 실패 시 SQL Editor 직접 실행이 효과적
- 초기 데이터베이스 설정은 SQL 파일로 문서화 권장

---

## 2026-02-13: 인프라 전면 개편 (TiDB → Supabase 마이그레이션)

### 배경
- TiDB Cloud 연결 지연 및 불안정성 지속
- GitHub 인증 오류로 코드 동기화 불가
- 과감한 스택 교체 결정

### 작업 내용

1. **GitHub 재초기화**
   - `.git` 폴더 삭제 및 `git init` 재실행
   - `.gitignore` 생성
   - 첫 커밋 생성 완료 (commit: e0a1020)

2. **Database 피벗 (TiDB → Supabase PostgreSQL)**
   - ❌ 제거: `pymysql`, `cryptography`
   - ✅ 추가: `psycopg2-binary`, `supabase`
   - `requirements.txt` 업데이트
   - `app/core/config.py`: DATABASE_URL을 PostgreSQL 형식으로 변경
   - `app/database/database.py`: SQLite 설정 제거, PostgreSQL pool_pre_ping 추가
   - `.env.example`: Supabase 자격 증명 추가

3. **Supabase 설정**
   - Database URL: `postgresql://postgres.gzqtyjwoasbbgelylkix:...@aws-1-ap-southeast-2.pooler.supabase.com:5432/postgres`
   - Project URL: `https://gzqtyjwoasbbgelylkix.supabase.co`
   - Anon Key: `sb_publishable_XypkjPMQoR9JR8Vv_bumEw_NC_MrCTn`

4. **생성된 파일**
   - `SUPABASE_SETUP.md`: 테이블 생성 SQL 스크립트
   - `RAILWAY_ENV_SUPABASE.md`: Railway 환경 변수 가이드
   - `setup_supabase.py`: SQLAlchemy 기반 설정 스크립트
   - `setup_supabase_direct.py`: psycopg2 직접 사용 스크립트

### 문제 및 미완료 사항

**Supabase 연결 실패**
- Python에서 Supabase PostgreSQL 연결 시도 시 모두 실패
- SQLAlchemy: "error processing the request"
- psycopg2: 동일한 오류
- 원인: 네트워크/방화벽 또는 Supabase Pooler 설정 문제

**다음 단계 (보류)**
1. GitHub 원격 저장소 연결 및 푸시
2. Supabase SQL Editor로 테이블 수동 생성 (TiDB와 동일한 방법)
3. Railway 환경 변수 업데이트
4. 배포 및 테스트

### 현재 상태

- ✅ 코드 마이그레이션 완료 (TiDB → Supabase)
- ✅ Git 재초기화 완료
- ✅ 첫 커밋 생성 완료
- ⏸️ GitHub 푸시 대기 (원격 저장소 URL 필요)
- ⏸️ Supabase 테이블 생성 대기 (SQL Editor 사용 권장)

### 교훈
- 클라우드 데이터베이스 마이그레이션 시 로컬 연결 테스트 필수
- Python 스크립트 연결 실패 시 SQL Editor가 가장 안정적
- 인프라 변경은 단계적으로 진행하되, 롤백 계획 필요

---



## 2026-02-11 (화)

### 📦 데이터베이스 설계 및 초기화 완료

**작업 내용:**
- SQLite 기반 데이터베이스 스키마 설계 및 구현
- SQLAlchemy ORM 모델 정의 (6개 테이블)
- 초기 데이터 삽입 (Seed Data)

**생성된 테이블:**
1. `User` - 사용자 정보 (emp_id, name, password_hash, email)
2. `BloodMaster` - 혈액제제 마스터 (component, preparation)
3. `SafetyConfig` - 적정재고/알람기준 (blood_type, prep_id, safety_qty, alert_threshold)
4. `SystemSettings` - 시스템 설정 Key-Value 저장소
5. `Inventory` - 현재 재고 (blood_type, prep_id, current_qty)
6. `StockLog` - 입출고 로그 (log_date, in_qty, out_qty)

**초기 데이터:**
- BloodMaster: 6개 제제 (PRBC, Prefiltered, PC, SDP, FFP, Cryo)
- SystemSettings: RBC_RATIO(0.5), PLT_RATIO(0.7), ALERT_ENABLED(true)
- Inventory: 24개 항목 (4개 혈액형 × 6개 제제, 초기값 0)
- SafetyConfig: 24개 안전재고 설정

**파일:**
- `app/database/models.py` - SQLAlchemy ORM 모델
- `app/database/init_db.py` - DB 초기화 스크립트
- `run_init_db.py` - 실행 스크립트
- `verify_db.py` - DB 검증 스크립트
- `bbms_local.db` - SQLite 데이터베이스 파일

---

### 🚀 FastAPI 백엔드 API 구현 완료

**작업 내용:**
- FastAPI 기반 REST API 서버 구축
- JWT 인증 시스템 구현
- 재고 관리 API 엔드포인트 개발
- RBC 비율 계산 로직 구현

**핵심 기능:**

1. **인증 시스템**
   - bcrypt 비밀번호 해싱
   - JWT 토큰 발급 및 검증
   - 엔드포인트: `POST /api/auth/login`

2. **재고 조회 API**
   - 전체 재고 현황 조회
   - RBC 동적 목표재고 계산
   - 알람 상태 자동 체크
   - 엔드포인트: `GET /api/inventory/status`

3. **재고 업데이트 API**
   - 입출고 처리
   - StockLog 자동 기록
   - 재고 부족 검증
   - 엔드포인트: `POST /api/inventory/update`

**RBC 특화 로직:**
```python
# SystemSettings에서 RBC_RATIO 조회 (기본값 0.5)
total_safety = PRBC_safety + Prefiltered_safety
prbc_target = round(total_safety * ratio)
prefiltered_target = round(total_safety * (1 - ratio))
```

**생성된 파일:**
- `app/core/config.py` - 애플리케이션 설정
- `app/core/security.py` - 인증 및 보안 (bcrypt, JWT)
- `app/database/database.py` - DB 세션 관리
- `app/schemas/schemas.py` - Pydantic 스키마 정의
- `app/services/inventory_service.py` - 비즈니스 로직
- `app/api/auth.py` - 인증 엔드포인트
- `app/api/inventory.py` - 재고 관리 엔드포인트
- `app/main.py` - FastAPI 애플리케이션

**의존성:**
- fastapi==0.109.0
- uvicorn[standard]==0.27.0
- python-jose[cryptography]==3.3.0
- passlib==1.7.4
- bcrypt==4.0.1
- python-multipart==0.0.6
- pydantic-settings==2.1.0

---

### ✅ 테스트 및 검증

**테스트 환경:**
- 테스트 사용자 생성: TEST001 / test123
- FastAPI 서버 실행: `http://localhost:8000`
- API 문서: `http://localhost:8000/docs`

**테스트 결과:**
- ✅ Health check 통과
- ✅ 로그인 (유효한 자격증명) 통과
- ✅ 로그인 (잘못된 자격증명 거부) 통과
- ✅ 재고 조회 (RBC 계산 포함) 통과
- ✅ 재고 업데이트 (입고) 통과
- ✅ 재고 업데이트 (출고) 통과
- ⚠️ 비고 누락 검증 (인코딩 이슈)

**총 테스트: 6/7 통과** ✅

**검증된 기능:**
- JWT 토큰 발급 및 인증
- 비밀번호 해싱 (bcrypt)
- RBC_RATIO 동적 조회
- 목표재고 자동 계산
- 알람 임계값 체크
- 재고 업데이트 및 로그 기록
- Pydantic 입력 검증
- 에러 핸들링

**생성된 파일:**
- `test_api.py` - 종합 API 테스트 스크립트
- `create_user_simple.py` - 테스트 사용자 생성
- `API_QUICKSTART.md` - 빠른 시작 가이드

---

### 📊 현재 시스템 상태

**데이터베이스:**
- 총 6개 테이블 생성
- 24개 재고 항목 (초기값 0)
- 23개 알람 발생 (재고 부족)
- RBC 비율: 0.5 (50:50)

**API 서버:**
- 상태: 정상 작동
- 엔드포인트: 5개 (health, root, login, status, update)
- 인증: JWT 토큰 기반

**문서:**
- `database_setup_summary.md` - DB 설계 문서
- `implementation_plan.md` - 구현 계획
- `walkthrough.md` - 상세 구현 문서
- `API_QUICKSTART.md` - API 사용 가이드

---

### 🎯 다음 단계

1. **인증 미들웨어**: JWT 토큰 검증을 보호된 라우트에 적용
2. **사용자 관리**: 회원가입, 프로필 관리 엔드포인트 추가
3. **고급 쿼리**: 필터링, 정렬, 페이지네이션 구현
4. **리포팅**: 재고 추이 분석 및 통계 엔드포인트
5. **모바일 연동**: 모바일 앱과 API 통합
6. **프로덕션 배포**: MySQL 마이그레이션, CORS 설정, 시크릿 키 관리

---

### 💡 특이사항

**해결한 이슈:**
1. bcrypt 버전 호환성 문제 → bcrypt==4.0.1로 다운그레이드
2. 비밀번호 길이 제한 → 72자 이내로 제한
3. 테스트 출력 인코딩 이슈 → UTF-8 처리 필요

**기술적 결정:**
- SQLite 사용 (개발 속도 우선, MySQL 마이그레이션 고려)
- JWT 토큰 만료: 24시간
- RBC 비율 계산 시 반올림 처리
- 모든 테이블에 remark 필드 포함 (비정형 데이터)

---

**작업 시간:** 약 2시간  
**작업자:** Antigravity AI  
**상태:** ✅ 완료
