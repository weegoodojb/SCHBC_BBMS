"""
TiDB Cloud 데이터베이스 전체 재구축
- 모든 테이블 생성
- 초기 데이터 주입
"""
import pymysql
from passlib.context import CryptContext
from datetime import datetime

# 비밀번호 해싱
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# TiDB Cloud 연결
connection = pymysql.connect(
    host='gateway01.ap-northeast-1.prod.aws.tidbcloud.com',
    port=4000,
    user='4Hv47XPrF3C3oHV.root',
    password='qcu4ldWPyNVjiMxm',
    database='test',
    ssl_verify_cert=True,
    ssl_verify_identity=True
)

try:
    cursor = connection.cursor()
    
    print("=" * 80)
    print("TiDB Cloud 데이터베이스 재구축 시작")
    print("=" * 80)
    print()
    
    # 1. 기존 테이블 삭제 (있다면)
    print("📋 Step 1: 기존 테이블 정리")
    tables_to_drop = ['stock_log', 'blood_inventory', 'safety_config', 'blood_master', 'master_config', 'users']
    for table in tables_to_drop:
        try:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
            print(f"  ✓ {table} 테이블 삭제")
        except Exception as e:
            print(f"  - {table} 테이블 삭제 스킵: {e}")
    
    connection.commit()
    print()
    
    # 2. 테이블 생성
    print("📋 Step 2: 테이블 생성")
    
    # users 테이블
    cursor.execute("""
        CREATE TABLE users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            emp_id VARCHAR(20) UNIQUE NOT NULL COMMENT '직원번호',
            password_hash VARCHAR(255) NOT NULL COMMENT '비밀번호 해시',
            name VARCHAR(50) NOT NULL COMMENT '이름',
            email VARCHAR(100) COMMENT '이메일',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '생성일시',
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일시'
        ) COMMENT='사용자 계정'
    """)
    print("  ✓ users 테이블 생성")
    
    # master_config 테이블
    cursor.execute("""
        CREATE TABLE master_config (
            id INT AUTO_INCREMENT PRIMARY KEY,
            config_key VARCHAR(50) UNIQUE NOT NULL COMMENT '설정 키',
            config_value VARCHAR(255) NOT NULL COMMENT '설정 값',
            description TEXT COMMENT '설명',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '생성일시',
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일시'
        ) COMMENT='시스템 설정'
    """)
    print("  ✓ master_config 테이블 생성")
    
    # blood_master 테이블
    cursor.execute("""
        CREATE TABLE blood_master (
            id INT AUTO_INCREMENT PRIMARY KEY,
            component VARCHAR(20) NOT NULL COMMENT '혈액 성분',
            preparation VARCHAR(50) NOT NULL COMMENT '제제명',
            volume INT COMMENT '용량(ml)',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '생성일시',
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일시',
            UNIQUE KEY unique_prep (component, preparation)
        ) COMMENT='혈액 제제 마스터'
    """)
    print("  ✓ blood_master 테이블 생성")
    
    # safety_config 테이블
    cursor.execute("""
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
        ) COMMENT='안전 재고 설정'
    """)
    print("  ✓ safety_config 테이블 생성")
    
    # blood_inventory 테이블
    cursor.execute("""
        CREATE TABLE blood_inventory (
            id INT AUTO_INCREMENT PRIMARY KEY,
            blood_type VARCHAR(5) NOT NULL COMMENT '혈액형',
            prep_id INT NOT NULL COMMENT '제제 ID',
            current_qty INT NOT NULL DEFAULT 0 COMMENT '현재 재고',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '생성일시',
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일시',
            FOREIGN KEY (prep_id) REFERENCES blood_master(id),
            UNIQUE KEY unique_inventory (blood_type, prep_id)
        ) COMMENT='혈액 재고'
    """)
    print("  ✓ blood_inventory 테이블 생성")
    
    # stock_log 테이블
    cursor.execute("""
        CREATE TABLE stock_log (
            id INT AUTO_INCREMENT PRIMARY KEY,
            blood_type VARCHAR(5) NOT NULL COMMENT '혈액형',
            prep_id INT NOT NULL COMMENT '제제 ID',
            in_qty INT NOT NULL DEFAULT 0 COMMENT '입고 수량',
            out_qty INT NOT NULL DEFAULT 0 COMMENT '출고 수량',
            remark TEXT COMMENT '비고',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '생성일시',
            FOREIGN KEY (prep_id) REFERENCES blood_master(id)
        ) COMMENT='재고 입출고 로그'
    """)
    print("  ✓ stock_log 테이블 생성")
    
    connection.commit()
    print()
    
    # 3. 초기 데이터 주입
    print("📋 Step 3: 초기 데이터 주입")
    
    # TEST001 사용자 생성
    password_hash = pwd_context.hash("test123")
    cursor.execute("""
        INSERT INTO users (emp_id, password_hash, name, email)
        VALUES (%s, %s, %s, %s)
    """, ('TEST001', password_hash, '테스트사용자', 'test001@schbc.ac.kr'))
    print("  ✓ TEST001 사용자 생성")
    
    # RBC 비율 설정 (5:5 = 50%)
    cursor.execute("""
        INSERT INTO master_config (config_key, config_value, description)
        VALUES (%s, %s, %s)
    """, ('rbc_ratio_percent', '50', 'PRBC vs Prefiltered RBC ratio percentage'))
    print("  ✓ RBC 비율 설정 (50%)")
    
    # blood_master 초기 데이터
    blood_products = [
        ('RBC', 'PRBC', 320),
        ('RBC', 'Prefiltered', 320),
        ('PLT', 'PC', 200),
        ('PLT', 'SDP', 200),
        ('FFP', 'FFP', 250),
        ('Cryo', 'Cryo', 50)
    ]
    
    for component, preparation, volume in blood_products:
        cursor.execute("""
            INSERT INTO blood_master (component, preparation, volume)
            VALUES (%s, %s, %s)
        """, (component, preparation, volume))
    print(f"  ✓ 혈액 제제 마스터 데이터 {len(blood_products)}건 생성")
    
    # safety_config 초기 데이터 (A, B, O, AB형)
    blood_types = ['A', 'B', 'O', 'AB']
    safety_configs = [
        (1, 20, 10),  # PRBC: 안전재고 20, 알림기준 10
        (2, 20, 10),  # Prefiltered: 안전재고 20, 알림기준 10
        (3, 10, 5),   # PC: 안전재고 10, 알림기준 5
        (4, 10, 5),   # SDP: 안전재고 10, 알림기준 5
        (5, 15, 8),   # FFP: 안전재고 15, 알림기준 8
        (6, 5, 3)     # Cryo: 안전재고 5, 알림기준 3
    ]
    
    for blood_type in blood_types:
        for prep_id, safety_qty, alert_threshold in safety_configs:
            cursor.execute("""
                INSERT INTO safety_config (blood_type, prep_id, safety_qty, alert_threshold)
                VALUES (%s, %s, %s, %s)
            """, (blood_type, prep_id, safety_qty, alert_threshold))
    
    print(f"  ✓ 안전 재고 설정 {len(blood_types) * len(safety_configs)}건 생성")
    
    # blood_inventory 초기화 (모든 혈액형/제제 조합, 재고 0으로 시작)
    for blood_type in blood_types:
        for prep_id in range(1, 7):  # 1-6 (PRBC, Prefiltered, PC, SDP, FFP, Cryo)
            cursor.execute("""
                INSERT INTO blood_inventory (blood_type, prep_id, current_qty)
                VALUES (%s, %s, %s)
            """, (blood_type, prep_id, 0))
    
    print(f"  ✓ 재고 테이블 초기화 {len(blood_types) * 6}건 생성")
    
    connection.commit()
    print()
    
    # 4. 테이블 목록 확인
    print("📋 Step 4: 생성된 테이블 확인")
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    
    print(f"\n  생성된 테이블 목록 ({len(tables)}개):")
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
        count = cursor.fetchone()[0]
        print(f"    - {table[0]:20} : {count:4}건")
    
    print()
    print("=" * 80)
    print("✅ TiDB Cloud 데이터베이스 재구축 완료!")
    print("=" * 80)
    print()
    print("📊 요약:")
    print(f"  - 테이블: {len(tables)}개")
    print(f"  - 사용자: TEST001 (비밀번호: test123)")
    print(f"  - RBC 비율: 50% (5:5)")
    print(f"  - 혈액 제제: {len(blood_products)}종")
    print(f"  - 안전 재고 설정: {len(blood_types) * len(safety_configs)}건")
    print(f"  - 재고 초기화: {len(blood_types) * 6}건")
    print()
    
    cursor.close()
    
except Exception as e:
    print(f"\n❌ 오류 발생: {e}")
    import traceback
    traceback.print_exc()
    connection.rollback()
    
finally:
    connection.close()
