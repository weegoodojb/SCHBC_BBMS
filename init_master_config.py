"""
데이터베이스 초기화 스크립트 - master_config 테이블 추가
"""
from sqlalchemy import text
from app.database.database import engine
from app.database.models import Base, MasterConfig
from sqlalchemy.orm import Session

def init_master_config():
    """master_config 테이블 생성 및 초기 데이터 삽입"""
    print("\n" + "="*60)
    print("Master Config 테이블 초기화")
    print("="*60)
    
    # Create master_config table
    print("\n1. master_config 테이블 생성 중...")
    MasterConfig.__table__.create(engine, checkfirst=True)
    print("   ✓ 테이블 생성 완료")
    
    # Insert default RBC ratio
    print("\n2. 기본 RBC 비율 설정 삽입 중...")
    with Session(engine) as session:
        # Check if already exists
        existing = session.query(MasterConfig).filter(
            MasterConfig.config_key == 'rbc_ratio_percent'
        ).first()
        
        if existing:
            print(f"   ⚠ RBC 비율 설정이 이미 존재합니다: {existing.config_value}%")
        else:
            config = MasterConfig(
                config_key='rbc_ratio_percent',
                config_value='50',
                description='PRBC vs Prefiltered RBC ratio percentage (0-100)'
            )
            session.add(config)
            session.commit()
            print("   ✓ RBC 비율 50% 설정 완료")
    
    print("\n" + "="*60)
    print("✅ Master Config 초기화 완료!")
    print("="*60)

if __name__ == "__main__":
    init_master_config()
