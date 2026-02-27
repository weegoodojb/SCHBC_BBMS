"""
DB Diagnosis and Data Reset Script
- inbound_history 테이블 존재 여부 확인 및 없으면 생성
- inventory(재고수량), stock_log(실사로그), inbound_history(엑셀통계) 데이터 초기화
"""
import sys
import psycopg2

DB_URL = "postgresql://postgres.gzqtyjwoasbbgelylkix:rkP4z7EfunMSIMXC@aws-1-ap-southeast-2.pooler.supabase.com:5432/postgres"

# parse connection string
def get_conn():
    import re
    m = re.match(r'postgresql://(.+):(.+)@(.+):(\d+)/(.+)', DB_URL)
    user, password, host, port, dbname = m.group(1), m.group(2), m.group(3), m.group(4), m.group(5)
    return psycopg2.connect(host=host, port=int(port), dbname=dbname, user=user, password=password, connect_timeout=10)

def main():
    print("DB 연결 중...")
    try:
        conn = get_conn()
        conn.autocommit = False
        cur = conn.cursor()
        print("✅ DB 연결 성공!\n")

        # 1. 테이블 목록 확인
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name;")
        tables = [row[0] for row in cur.fetchall()]
        print(f"현재 존재하는 테이블 목록: {tables}\n")

        # 2. inbound_history 테이블 확인 및 생성
        if 'inbound_history' not in tables:
            print("⚠️ inbound_history 테이블이 없습니다! 생성합니다...")
            cur.execute("""
                CREATE TABLE inbound_history (
                    id SERIAL PRIMARY KEY,
                    receive_date DATE NOT NULL DEFAULT CURRENT_DATE,
                    blood_type VARCHAR(5) NOT NULL,
                    prep_id INTEGER NOT NULL REFERENCES blood_master(id),
                    qty INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT NOW()
                );
            """)
            conn.commit()
            print("✅ inbound_history 테이블 생성 완료!")
        else:
            print("✅ inbound_history 테이블 이미 존재함.")
            cur.execute("SELECT count(*) FROM inbound_history;")
            count = cur.fetchone()[0]
            print(f"   현재 행 수: {count}")

        # 3. 각 테이블 행 수 확인
        print("\n[현재 데이터 현황]")
        for table in ['inventory', 'stock_log', 'inbound_history']:
            if table in tables:
                cur.execute(f"SELECT count(*) FROM {table};")
                cnt = cur.fetchone()[0]
                print(f"  {table}: {cnt}개 행")

        # 4. 데이터 초기화 여부 물어보기
        print("\n🔴 [데이터 초기화 모드]")
        print("다음 테이블을 모두 초기화(전체 삭제)합니다:")
        print("  - inventory (재고 수량 → 모두 0으로 초기화)")
        print("  - stock_log (재고 실사 로그 삭제)")
        print("  - inbound_history (엑셀 업로드 통계 삭제)")
        confirm = input("\n정말 초기화하시겠습니까? (yes 입력 시 진행): ").strip().lower()
        if confirm == "yes":
            cur.execute("UPDATE inventory SET current_qty = 0;")
            cur.execute("DELETE FROM stock_log;")
            cur.execute("DELETE FROM inbound_history;")
            conn.commit()
            print("\n✅ 초기화 완료!")
            print("  - inventory: 수량 모두 0으로 초기화")
            print("  - stock_log: 모두 삭제")
            print("  - inbound_history: 모두 삭제")
        else:
            print("초기화를 취소했습니다.")

        cur.close()
        conn.close()
    except Exception as e:
        print(f"❌ 오류: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
