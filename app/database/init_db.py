"""
Database Initialization Script
Creates database schema and inserts seed data
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, BloodMaster, SafetyConfig, SystemSettings, Inventory, StockLog

# Database configuration
DB_FILE = 'bbms_local.db'
DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', DB_FILE)
DATABASE_URL = f'sqlite:///{DB_PATH}'


def create_database():
    """데이터베이스 파일 및 테이블 생성"""
    print(f"Creating database at: {DB_PATH}")
    
    # Create engine
    engine = create_engine(DATABASE_URL, echo=True)
    
    # Create all tables
    Base.metadata.create_all(engine)
    print("✓ All tables created successfully")
    
    return engine


def insert_seed_data(engine):
    """초기 데이터 삽입"""
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        print("\n=== Inserting seed data ===")
        
        # 1. BloodMaster 데이터 삽입
        print("\n1. Inserting BloodMaster data...")
        blood_masters = [
            # RBC 제제
            BloodMaster(component='RBC', preparation='PRBC', remark='농축적혈구'),
            BloodMaster(component='RBC', preparation='Prefiltered', remark='백혈구여과제거 적혈구'),
            
            # PLT 제제
            BloodMaster(component='PLT', preparation='PC', remark='농축혈소판'),
            BloodMaster(component='PLT', preparation='SDP', remark='성분채집혈소판'),
            
            # FFP 제제
            BloodMaster(component='FFP', preparation='FFP', remark='신선동결혈장'),
            
            # Cryo 제제
            BloodMaster(component='Cryo', preparation='Cryo', remark='동결침전제제'),
        ]
        
        session.add_all(blood_masters)
        session.commit()
        print(f"✓ Inserted {len(blood_masters)} blood master records")
        
        # 2. SystemSettings 데이터 삽입
        print("\n2. Inserting SystemSettings data...")
        system_settings = [
            SystemSettings(
                key='RBC_RATIO',
                value='0.5',
                description='RBC 제제 비율 (PRBC:Prefiltered)',
                remark='기본값 0.5 (50%)'
            ),
            SystemSettings(
                key='PLT_RATIO',
                value='0.7',
                description='PLT 제제 비율 (PC:SDP)',
                remark='기본값 0.7 (70%)'
            ),
            SystemSettings(
                key='ALERT_ENABLED',
                value='true',
                description='재고 알람 활성화 여부',
                remark='true/false'
            ),
            SystemSettings(
                key='SYSTEM_NAME',
                value='SCHBC BBMS',
                description='시스템 명칭',
                remark='순천향대학교 부천병원 혈액관리시스템'
            ),
        ]
        
        session.add_all(system_settings)
        session.commit()
        print(f"✓ Inserted {len(system_settings)} system settings")
        
        # 3. 초기 재고 데이터 삽입 (선택사항 - 모든 혈액형/제제 조합에 대해 0으로 초기화)
        print("\n3. Initializing inventory records...")
        blood_types = ['A', 'B', 'O', 'AB']
        
        # Get all blood master IDs
        blood_master_records = session.query(BloodMaster).all()
        
        inventory_records = []
        for blood_type in blood_types:
            for bm in blood_master_records:
                inventory_records.append(
                    Inventory(
                        blood_type=blood_type,
                        prep_id=bm.id,
                        current_qty=0,
                        remark=f'초기 재고 - {blood_type}형 {bm.preparation}'
                    )
                )
        
        session.add_all(inventory_records)
        session.commit()
        print(f"✓ Initialized {len(inventory_records)} inventory records")
        
        # 4. 안전재고 기본값 설정 (선택사항)
        print("\n4. Setting default safety configurations...")
        safety_configs = []
        
        # 기본 안전재고 설정값 (예시)
        default_safety = {
            'PRBC': {'safety': 10, 'alert': 5},
            'Prefiltered': {'safety': 8, 'alert': 4},
            'PC': {'safety': 15, 'alert': 7},
            'SDP': {'safety': 10, 'alert': 5},
            'FFP': {'safety': 12, 'alert': 6},
            'Cryo': {'safety': 8, 'alert': 4},
        }
        
        for blood_type in blood_types:
            for bm in blood_master_records:
                if bm.preparation in default_safety:
                    config = default_safety[bm.preparation]
                    safety_configs.append(
                        SafetyConfig(
                            blood_type=blood_type,
                            prep_id=bm.id,
                            safety_qty=config['safety'],
                            alert_threshold=config['alert'],
                            remark=f'기본 설정 - {blood_type}형 {bm.preparation}'
                        )
                    )
        
        session.add_all(safety_configs)
        session.commit()
        print(f"✓ Inserted {len(safety_configs)} safety configuration records")
        
        print("\n=== Seed data insertion completed successfully ===")
        
    except Exception as e:
        print(f"\n✗ Error inserting seed data: {e}")
        session.rollback()
        raise
    finally:
        session.close()


def verify_database(engine):
    """데이터베이스 검증"""
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        print("\n=== Verifying database ===")
        
        # Count records in each table
        tables = [
            ('Users', User),
            ('BloodMaster', BloodMaster),
            ('SafetyConfig', SafetyConfig),
            ('SystemSettings', SystemSettings),
            ('Inventory', Inventory),
            ('StockLog', StockLog),
        ]
        
        for table_name, model in tables:
            count = session.query(model).count()
            print(f"{table_name}: {count} records")
        
        # Display some sample data
        print("\n--- Sample BloodMaster records ---")
        blood_masters = session.query(BloodMaster).all()
        for bm in blood_masters:
            print(f"  ID={bm.id}: {bm.component} - {bm.preparation}")
        
        print("\n--- Sample SystemSettings ---")
        settings = session.query(SystemSettings).all()
        for setting in settings:
            print(f"  {setting.key} = {setting.value}")
        
        print("\n✓ Database verification completed")
        
    except Exception as e:
        print(f"\n✗ Error verifying database: {e}")
        raise
    finally:
        session.close()


def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("SCHBC BBMS Database Initialization")
    print("=" * 60)
    
    # Check if database already exists
    if os.path.exists(DB_PATH):
        response = input(f"\nDatabase file '{DB_FILE}' already exists. Overwrite? (yes/no): ")
        if response.lower() != 'yes':
            print("Initialization cancelled.")
            return
        else:
            os.remove(DB_PATH)
            print(f"✓ Removed existing database file")
    
    # Create database and tables
    engine = create_database()
    
    # Insert seed data
    insert_seed_data(engine)
    
    # Verify database
    verify_database(engine)
    
    print("\n" + "=" * 60)
    print("Database initialization completed successfully!")
    print(f"Database location: {DB_PATH}")
    print("=" * 60)


if __name__ == '__main__':
    main()
