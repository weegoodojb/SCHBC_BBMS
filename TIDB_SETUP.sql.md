# TiDB Cloud SQL Editor 실행용 SQL 파일

## 1. 기존 테이블 삭제 (있다면)

```sql
DROP TABLE IF EXISTS stock_log;
DROP TABLE IF EXISTS blood_inventory;
DROP TABLE IF EXISTS safety_config;
DROP TABLE IF EXISTS blood_master;
DROP TABLE IF EXISTS master_config;
DROP TABLE IF EXISTS users;
```

## 2. 테이블 생성

```sql
-- users 테이블
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    emp_id VARCHAR(20) UNIQUE NOT NULL COMMENT '직원번호',
    password_hash VARCHAR(255) NOT NULL COMMENT '비밀번호 해시',
    name VARCHAR(50) NOT NULL COMMENT '이름',
    email VARCHAR(100) COMMENT '이메일',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '생성일시',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일시'
) COMMENT='사용자 계정';

-- master_config 테이블
CREATE TABLE master_config (
    id INT AUTO_INCREMENT PRIMARY KEY,
    config_key VARCHAR(50) UNIQUE NOT NULL COMMENT '설정 키',
    config_value VARCHAR(255) NOT NULL COMMENT '설정 값',
    description TEXT COMMENT '설명',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '생성일시',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일시'
) COMMENT='시스템 설정';

-- blood_master 테이블
CREATE TABLE blood_master (
    id INT AUTO_INCREMENT PRIMARY KEY,
    component VARCHAR(20) NOT NULL COMMENT '혈액 성분',
    preparation VARCHAR(50) NOT NULL COMMENT '제제명',
    volume INT COMMENT '용량(ml)',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '생성일시',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일시',
    UNIQUE KEY unique_prep (component, preparation)
) COMMENT='혈액 제제 마스터';

-- safety_config 테이블
CREATE TABLE safety_config (
    id INT AUTO_INCREMENT PRIMARY KEY,
    blood_type VARCHAR(5) NOT NULL COMMENT '혈액형',
    prep_id INT NOT NULL COMMENT '제제 ID',
    safety_qty INT NOT NULL DEFAULT 0 COMMENT '안전 재고',
    alert_threshold INT NOT NULL DEFAULT 0 COMMENT '알림 기준',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '생성일시',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일시',
    FOREIGN KEY (prep_id) REFERENCES blood_master(id),
    UNIQUE KEY unique_safety (blood_type, prep_id)
) COMMENT='안전 재고 설정';

-- blood_inventory 테이블
CREATE TABLE blood_inventory (
    id INT AUTO_INCREMENT PRIMARY KEY,
    blood_type VARCHAR(5) NOT NULL COMMENT '혈액형',
    prep_id INT NOT NULL COMMENT '제제 ID',
    current_qty INT NOT NULL DEFAULT 0 COMMENT '현재 재고',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '생성일시',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일시',
    FOREIGN KEY (prep_id) REFERENCES blood_master(id),
    UNIQUE KEY unique_inventory (blood_type, prep_id)
) COMMENT='혈액 재고';

-- stock_log 테이블
CREATE TABLE stock_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    blood_type VARCHAR(5) NOT NULL COMMENT '혈액형',
    prep_id INT NOT NULL COMMENT '제제 ID',
    in_qty INT NOT NULL DEFAULT 0 COMMENT '입고 수량',
    out_qty INT NOT NULL DEFAULT 0 COMMENT '출고 수량',
    remark TEXT COMMENT '비고',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '생성일시',
    FOREIGN KEY (prep_id) REFERENCES blood_master(id)
) COMMENT='재고 입출고 로그';
```

## 3. 초기 데이터 주입

```sql
-- TEST001 사용자 (비밀번호: test123의 bcrypt 해시)
INSERT INTO users (emp_id, password_hash, name, email)
VALUES ('TEST001', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzpLaEg7Ky', '테스트사용자', 'test001@schbc.ac.kr');

-- RBC 비율 설정
INSERT INTO master_config (config_key, config_value, description)
VALUES ('rbc_ratio_percent', '50', 'PRBC vs Prefiltered RBC ratio percentage');

-- blood_master 데이터
INSERT INTO blood_master (component, preparation, volume) VALUES
('RBC', 'PRBC', 320),
('RBC', 'Prefiltered', 320),
('PLT', 'PC', 200),
('PLT', 'SDP', 200),
('FFP', 'FFP', 250),
('Cryo', 'Cryo', 50);

-- safety_config 데이터 (A, B, O, AB형)
INSERT INTO safety_config (blood_type, prep_id, safety_qty, alert_threshold) VALUES
-- A형
('A', 1, 20, 10), ('A', 2, 20, 10), ('A', 3, 10, 5), ('A', 4, 10, 5), ('A', 5, 15, 8), ('A', 6, 5, 3),
-- B형
('B', 1, 20, 10), ('B', 2, 20, 10), ('B', 3, 10, 5), ('B', 4, 10, 5), ('B', 5, 15, 8), ('B', 6, 5, 3),
-- O형
('O', 1, 20, 10), ('O', 2, 20, 10), ('O', 3, 10, 5), ('O', 4, 10, 5), ('O', 5, 15, 8), ('O', 6, 5, 3),
-- AB형
('AB', 1, 20, 10), ('AB', 2, 20, 10), ('AB', 3, 10, 5), ('AB', 4, 10, 5), ('AB', 5, 15, 8), ('AB', 6, 5, 3);

-- blood_inventory 초기화
INSERT INTO blood_inventory (blood_type, prep_id, current_qty) VALUES
-- A형
('A', 1, 0), ('A', 2, 0), ('A', 3, 0), ('A', 4, 0), ('A', 5, 0), ('A', 6, 0),
-- B형
('B', 1, 0), ('B', 2, 0), ('B', 3, 0), ('B', 4, 0), ('B', 5, 0), ('B', 6, 0),
-- O형
('O', 1, 0), ('O', 2, 0), ('O', 3, 0), ('O', 4, 0), ('O', 5, 0), ('O', 6, 0),
-- AB형
('AB', 1, 0), ('AB', 2, 0), ('AB', 3, 0), ('AB', 4, 0), ('AB', 5, 0), ('AB', 6, 0);
```

## 4. 확인 쿼리

```sql
-- 테이블 목록
SHOW TABLES;

-- 각 테이블 데이터 확인
SELECT COUNT(*) as count FROM users;
SELECT COUNT(*) as count FROM master_config;
SELECT COUNT(*) as count FROM blood_master;
SELECT COUNT(*) as count FROM safety_config;
SELECT COUNT(*) as count FROM blood_inventory;
SELECT COUNT(*) as count FROM stock_log;

-- TEST001 사용자 확인
SELECT emp_id, name, email FROM users WHERE emp_id = 'TEST001';
```

## 사용 방법

1. TiDB Cloud 콘솔 접속
2. SQL Editor 열기
3. 위 SQL을 순서대로 실행
4. 확인 쿼리로 데이터 검증
