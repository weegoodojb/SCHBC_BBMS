"""
Supabase PostgreSQL 테이블 생성 (psycopg2 직접 사용)
"""
import psycopg2
from passlib.context import CryptContext

# Supabase 연결 정보
conn_params = {
    'host': 'aws-1-ap-southeast-2.pooler.supabase.com',
    'port': 5432,
    'database': 'postgres',
    'user': 'postgres.gzqtyjwoasbbgelylkix',
    'password': 'rkP4z7EfunMSIMXC'
}

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

print("=" * 80)
print("Supabase PostgreSQL 테이블 생성")
print("=" * 80)
print()

try:
    conn = psycopg2.connect(**conn_params)
    cursor = conn.cursor()
    
    # 1. 기존 테이블 삭제
    print("📋 Step 1: 기존 테이블 정리")
    tables = ['stock_log', 'blood_inventory', 'safety_config', 'blood_master', 'master_config', 'users']
    for table in tables:
        cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
        print(f"  ✓ {table} 삭제")
    conn.commit()
    print()
    
    # 2. 테이블 생성
    print("📋 Step 2: 테이블 생성")
    
    cursor.execute("""
        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            emp_id VARCHAR(20) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            name VARCHAR(50) NOT NULL,
            email VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("  ✓ users")
    
    cursor.execute("""
        CREATE TABLE master_config (
            id SERIAL PRIMARY KEY,
            config_key VARCHAR(50) UNIQUE NOT NULL,
            config_value VARCHAR(255) NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("  ✓ master_config")
    
    cursor.execute("""
        CREATE TABLE blood_master (
            id SERIAL PRIMARY KEY,
            component VARCHAR(20) NOT NULL,
            preparation VARCHAR(50) NOT NULL,
            volume INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (component, preparation)
        )
    """)
    print("  ✓ blood_master")
    
    cursor.execute("""
        CREATE TABLE safety_config (
            id SERIAL PRIMARY KEY,
            blood_type VARCHAR(5) NOT NULL,
            prep_id INTEGER NOT NULL REFERENCES blood_master(id),
            safety_qty INTEGER NOT NULL DEFAULT 0,
            alert_threshold INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (blood_type, prep_id)
        )
    """)
    print("  ✓ safety_config")
    
    cursor.execute("""
        CREATE TABLE blood_inventory (
            id SERIAL PRIMARY KEY,
            blood_type VARCHAR(5) NOT NULL,
            prep_id INTEGER NOT NULL REFERENCES blood_master(id),
            current_qty INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (blood_type, prep_id)
        )
    """)
    print("  ✓ blood_inventory")
    
    cursor.execute("""
        CREATE TABLE stock_log (
            id SERIAL PRIMARY KEY,
            blood_type VARCHAR(5) NOT NULL,
            prep_id INTEGER NOT NULL REFERENCES blood_master(id),
            in_qty INTEGER NOT NULL DEFAULT 0,
            out_qty INTEGER NOT NULL DEFAULT 0,
            remark TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("  ✓ stock_log")
    
    conn.commit()
    print()
    
    # 3. 초기 데이터
    print("📋 Step 3: 초기 데이터 주입")
    
    # TEST001
    password_hash = pwd_context.hash("test123")
    cursor.execute(
        "INSERT INTO users (emp_id, password_hash, name, email) VALUES (%s, %s, %s, %s)",
        ("TEST001", password_hash, "테스트사용자", "test001@schbc.ac.kr")
    )
    print("  ✓ TEST001 사용자")
    
    # RBC 비율
    cursor.execute(
        "INSERT INTO master_config (config_key, config_value, description) VALUES (%s, %s, %s)",
        ("rbc_ratio_percent", "50", "PRBC vs Prefiltered RBC ratio percentage")
    )
    print("  ✓ RBC 비율 (50%)")
    
    # blood_master
    products = [
        ('RBC', 'PRBC', 320),
        ('RBC', 'Prefiltered', 320),
        ('PLT', 'PC', 200),
        ('PLT', 'SDP', 200),
        ('FFP', 'FFP', 250),
        ('Cryo', 'Cryo', 50)
    ]
    for component, preparation, volume in products:
        cursor.execute(
            "INSERT INTO blood_master (component, preparation, volume) VALUES (%s, %s, %s)",
            (component, preparation, volume)
        )
    print(f"  ✓ 혈액 제제 마스터 ({len(products)}건)")
    
    # safety_config
    blood_types = ['A', 'B', 'O', 'AB']
    configs = [(1,20,10), (2,20,10), (3,10,5), (4,10,5), (5,15,8), (6,5,3)]
    
    for bt in blood_types:
        for pid, sq, at in configs:
            cursor.execute(
                "INSERT INTO safety_config (blood_type, prep_id, safety_qty, alert_threshold) VALUES (%s, %s, %s, %s)",
                (bt, pid, sq, at)
            )
    print(f"  ✓ 안전 재고 설정 ({len(blood_types) * len(configs)}건)")
    
    # blood_inventory
    for bt in blood_types:
        for pid in range(1, 7):
            cursor.execute(
                "INSERT INTO blood_inventory (blood_type, prep_id, current_qty) VALUES (%s, %s, %s)",
                (bt, pid, 0)
            )
    print(f"  ✓ 재고 초기화 ({len(blood_types) * 6}건)")
    
    conn.commit()
    print()
    
    # 4. 확인
    print("📋 Step 4: 데이터 확인")
    cursor.execute("SELECT COUNT(*) FROM users")
    print(f"  - users: {cursor.fetchone()[0]}건")
    
    cursor.execute("SELECT COUNT(*) FROM master_config")
    print(f"  - master_config: {cursor.fetchone()[0]}건")
    
    cursor.execute("SELECT COUNT(*) FROM blood_master")
    print(f"  - blood_master: {cursor.fetchone()[0]}건")
    
    cursor.execute("SELECT COUNT(*) FROM safety_config")
    print(f"  - safety_config: {cursor.fetchone()[0]}건")
    
    cursor.execute("SELECT COUNT(*) FROM blood_inventory")
    print(f"  - blood_inventory: {cursor.fetchone()[0]}건")
    
    print()
    print("=" * 80)
    print("✅ Supabase PostgreSQL 데이터베이스 구축 완료!")
    print("=" * 80)
    print()
    print("📊 로그인 정보:")
    print("  사번: TEST001")
    print("  비밀번호: test123")
    print()
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"\n❌ 오류 발생: {e}")
    import traceback
    traceback.print_exc()
