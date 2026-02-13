"""
TiDB Cloud 테이블 목록 확인
"""
import pymysql

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
    
    print("=" * 60)
    print("TiDB Cloud 테이블 확인")
    print("=" * 60)
    
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    
    if tables:
        print(f"\n✅ 테이블 목록 ({len(tables)}개):\n")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cursor.fetchone()[0]
            print(f"  {table[0]:20} : {count:4}건")
    else:
        print("\n⚠️ 테이블이 없습니다 (empty set)")
    
    print("\n" + "=" * 60)
    
    cursor.close()
    
except Exception as e:
    print(f"❌ 오류: {e}")
    
finally:
    connection.close()
