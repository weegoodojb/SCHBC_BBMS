"""Simple test user creation script"""
import sys
sys.path.insert(0, 'app')

from database.models import User
from core.security import hash_password
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///bbms_local.db')
Session = sessionmaker(bind=engine)
session = Session()

try:
    existing = session.query(User).filter(User.emp_id == 'TEST001').first()
    
    if existing:
        print(f"✓ Test user already exists: {existing.emp_id} - {existing.name}")
    else:
        # Create with shorter password
        pwd_hash = hash_password('test123')
        user = User(
            emp_id='TEST001',
            name='Test User',
            password_hash=pwd_hash,
            email='test@test.com',
            remark='Test'
        )
        session.add(user)
        session.commit()
        print(f"✓ Test user created: TEST001 / test123")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    session.close()
