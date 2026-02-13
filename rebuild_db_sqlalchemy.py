"""
SQLAlchemy를 사용한 TiDB Cloud 데이터베이스 재구축
"""
from app.database.database import engine, SessionLocal, Base
from app.database.models import User, MasterConfig, BloodMaster, SafetyConfig, Inventory, StockLog
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

print("=" * 80)
print("TiDB Cloud 데이터베이스 재구축 (SQLAlchemy)")
print("=" * 80)
print()

try:
    # 1. 모든 테이블 삭제 후 재생성
    print("📋 Step 1: 테이블 생성")
    Base.metadata.drop_all(bind=engine)
    print("  ✓ 기존 테이블 삭제 완료")
    
    Base.metadata.create_all(bind=engine)
    print("  ✓ 새 테이블 생성 완료")
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
        print("  ✓ TEST001 사용자 생성")
        
        # RBC 비율 설정
        rbc_config = MasterConfig(
            config_key='rbc_ratio_percent',
            config_value='50',
            description='PRBC vs Prefiltered RBC ratio percentage'
        )
        db.add(rbc_config)
        print("  ✓ RBC 비율 설정 (50%)")
        
        # blood_master 데이터
        blood_products = [
            BloodMaster(component='RBC', preparation='PRBC', volume=320),
            BloodMaster(component='RBC', preparation='Prefiltered', volume=320),
            BloodMaster(component='PLT', preparation='PC', volume=200),
            BloodMaster(component='PLT', preparation='SDP', volume=200),
            BloodMaster(component='FFP', preparation='FFP', volume=250),
            BloodMaster(component='Cryo', preparation='Cryo', volume=50)
        ]
        
        for product in blood_products:
            db.add(product)
        
        db.commit()
        print(f"  ✓ 혈액 제제 마스터 {len(blood_products)}건 생성")
        
        # safety_config 데이터
        blood_types = ['A', 'B', 'O', 'AB']
        safety_configs_data = [
            (1, 20, 10),  # PRBC
            (2, 20, 10),  # Prefiltered
            (3, 10, 5),   # PC
            (4, 10, 5),   # SDP
            (5, 15, 8),   # FFP
            (6, 5, 3)     # Cryo
        ]
        
        for blood_type in blood_types:
            for prep_id, safety_qty, alert_threshold in safety_configs_data:
                config = SafetyConfig(
                    blood_type=blood_type,
                    prep_id=prep_id,
                    safety_qty=safety_qty,
                    alert_threshold=alert_threshold
                )
                db.add(config)
        
        db.commit()
        print(f"  ✓ 안전 재고 설정 {len(blood_types) * len(safety_configs_data)}건 생성")
        
        # blood_inventory 초기화
        for blood_type in blood_types:
            for prep_id in range(1, 7):
                inventory = Inventory(
                    blood_type=blood_type,
                    prep_id=prep_id,
                    current_qty=0
                )
                db.add(inventory)
        
        db.commit()
        print(f"  ✓ 재고 테이블 초기화 {len(blood_types) * 6}건 생성")
        print()
        
        # 3. 데이터 확인
        print("📋 Step 3: 데이터 확인")
        user_count = db.query(User).count()
        config_count = db.query(MasterConfig).count()
        master_count = db.query(BloodMaster).count()
        safety_count = db.query(SafetyConfig).count()
        inventory_count = db.query(Inventory).count()
        
        print(f"  - users: {user_count}건")
        print(f"  - master_config: {config_count}건")
        print(f"  - blood_master: {master_count}건")
        print(f"  - safety_config: {safety_count}건")
        print(f"  - blood_inventory: {inventory_count}건")
        print()
        
        print("=" * 80)
        print("✅ TiDB Cloud 데이터베이스 재구축 완료!")
        print("=" * 80)
        print()
        print("📊 로그인 정보:")
        print("  사번: TEST001")
        print("  비밀번호: test123")
        print("  이름: 테스트사용자")
        print()
        
    except Exception as e:
        print(f"\n❌ 데이터 주입 오류: {e}")
        db.rollback()
        raise
    finally:
        db.close()
        
except Exception as e:
    print(f"\n❌ 오류 발생: {e}")
    import traceback
    traceback.print_exc()
