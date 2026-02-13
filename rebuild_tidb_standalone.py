"""
독립 실행형 TiDB 데이터베이스 재구축 스크립트
"""
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from passlib.context import CryptContext

# DATABASE_URL
DATABASE_URL = "mysql+pymysql://4Hv47XPrF3C3oHV.root:qcu4ldWPyNVjiMxm@gateway01.ap-northeast-1.prod.aws.tidbcloud.com:4000/test?ssl_ca=&ssl_verify_cert=true&ssl_verify_identity=true"

# SQLAlchemy 설정
Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 모델 정의
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    emp_id = Column(String(20), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(50), nullable=False)
    email = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class MasterConfig(Base):
    __tablename__ = "master_config"
    id = Column(Integer, primary_key=True, autoincrement=True)
    config_key = Column(String(50), unique=True, nullable=False)
    config_value = Column(String(255), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class BloodMaster(Base):
    __tablename__ = "blood_master"
    id = Column(Integer, primary_key=True, autoincrement=True)
    component = Column(String(20), nullable=False)
    preparation = Column(String(50), nullable=False)
    volume = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SafetyConfig(Base):
    __tablename__ = "safety_config"
    id = Column(Integer, primary_key=True, autoincrement=True)
    blood_type = Column(String(5), nullable=False)
    prep_id = Column(Integer, ForeignKey('blood_master.id'), nullable=False)
    safety_qty = Column(Integer, nullable=False, default=0)
    alert_threshold = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Inventory(Base):
    __tablename__ = "blood_inventory"
    id = Column(Integer, primary_key=True, autoincrement=True)
    blood_type = Column(String(5), nullable=False)
    prep_id = Column(Integer, ForeignKey('blood_master.id'), nullable=False)
    current_qty = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class StockLog(Base):
    __tablename__ = "stock_log"
    id = Column(Integer, primary_key=True, autoincrement=True)
    blood_type = Column(String(5), nullable=False)
    prep_id = Column(Integer, ForeignKey('blood_master.id'), nullable=False)
    in_qty = Column(Integer, nullable=False, default=0)
    out_qty = Column(Integer, nullable=False, default=0)
    remark = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

print("=" * 80)
print("TiDB Cloud 데이터베이스 재구축")
print("=" * 80)
print()

try:
    # 1. 테이블 생성
    print("📋 Step 1: 테이블 생성")
    Base.metadata.drop_all(bind=engine)
    print("  ✓ 기존 테이블 삭제")
    
    Base.metadata.create_all(bind=engine)
    print("  ✓ 새 테이블 생성 (6개)")
    print()
    
    # 2. 초기 데이터 주입
    print("📋 Step 2: 초기 데이터 주입")
    db = SessionLocal()
    
    try:
        # TEST001 사용자
        user = User(
            emp_id='TEST001',
            password_hash=pwd_context.hash('test123'),
            name='테스트사용자',
            email='test001@schbc.ac.kr'
        )
        db.add(user)
        print("  ✓ TEST001 사용자")
        
        # RBC 비율
        rbc_config = MasterConfig(
            config_key='rbc_ratio_percent',
            config_value='50',
            description='PRBC vs Prefiltered RBC ratio percentage'
        )
        db.add(rbc_config)
        print("  ✓ RBC 비율 (50%)")
        
        # blood_master
        products = [
            BloodMaster(component='RBC', preparation='PRBC', volume=320),
            BloodMaster(component='RBC', preparation='Prefiltered', volume=320),
            BloodMaster(component='PLT', preparation='PC', volume=200),
            BloodMaster(component='PLT', preparation='SDP', volume=200),
            BloodMaster(component='FFP', preparation='FFP', volume=250),
            BloodMaster(component='Cryo', preparation='Cryo', volume=50)
        ]
        for p in products:
            db.add(p)
        
        db.commit()
        print(f"  ✓ 혈액 제제 마스터 (6건)")
        
        # safety_config
        blood_types = ['A', 'B', 'O', 'AB']
        configs = [(1,20,10), (2,20,10), (3,10,5), (4,10,5), (5,15,8), (6,5,3)]
        
        for bt in blood_types:
            for pid, sq, at in configs:
                db.add(SafetyConfig(blood_type=bt, prep_id=pid, safety_qty=sq, alert_threshold=at))
        
        db.commit()
        print(f"  ✓ 안전 재고 설정 (24건)")
        
        # blood_inventory
        for bt in blood_types:
            for pid in range(1, 7):
                db.add(Inventory(blood_type=bt, prep_id=pid, current_qty=0))
        
        db.commit()
        print(f"  ✓ 재고 초기화 (24건)")
        print()
        
        # 3. 확인
        print("📋 Step 3: 데이터 확인")
        print(f"  - users: {db.query(User).count()}건")
        print(f"  - master_config: {db.query(MasterConfig).count()}건")
        print(f"  - blood_master: {db.query(BloodMaster).count()}건")
        print(f"  - safety_config: {db.query(SafetyConfig).count()}건")
        print(f"  - blood_inventory: {db.query(Inventory).count()}건")
        print()
        
        print("=" * 80)
        print("✅ 데이터베이스 재구축 완료!")
        print("=" * 80)
        print()
        print("📊 로그인 정보:")
        print("  사번: TEST001")
        print("  비밀번호: test123")
        print()
        
    finally:
        db.close()
        
except Exception as e:
    print(f"\n❌ 오류: {e}")
    import traceback
    traceback.print_exc()
