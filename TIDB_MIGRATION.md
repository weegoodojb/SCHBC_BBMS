# TiDB Cloud 마이그레이션 가이드

## 📋 개요

SQLite에서 TiDB Cloud (MySQL 호환)로 데이터베이스를 마이그레이션합니다.

---

## 🔧 TiDB 연결 정보

### 현재 설정
- **Host:** `gateway01.ap-northeast-1.prod.aws.tidbcloud.com`
- **Port:** `4000`
- **User:** `4Hv47XPrF3C3oHV.root`
- **Password:** `qcu4ldWPyNVjiMxm`
- **Database:** `test` (임시, 나중에 `schbc_bbms`로 변경 예정)

### 연결 문자열
```
mysql+pymysql://4Hv47XPrF3C3oHV.root:qcu4ldWPyNVjiMxm@gateway01.ap-northeast-1.prod.aws.tidbcloud.com:4000/test?ssl_ca=&ssl_verify_cert=true&ssl_verify_identity=true
```

---

## ✅ 완료된 작업

### 1. 설정 파일 업데이트
- ✅ `app/core/config.py` - DATABASE_URL을 TiDB로 변경
- ✅ `requirements.txt` - PyMySQL 및 cryptography 추가

### 2. 드라이버 설치
```bash
pip install pymysql==1.1.0 cryptography==41.0.7
```

---

## 🧪 연결 테스트

### 1. 테스트 스크립트 실행
```bash
python test_tidb_connection.py
```

**확인 사항:**
- ✅ TiDB 버전 표시
- ✅ 현재 데이터베이스 이름 (test)
- ✅ 기존 테이블 목록

### 2. 예상 출력
```
============================================================
TiDB 연결 테스트
============================================================

연결 정보:
- Host: gateway01.ap-northeast-1.prod.aws.tidbcloud.com
- Port: 4000
- User: 4Hv47XPrF3C3oHV.root
- Database: test

1. 데이터베이스 엔진 생성 중...
2. 데이터베이스 연결 테스트 중...
✅ 연결 성공!
   TiDB 버전: 8.x.x-TiDB-vx.x.x
   현재 데이터베이스: test

3. 기존 테이블 목록:
   (테이블 없음)

============================================================
✅ TiDB 연결 테스트 성공!
============================================================
```

---

## 🗄️ 데이터베이스 초기화

### 1. 테이블 생성
```bash
python run_init_db.py
```

**생성될 테이블:**
- `users` - 사용자 정보
- `blood_master` - 혈액제제 마스터
- `safety_config` - 적정재고/알람기준
- `system_settings` - 시스템 설정
- `inventory` - 현재 재고
- `stock_log` - 입출고 로그

### 2. 테스트 사용자 생성
```bash
python create_user_simple.py
```

---

## 🔄 데이터베이스 이름 변경 (나중에)

현재는 `test` 데이터베이스를 사용하지만, 나중에 `schbc_bbms`로 변경할 수 있습니다.

### TiDB Cloud 콘솔에서 변경

1. **TiDB Cloud 대시보드 접속**
   - https://tidbcloud.com

2. **데이터베이스 생성**
   - Clusters → 클러스터 선택
   - SQL Editor 또는 Connect 메뉴
   - 새 데이터베이스 생성:
     ```sql
     CREATE DATABASE schbc_bbms;
     ```

3. **설정 파일 업데이트**
   - `app/core/config.py` 수정:
     ```python
     DATABASE_URL: str = "mysql+pymysql://4Hv47XPrF3C3oHV.root:qcu4ldWPyNVjiMxm@gateway01.ap-northeast-1.prod.aws.tidbcloud.com:4000/schbc_bbms?ssl_ca=&ssl_verify_cert=true&ssl_verify_identity=true"
     ```

4. **테이블 재생성**
   ```bash
   python run_init_db.py
   ```

---

## 📊 SQLite vs TiDB 비교

| 항목 | SQLite | TiDB Cloud |
|------|--------|------------|
| 위치 | 로컬 파일 | 클라우드 |
| 동시 접속 | 제한적 | 무제한 |
| 확장성 | 낮음 | 높음 |
| 백업 | 수동 | 자동 |
| SSL | 없음 | 있음 |
| 프로덕션 | ❌ | ✅ |

---

## ⚠️ 주의사항

### 1. SSL 연결 필수
TiDB Cloud는 SSL 연결을 요구합니다. 연결 문자열에 SSL 파라미터가 포함되어 있습니다.

### 2. 방화벽 설정
TiDB Cloud는 기본적으로 모든 IP에서 접속 가능하지만, 보안을 위해 IP 화이트리스트 설정을 권장합니다.

### 3. 데이터 마이그레이션
SQLite에서 기존 데이터가 있다면, 별도로 마이그레이션 스크립트가 필요합니다.

---

## 🚀 다음 단계

1. ✅ PyMySQL 설치
2. ✅ 연결 테스트 (`test_tidb_connection.py`)
3. ⬜ 테이블 생성 (`run_init_db.py`)
4. ⬜ 테스트 사용자 생성
5. ⬜ FastAPI 서버 재시작
6. ⬜ API 테스트
7. ⬜ (선택) 데이터베이스 이름을 `schbc_bbms`로 변경

---

## 🔧 문제 해결

### 연결 실패
```
pymysql.err.OperationalError: (2003, "Can't connect to MySQL server")
```
**해결:**
- 인터넷 연결 확인
- 방화벽 설정 확인
- TiDB Cloud 클러스터 상태 확인

### SSL 오류
```
SSL connection error
```
**해결:**
- `cryptography` 패키지 설치 확인
- 연결 문자열의 SSL 파라미터 확인

### 인증 실패
```
Access denied for user
```
**해결:**
- 사용자 이름과 비밀번호 재확인
- TiDB Cloud 콘솔에서 사용자 권한 확인

---

**TiDB Cloud 마이그레이션 준비 완료!** 🎉
