"""
Create test user for API testing
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import User
from core.security import hash_password

# Database setup
DB_FILE = 'bbms_local.db'
DATABASE_URL = f'sqlite:///{DB_FILE}'

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

try:
    # Check if test user already exists
    existing_user = session.query(User).filter(User.emp_id == 'TEST001').first()
    
    if existing_user:
        print("✓ Test user already exists")
        print(f"  - Employee ID: {existing_user.emp_id}")
        print(f"  - Name: {existing_user.name}")
        print(f"  - Email: {existing_user.email}")
    else:
        # Create test user
        test_user = User(
            emp_id='TEST001',
            name='테스트 사용자',
            password_hash=hash_password('password123'),
            email='test@schbc.ac.kr',
            remark='API 테스트용 사용자'
        )
        
        session.add(test_user)
        session.commit()
        session.refresh(test_user)
        
        print("✓ Test user created successfully")
        print(f"  - Employee ID: {test_user.emp_id}")
        print(f"  - Name: {test_user.name}")
        print(f"  - Email: {test_user.email}")
        print(f"  - Password: password123")
    
except Exception as e:
    print(f"✗ Error creating test user: {e}")
    session.rollback()
finally:
    session.close()
