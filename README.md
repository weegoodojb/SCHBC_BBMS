# SCHBC BBMS (순천향대학교 부천병원 혈액관리시스템)

Blood Bank Management System for Soonchunhyang University Bucheon Hospital

## 📋 프로젝트 개요

SCHBC BBMS는 병원 혈액은행의 재고 관리를 위한 웹 기반 시스템입니다.

### 주요 기능
- 🔐 JWT 기반 사용자 인증
- 📊 실시간 혈액 재고 현황 조회
- 🎯 RBC 제제 동적 목표재고 계산
- 🚨 재고 부족 알람 시스템
- 📝 입출고 로그 자동 기록

## 🛠️ 기술 스택

### Backend
- **Framework**: FastAPI 0.109.0
- **Database**: SQLite (개발), MySQL (프로덕션 예정)
- **ORM**: SQLAlchemy 2.0.25
- **Authentication**: JWT (python-jose)
- **Password Hashing**: bcrypt (passlib)

### Database Schema
- User (사용자 정보)
- BloodMaster (혈액제제 마스터)
- SafetyConfig (적정재고/알람기준)
- SystemSettings (시스템 설정)
- Inventory (현재 재고)
- StockLog (입출고 로그)

## 🚀 시작하기

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. 데이터베이스 초기화
```bash
python run_init_db.py
```

### 3. 테스트 사용자 생성
```bash
python create_user_simple.py
```

### 4. 서버 실행
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

서버 주소: `http://localhost:8000`

## 📚 API 문서

서버 실행 후 다음 주소에서 API 문서를 확인할 수 있습니다:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🔑 테스트 계정

- **사번**: TEST001
- **비밀번호**: test123

## 📡 주요 API 엔드포인트

### 인증
- `POST /api/auth/login` - 로그인 및 JWT 토큰 발급

### 재고 관리
- `GET /api/inventory/status` - 재고 현황 조회 (RBC 목표재고 계산 포함)
- `POST /api/inventory/update` - 재고 업데이트 (입출고 처리)

## 🎯 RBC 비율 계산 로직

시스템은 RBC 제제(PRBC, Prefiltered)의 목표재고를 동적으로 계산합니다:

```python
# SystemSettings에서 RBC_RATIO 조회 (기본값 0.5)
total_safety = PRBC_safety + Prefiltered_safety
prbc_target = round(total_safety * ratio)
prefiltered_target = round(total_safety * (1 - ratio))
```

## 📁 프로젝트 구조

```
PBM/
├── app/
│   ├── api/              # API 엔드포인트
│   │   ├── auth.py       # 인증
│   │   └── inventory.py  # 재고 관리
│   ├── core/             # 핵심 기능
│   │   ├── config.py     # 설정
│   │   └── security.py   # 보안 (JWT, bcrypt)
│   ├── database/         # 데이터베이스
│   │   ├── models.py     # SQLAlchemy 모델
│   │   ├── database.py   # DB 세션 관리
│   │   └── init_db.py    # DB 초기화
│   ├── schemas/          # Pydantic 스키마
│   │   └── schemas.py
│   ├── services/         # 비즈니스 로직
│   │   └── inventory_service.py
│   └── main.py           # FastAPI 애플리케이션
├── requirements.txt      # Python 의존성
├── run_init_db.py       # DB 초기화 스크립트
├── test_api.py          # API 테스트
└── README.md
```

## ✅ 테스트

API 테스트 실행:
```bash
python test_api.py
```

**테스트 결과**: 6/7 통과 ✅

## 📝 개발 로그

자세한 개발 내용은 [LOG.md](LOG.md)를 참조하세요.

## 🔄 다음 단계

- [ ] JWT 인증 미들웨어 적용
- [ ] 사용자 관리 기능 추가
- [ ] 리포팅 및 분석 기능
- [ ] MySQL 마이그레이션
- [ ] 모바일 앱 연동

## 📄 라이선스

MIT License

## 👥 개발자

Antigravity AI - SCHBC BBMS Development Team
