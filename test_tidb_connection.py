"""
TiDB 연결 테스트 스크립트
"""
from sqlalchemy import create_engine, text
from app.core.config import settings

def test_tidb_connection():
    """TiDB 연결 테스트"""
    print("=" * 60)
    print("TiDB 연결 테스트")
    print("=" * 60)
    
    print(f"\n연결 정보:")
    print(f"- Host: gateway01.ap-northeast-1.prod.aws.tidbcloud.com")
    print(f"- Port: 4000")
    print(f"- User: 4Hv47XPrF3C3oHV.root")
    print(f"- Database: test")
    
    try:
        # 엔진 생성
        print("\n1. 데이터베이스 엔진 생성 중...")
        engine = create_engine(
            settings.DATABASE_URL,
            echo=True,
            pool_pre_ping=True  # 연결 유효성 검사
        )
        
        # 연결 테스트
        print("\n2. 데이터베이스 연결 테스트 중...")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT VERSION()"))
            version = result.fetchone()[0]
            print(f"✅ 연결 성공!")
            print(f"   TiDB 버전: {version}")
            
            # 현재 데이터베이스 확인
            result = conn.execute(text("SELECT DATABASE()"))
            current_db = result.fetchone()[0]
            print(f"   현재 데이터베이스: {current_db}")
            
            # 테이블 목록 확인
            result = conn.execute(text("SHOW TABLES"))
            tables = result.fetchall()
            print(f"\n3. 기존 테이블 목록:")
            if tables:
                for table in tables:
                    print(f"   - {table[0]}")
            else:
                print("   (테이블 없음)")
        
        print("\n" + "=" * 60)
        print("✅ TiDB 연결 테스트 성공!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ TiDB 연결 실패!")
        print("=" * 60)
        print(f"\n오류: {str(e)}")
        return False

if __name__ == "__main__":
    test_tidb_connection()
