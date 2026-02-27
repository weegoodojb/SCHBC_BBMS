import psycopg2
from app.core.security import hash_password

conn_params = dict(
    host='aws-1-ap-southeast-2.pooler.supabase.com',
    port=5432,
    database='postgres',
    user='postgres.gzqtyjwoasbbgelylkix',
    password='rkP4z7EfunMSIMXC',
    sslmode='require',
    connect_timeout=10
)

try:
    conn = psycopg2.connect(**conn_params)
    cur = conn.cursor()
    
    new_hash = hash_password('1234')
    
    cur.execute("SELECT id FROM users WHERE emp_id = '111'")
    row = cur.fetchone()
    if row:
        cur.execute("UPDATE users SET password_hash = %s WHERE emp_id = '111'", (new_hash,))
        print('Updated user 111 with new password hash')
    else:
        cur.execute(
            "INSERT INTO users (emp_id, name, password_hash, email, is_admin) VALUES (%s,%s,%s,%s,%s)",
            ('111', '111_user', new_hash, '111@schbc.ac.kr', 0)
        )
        print('Created user 111 with new password hash')
        
    conn.commit()
    print('Success')
except Exception as e:
    print(f'Error: {e}')
finally:
    if 'cur' in locals(): cur.close()
    if 'conn' in locals(): conn.close()
