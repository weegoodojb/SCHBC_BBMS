"""
Supabase PostgreSQL 테이블 생성 및 초기 데이터 주입 (psycopg2 직접 사용)
"""
import psycopg2
from passlib.context import CryptContext

# ── 연결 정보 ──────────────────────────────────────────────────────────────
HOST = 'aws-1-ap-southeast-2.pooler.supabase.com'
PORT = 5432
DATABASE = 'postgres'
USER = 'postgres.gzqtyjwoasbbgelylkix'
PASSWORD = 'rkP4z7EfunMSIMXC'

conn_params = dict(host=HOST, port=PORT, database=DATABASE, user=USER,
                   password=PASSWORD, sslmode='require', connect_timeout=10)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

print("=" * 70)
print("  Supabase PostgreSQL 테이블 생성")
print("=" * 70)

# ── 연결 테스트 ─────────────────────────────────────────────────────────────
print("\n[STEP 0] 연결 테스트 (SELECT 1)")
try:
    conn = psycopg2.connect(**conn_params)
    cur = conn.cursor()
    cur.execute("SELECT 1")
    assert cur.fetchone()[0] == 1
    print("  ✅ SELECT 1 → 성공! Supabase 연결 확인")
    cur.close()
    conn.close()
except Exception as e:
    print(f"  ❌ 연결 실패: {e}")
    exit(1)

# ── 본 작업 ─────────────────────────────────────────────────────────────────
conn = psycopg2.connect(**conn_params)
cur = conn.cursor()

