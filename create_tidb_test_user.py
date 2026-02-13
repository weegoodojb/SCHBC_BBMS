"""
TiDB Cloud에 TEST001 사용자 생성
"""
import pymysql
from passlib.context import CryptContext

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
    
    # TEST001 사용자 존재 확인
    cursor.execute("SELECT emp_id, name FROM users WHERE emp_id = 'TEST001'")
    existing_user = cursor.fetchone()
    
    if existing_user:
        print(f"✅ TEST001 사용자가 이미 존재합니다: {existing_user}")
    else:
        # 비밀번호 해싱
        password_hash = pwd_context.hash("test123")
        
        # 사용자 생성
        cursor.execute("""
            INSERT INTO users (emp_id, password_hash, name, email, created_at, updated_at)
            VALUES (%s, %s, %s, %s, NOW(), NOW())
        """, ('TEST001', password_hash, '테스트사용자', 'test001@schbc.ac.kr'))
        
        connection.commit()
        print("✅ TEST001 사용자가 생성되었습니다!")
        print("   사번: TEST001")
        print("   비밀번호: test123")
        print("   이름: 테스트사용자")
    
    # 생성된 사용자 확인
    cursor.execute("SELECT id, emp_id, name, email FROM users WHERE emp_id = 'TEST001'")
    user = cursor.fetchone()
    print(f"\n📊 사용자 정보:")
    print(f"   ID: {user[0]}")
    print(f"   사번: {user[1]}")
    print(f"   이름: {user[2]}")
    print(f"   이메일: {user[3]}")
    
    cursor.close()
    
except Exception as e:
    print(f"❌ 오류 발생: {e}")
    connection.rollback()
    
finally:
    connection.close()
