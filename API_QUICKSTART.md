# SCHBC BBMS API - Quick Start Guide

## 🚀 서버 시작

```bash
cd c:\code\02_antigravity\PBM
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

서버 주소: `http://localhost:8000`

## 📚 API 문서

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🔐 테스트 계정

- **사번**: TEST001
- **비밀번호**: test123

## 📡 주요 엔드포인트

### 1. 로그인
```bash
POST /api/auth/login
{
  "emp_id": "TEST001",
  "password": "test123"
}
```

### 2. 재고 조회
```bash
GET /api/inventory/status
```

**응답 예시:**
- `total_items`: 전체 재고 항목 수
- `alert_count`: 알람 발생 항목 수  
- `rbc_ratio`: RBC 비율 (0.5)
- `items`: 재고 목록
  - RBC 제제는 `target_qty` 포함 (동적 계산)
  - `is_alert`: true면 재고 부족 알람

### 3. 재고 업데이트
```bash
POST /api/inventory/update
{
  "blood_type": "A",
  "prep_id": 1,
  "in_qty": 10,
  "out_qty": 0,
  "remark": "입고 - 2026-02-11"
}
```

**주의**: `remark` 필드는 필수입니다.

## ✅ 테스트 실행

```bash
python test_api.py
```

**결과**: 6/7 테스트 통과 ✅

## 🎯 RBC 비율 계산 로직

```python
# SystemSettings에서 RBC_RATIO 조회 (기본값 0.5)
total_safety = PRBC_safety + Prefiltered_safety
prbc_target = round(total_safety * ratio)
prefiltered_target = round(total_safety * (1 - ratio))
```

## 📊 현재 상태

- ✅ 24개 재고 항목 초기화
- ✅ 23개 알람 발생 (초기 재고 0)
- ✅ RBC 비율 0.5 설정
- ✅ JWT 인증 작동
- ✅ 재고 업데이트 및 로그 기록 작동
