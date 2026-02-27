"""
Database Models for SCHBC BBMS
- MasterConfig: blood_type/prep_id별 별도 행 (daily_consumption_rate, safety_factor)
- InventoryRatioHistory: 적정재고비 변경 히스토리
"""
from datetime import datetime
from math import ceil
from sqlalchemy import Column, Integer, String, Float, DateTime, Date, ForeignKey, Text, UniqueConstraint, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

# ==================== Configuration ====================

class MasterConfig(Base):
    """
    마스터 설정 테이블 - 혈액형/제제별 RBC 재고비 관리
    
    설계 원칙:
    - blood_type + prep_id 기준으로 별도 행 관리 (향후 확장성)
    - blood_type=None, prep_id=None → 전체 공통 기본값 행
    - 초기에는 공통 일괄 적용 기능으로 모든 행 동일값 유지
    """
    __tablename__ = 'master_config'

    id = Column(Integer, primary_key=True, autoincrement=True)
    blood_type = Column(String(5), nullable=True, comment='혈액형 (A/B/O/AB, NULL=공통)')
    prep_id = Column(Integer, ForeignKey('blood_master.id'), nullable=True, comment='제제 ID (NULL=공통)')
    config_key = Column(String(50), nullable=False, comment='설정 키')
    config_value = Column(String(255), nullable=False, comment='설정 값 (문자열로 저장)')
    daily_consumption_rate = Column(Float, nullable=True, comment='1일 재고비 (소수점 1자리)')
    safety_factor = Column(Float, nullable=True, comment='적정재고비 (배수)')
    danger_factor = Column(Float, nullable=True, comment='위험재고비 (배수) - 미만 시 알람')
    description = Column(Text, comment='설명')
    created_at = Column(DateTime, default=datetime.now, comment='생성일시')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='수정일시')

    __table_args__ = (
        UniqueConstraint('blood_type', 'prep_id', 'config_key', name='uix_master_config'),
    )

    def __repr__(self):
        scope = f"{self.blood_type or 'ALL'}/{self.prep_id or 'ALL'}"
        return f"<MasterConfig({scope} key='{self.config_key}' value='{self.config_value}')>"


class InventoryRatioHistory(Base):
    """적정재고비 변경 히스토리 테이블"""
    __tablename__ = 'inventory_ratio_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    blood_type = Column(String(5), nullable=True, comment='혈액형 (NULL=공통 변경)')
    prep_id = Column(Integer, ForeignKey('blood_master.id'), nullable=True, comment='제제 ID (NULL=공통 변경)')
    config_key = Column(String(50), nullable=False, comment='변경된 설정 키')
    old_factor = Column(Float, nullable=True, comment='변경 전 값')
    new_factor = Column(Float, nullable=False, comment='변경 후 값')
    change_reason = Column(Text, nullable=False, comment='변경 사유 (필수)')
    changed_by = Column(String(50), nullable=True, comment='변경자 사번')
    created_at = Column(DateTime, default=datetime.now, comment='변경일시')

    def __repr__(self):
        return f"<InventoryRatioHistory({self.config_key}: {self.old_factor} → {self.new_factor})>"


# ==================== Users ====================