try:
    # STEP 1: 기존 테이블 정리
    print("\n[STEP 1] 기존 테이블 정리")
    drop_order = [
        'inventory_ratio_history', 'stock_log', 'inventory',
        'safety_config', 'master_config', 'blood_master', 'system_settings', 'users'
    ]
    for tbl in drop_order:
        cur.execute(f"DROP TABLE IF EXISTS {tbl} CASCADE")
        print(f"  ✓ DROP {tbl}")
    conn.commit()

    # STEP 2: 테이블 생성
    print("\n[STEP 2] 테이블 생성")

    cur.execute("""
    CREATE TABLE users (
        id SERIAL PRIMARY KEY,
        emp_id VARCHAR(50) UNIQUE NOT NULL,
        name VARCHAR(100) NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        email VARCHAR(100),
        is_admin INTEGER DEFAULT 0,
        remark TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    print("  ✓ users")

    cur.execute("""
    CREATE TABLE blood_master (
        id SERIAL PRIMARY KEY,
        component VARCHAR(20) NOT NULL,
        preparation VARCHAR(50) NOT NULL,
        remark TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (component, preparation)
    )""")
    print("  ✓ blood_master")

    cur.execute("""
    CREATE TABLE master_config (
        id SERIAL PRIMARY KEY,
        blood_type VARCHAR(5),
        prep_id INTEGER REFERENCES blood_master(id),
        config_key VARCHAR(50) NOT NULL,
        config_value VARCHAR(255) NOT NULL,
        daily_consumption_rate NUMERIC(5,1),
        safety_factor NUMERIC(5,2),
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (blood_type, prep_id, config_key)
    )""")
    print("  ✓ master_config (blood_type/prep_id별 행)")

    cur.execute("""
    CREATE TABLE inventory_ratio_history (
        id SERIAL PRIMARY KEY,
        blood_type VARCHAR(5),
        prep_id INTEGER REFERENCES blood_master(id),
        config_key VARCHAR(50) NOT NULL,
        old_factor NUMERIC(5,2),
        new_factor NUMERIC(5,2) NOT NULL,
        change_reason TEXT NOT NULL,
        changed_by VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    print("  ✓ inventory_ratio_history")

    cur.execute("""
    CREATE TABLE safety_config (
        id SERIAL PRIMARY KEY,
        blood_type VARCHAR(5) NOT NULL,
        prep_id INTEGER NOT NULL REFERENCES blood_master(id),
        safety_qty INTEGER NOT NULL DEFAULT 0,
        alert_threshold INTEGER NOT NULL DEFAULT 0,
        remark TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (blood_type, prep_id)
    )""")
    print("  ✓ safety_config")

    cur.execute("""
    CREATE TABLE inventory (
        id SERIAL PRIMARY KEY,
        blood_type VARCHAR(5) NOT NULL,
        prep_id INTEGER NOT NULL REFERENCES blood_master(id),
        current_qty INTEGER NOT NULL DEFAULT 0,
        remark TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (blood_type, prep_id)
    )""")
    print("  ✓ inventory")

    cur.execute("""
    CREATE TABLE stock_log (
        id SERIAL PRIMARY KEY,
        log_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        blood_type VARCHAR(5) NOT NULL,
        prep_id INTEGER NOT NULL REFERENCES blood_master(id),
        in_qty INTEGER NOT NULL DEFAULT 0,
        out_qty INTEGER NOT NULL DEFAULT 0,
        remark TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    print("  ✓ stock_log")

    cur.execute("""
    CREATE TABLE system_settings (
        key VARCHAR(100) PRIMARY KEY,
        value VARCHAR(255) NOT NULL,
        description TEXT,
        remark TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    print("  ✓ system_settings")

    conn.commit()

    # STEP 3: 초기 데이터
    print("\n[STEP 3] 초기 데이터 주입")

    # TEST001 사용자
    ph = pwd_context.hash("test123")
    cur.execute(
        "INSERT INTO users (emp_id, name, password_hash, email, is_admin) VALUES (%s,%s,%s,%s,%s)",
        ("TEST001", "테스트사용자", ph, "test001@schbc.ac.kr", 0)
    )
    cur.execute(
        "INSERT INTO users (emp_id, name, password_hash, email, is_admin) VALUES (%s,%s,%s,%s,%s)",
        ("ADMIN001", "관리자", pwd_context.hash("admin123"), "admin@schbc.ac.kr", 1)
    )
    print("  ✓ 사용자 2명 (TEST001, ADMIN001)")

    # blood_master
    products = [
        ('RBC', 'PRBC'), ('RBC', 'Prefiltered'),
        ('PLT', 'PC'), ('PLT', 'SDP'),
        ('FFP', 'FFP'), ('Cryo', 'Cryo')
    ]
    for comp, prep in products:
        cur.execute("INSERT INTO blood_master (component, preparation) VALUES (%s,%s)", (comp, prep))
    conn.commit()
    print(f"  ✓ blood_master {len(products)}건")

    # blood_master id 조회
    cur.execute("SELECT id, component, preparation FROM blood_master ORDER BY id")
    bm_rows = cur.fetchall()
    bm_map = {(row[1], row[2]): row[0] for row in bm_rows}

    # master_config: 공통 기본값 (blood_type=NULL, prep_id=NULL)
    cur.execute("""
        INSERT INTO master_config (blood_type, prep_id, config_key, config_value, daily_consumption_rate, safety_factor, description)
        VALUES (NULL, NULL, 'rbc_factors', 'dcr=3.0,sf=2.0', 3.0, 2.0, '공통 RBC 재고비 기본값')
    """)
    cur.execute("""
        INSERT INTO master_config (blood_type, prep_id, config_key, config_value, description)
        VALUES (NULL, NULL, 'rbc_ratio_percent', '50', 'PRBC vs Prefiltered 비율(%)')
    """)
    print("  ✓ master_config 공통 기본값 (DCR=3.0, SF=2.0, 비율=50%)")

    # safety_config + inventory
    blood_types = ['A', 'B', 'O', 'AB']
    safety_map = {
        ('RBC', 'PRBC'): (20, 10),
        ('RBC', 'Prefiltered'): (20, 10),
        ('PLT', 'PC'): (10, 5),
        ('PLT', 'SDP'): (10, 5),
        ('FFP', 'FFP'): (15, 8),
        ('Cryo', 'Cryo'): (5, 3),
    }
    for bt in blood_types:
        for (comp, prep), (safety, alert) in safety_map.items():
            pid = bm_map[(comp, prep)]
            cur.execute(
                "INSERT INTO safety_config (blood_type, prep_id, safety_qty, alert_threshold) VALUES (%s,%s,%s,%s)",
                (bt, pid, safety, alert)
            )
            cur.execute(
                "INSERT INTO inventory (blood_type, prep_id, current_qty) VALUES (%s,%s,%s)",
                (bt, pid, 0)
            )
    conn.commit()
    print(f"  ✓ safety_config + inventory 각 {len(blood_types)*6}건")

    # STEP 4: 검증
    print("\n[STEP 4] 데이터 검증")
    for tbl in ['users','blood_master','master_config','inventory_ratio_history',
                'safety_config','inventory','stock_log']:
        cur.execute(f"SELECT COUNT(*) FROM {tbl}")
        print(f"  - {tbl:<28}: {cur.fetchone()[0]:>3}건")

    print("\n" + "=" * 70)
    print("  ✅ Supabase 연결 및 테이블 생성 완료!")
    print("  📊 로그인: TEST001 / test123  |  관리자: ADMIN001 / admin123")
    print("=" * 70)

except Exception as e:
    conn.rollback()
    print(f"\n  ❌ 오류: {e}")
    import traceback
    traceback.print_exc()
finally:
    cur.close()
    conn.close()
