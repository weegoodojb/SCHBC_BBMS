"""
Database Models for SCHBC BBMS
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

# ==================== Configuration ====================

class MasterConfig(Base):
    """마스터 설정 테이블 - RBC 비율 등 시스템 설정"""
    __tablename__ = 'master_config'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    config_key = Column(String(50), unique=True, nullable=False, comment='설정 키')
    config_value = Column(String(255), nullable=False, comment='설정 값')
    description = Column(Text, comment='설명')
    created_at = Column(DateTime, default=datetime.now, comment='생성일시')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='수정일시')
    
    def __repr__(self):
        return f"<MasterConfig(key='{self.config_key}', value='{self.config_value}')>"


class User(Base):
    """사용자 정보 테이블"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    emp_id = Column(String(50), unique=True, nullable=False, comment='직원번호')
    name = Column(String(100), nullable=False, comment='이름')
    password_hash = Column(String(255), nullable=False, comment='비밀번호 해시')
    email = Column(String(100), comment='이메일')
    remark = Column(Text, comment='비고')
    created_at = Column(DateTime, default=datetime.now, comment='생성일시')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='수정일시')
    
    def __repr__(self):
        return f"<User(emp_id='{self.emp_id}', name='{self.name}')>"


class BloodMaster(Base):
    """혈액제제 마스터 테이블"""
    __tablename__ = 'blood_master'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    component = Column(String(20), nullable=False, comment='혈액성분 (RBC, PLT, FFP, Cryo)')
    preparation = Column(String(50), nullable=False, comment='제제명 (PRBC, Prefiltered, PC, SDP, FFP, Cryo)')
    remark = Column(Text, comment='비고')
    created_at = Column(DateTime, default=datetime.now, comment='생성일시')
    
    # Relationships
    safety_configs = relationship('SafetyConfig', back_populates='blood_prep')
    inventories = relationship('Inventory', back_populates='blood_prep')
    stock_logs = relationship('StockLog', back_populates='blood_prep')
    
    def __repr__(self):
        return f"<BloodMaster(component='{self.component}', preparation='{self.preparation}')>"


class SafetyConfig(Base):
    """적정재고 및 알람기준 설정 테이블"""
    __tablename__ = 'safety_config'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    blood_type = Column(String(5), nullable=False, comment='혈액형 (A, B, O, AB)')
    prep_id = Column(Integer, ForeignKey('blood_master.id'), nullable=False, comment='제제 ID')
    safety_qty = Column(Integer, nullable=False, default=0, comment='적정재고량')
    alert_threshold = Column(Integer, nullable=False, default=0, comment='알람기준량')
    remark = Column(Text, comment='비고')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='수정일시')
    
    # Relationships
    blood_prep = relationship('BloodMaster', back_populates='safety_configs')
    
    # Unique constraint: one config per blood_type + prep_id combination
    __table_args__ = (
        UniqueConstraint('blood_type', 'prep_id', name='uix_blood_type_prep'),
    )
    
    def __repr__(self):
        return f"<SafetyConfig(blood_type='{self.blood_type}', prep_id={self.prep_id}, safety={self.safety_qty}, alert={self.alert_threshold})>"


class SystemSettings(Base):
    """시스템 설정 테이블 (Key-Value 저장소)"""
    __tablename__ = 'system_settings'
    
    key = Column(String(100), primary_key=True, comment='설정 키')
    value = Column(String(255), nullable=False, comment='설정 값')
    description = Column(Text, comment='설정 설명')
    remark = Column(Text, comment='비고')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='수정일시')
    
    def __repr__(self):
        return f"<SystemSettings(key='{self.key}', value='{self.value}')>"


class Inventory(Base):
    """현재 재고 테이블"""
    __tablename__ = 'inventory'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    blood_type = Column(String(5), nullable=False, comment='혈액형 (A, B, O, AB)')
    prep_id = Column(Integer, ForeignKey('blood_master.id'), nullable=False, comment='제제 ID')
    current_qty = Column(Integer, nullable=False, default=0, comment='현재재고량')
    remark = Column(Text, comment='비고')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='수정일시')
    
    # Relationships
    blood_prep = relationship('BloodMaster', back_populates='inventories')
    
    # Unique constraint: one inventory record per blood_type + prep_id combination
    __table_args__ = (
        UniqueConstraint('blood_type', 'prep_id', name='uix_inventory_blood_type_prep'),
    )
    
    def __repr__(self):
        return f"<Inventory(blood_type='{self.blood_type}', prep_id={self.prep_id}, qty={self.current_qty})>"


class StockLog(Base):
    """입출고 로그 테이블"""
    __tablename__ = 'stock_log'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    log_date = Column(DateTime, nullable=False, default=datetime.now, comment='로그일시')
    blood_type = Column(String(5), nullable=False, comment='혈액형 (A, B, O, AB)')
    prep_id = Column(Integer, ForeignKey('blood_master.id'), nullable=False, comment='제제 ID')
    in_qty = Column(Integer, nullable=False, default=0, comment='입고량')
    out_qty = Column(Integer, nullable=False, default=0, comment='출고량')
    remark = Column(Text, comment='비고')
    created_at = Column(DateTime, default=datetime.now, comment='생성일시')
    
    # Relationships
    blood_prep = relationship('BloodMaster', back_populates='stock_logs')
    
    def __repr__(self):
        return f"<StockLog(date='{self.log_date}', blood_type='{self.blood_type}', in={self.in_qty}, out={self.out_qty})>"