class User(Base):
    """사용자 정보 테이블"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    emp_id = Column(String(50), unique=True, nullable=False, comment='직원번호')
    name = Column(String(100), nullable=False, comment='이름')
    password_hash = Column(String(255), nullable=False, comment='비밀번호 해시')
    email = Column(String(100), comment='이메일')
    is_admin = Column(Integer, default=0, comment='관리자 여부 (0=일반, 1=관리자)')
    remark = Column(Text, comment='비고')
    created_at = Column(DateTime, default=datetime.now, comment='생성일시')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='수정일시')

    def __repr__(self):
        return f"<User(emp_id='{self.emp_id}', name='{self.name}')>"


# ==================== Blood Products ====================

class BloodMaster(Base):
    """혈액제제 마스터 테이블"""
    __tablename__ = 'blood_master'

    id = Column(Integer, primary_key=True, autoincrement=True)
    component = Column(String(20), nullable=False, comment='혈액성분 (RBC, PLT, FFP, Cryo)')
    preparation = Column(String(50), nullable=False, comment='제제명 (PRBC, Prefiltered, PC, SDP, FFP, Cryo)')
    remark = Column(Text, comment='비고')
    created_at = Column(DateTime, default=datetime.now, comment='생성일시')

    __table_args__ = (
        UniqueConstraint('component', 'preparation', name='uix_blood_component_prep'),
    )

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

    blood_prep = relationship('BloodMaster', back_populates='safety_configs')

    __table_args__ = (
        UniqueConstraint('blood_type', 'prep_id', name='uix_blood_type_prep'),
    )

    def __repr__(self):
        return f"<SafetyConfig({self.blood_type}, prep={self.prep_id}, safety={self.safety_qty})>"


# ==================== Inventory ====================

class Inventory(Base):
    """현재 재고 테이블"""
    __tablename__ = 'inventory'

    id = Column(Integer, primary_key=True, autoincrement=True)
    blood_type = Column(String(5), nullable=False, comment='혈액형 (A, B, O, AB)')
    prep_id = Column(Integer, ForeignKey('blood_master.id'), nullable=False, comment='제제 ID')
    current_qty = Column(Integer, nullable=False, default=0, comment='현재재고량')
    remark = Column(Text, comment='비고')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='수정일시')

    blood_prep = relationship('BloodMaster', back_populates='inventories')

    __table_args__ = (
        UniqueConstraint('blood_type', 'prep_id', name='uix_inventory_blood_type_prep'),
    )

    def __repr__(self):
        return f"<Inventory({self.blood_type}, prep={self.prep_id}, qty={self.current_qty})>"


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
    
    # Audit trail fields
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True, comment='작업자 ID')
    expiry_ok = Column(Boolean, default=True, comment='유효기간 확인')
    visual_ok = Column(Boolean, default=True, comment='육안/성상 확인')
    
    created_at = Column(DateTime, default=datetime.now, comment='생성일시')

    blood_prep = relationship('BloodMaster', back_populates='stock_logs')

    def __repr__(self):
        return f"<StockLog({self.blood_type}, in={self.in_qty}, out={self.out_qty})>"


# ==================== Inbound ====================

class InboundHistory(Base):
    """(통계용) 엑셀 업로드 입고 내역 테이블"""
    __tablename__ = 'inbound_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    receive_date = Column(Date, nullable=False, default=datetime.now().date, comment='입고일자 (엑셀기준)')
    blood_type = Column(String(5), nullable=False, comment='혈액형')
    prep_id = Column(Integer, ForeignKey('blood_master.id'), nullable=False, comment='제제 ID')
    qty = Column(Integer, nullable=False, default=0, comment='입고량')
    created_at = Column(DateTime, default=datetime.now, comment='생성일시 (업로드일시)')

    blood_prep = relationship('BloodMaster')

    def __repr__(self):
        return f"<InboundHistory(date={self.receive_date}, {self.blood_type}, prep={self.prep_id}, qty={self.qty})>"


# ==================== Helper ====================

class SystemSettings(Base):
    """시스템 설정 테이블 (Key-Value, legacy 호환)"""
    __tablename__ = 'system_settings'

    key = Column(String(100), primary_key=True, comment='설정 키')
    value = Column(String(255), nullable=False, comment='설정 값')
    description = Column(Text, comment='설정 설명')
    remark = Column(Text, comment='비고')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='수정일시')

    def __repr__(self):
        return f"<SystemSettings(key='{self.key}', value='{self.value}')>"


# ==================== Alert Emails ====================

class AlertEmail(Base):
    """위험재고 알람 수신 이메일 목록"""
    __tablename__ = 'alert_emails'

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, comment='알람 수신 이메일')
    is_active = Column(Boolean, default=True, comment='활성화 여부')
    created_at = Column(DateTime, default=datetime.now, comment='등록일시')

    def __repr__(self):
        return f"<AlertEmail(email='{self.email}')>"


class DangerAlertLog(Base):
    """위험재고 알람 기록 테이블 (RBC 전용)"""
    __tablename__ = 'danger_alert_log'

    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_date = Column(DateTime, nullable=False, default=datetime.now, comment='알람 발생일시')
    blood_type = Column(String(5), nullable=False, comment='혈액형')
    rbc_qty = Column(Integer, nullable=False, comment='발생 시점 RBC 재고량')
    danger_threshold = Column(Float, nullable=True, comment='위험재고비 기준값 (DCR x DF)')
    actual_ratio = Column(Float, nullable=True, comment='실제 재고비 (qty / DCR)')
    reason = Column(Text, nullable=True, comment='위험재고 발생 사유 (사용자 입력)')
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True, comment='기록자 ID')
    created_at = Column(DateTime, default=datetime.now, comment='생성일시')

    def __repr__(self):
        return f"<DangerAlertLog({self.blood_type}, ratio={self.actual_ratio})>"
