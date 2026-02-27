"""
재고 관리 서비스 - Alert 체크 기능 추가
"""
from sqlalchemy.orm import Session
from typing import Dict, Optional
import logging

from app.database.models import Inventory, BloodMaster, SafetyConfig


logger = logging.getLogger(__name__)


def check_blood_type_rbc_alert(db: Session, blood_type: str) -> Optional[Dict]:
    """
    특정 혈액형의 RBC 총 재고가 알림 기준 이하인지 확인
    
    Args:
        db: Database session
        blood_type: 혈액형 (A, B, O, AB)
        
    Returns:
        알림이 필요한 경우 알림 데이터, 아니면 None
    """
    # PRBC와 Prefiltered 제제 조회
    prbc = db.query(BloodMaster).filter(BloodMaster.preparation == 'PRBC').first()
    prefiltered = db.query(BloodMaster).filter(BloodMaster.preparation == 'Prefiltered').first()
    
    if not prbc or not prefiltered:
        logger.warning(f"RBC preparations not found in BloodMaster")
        return None
    
    # 해당 혈액형의 RBC 재고 조회
    prbc_inv = db.query(Inventory).filter(
        Inventory.blood_type == blood_type,
        Inventory.prep_id == prbc.id
    ).first()
    
    prefiltered_inv = db.query(Inventory).filter(
        Inventory.blood_type == blood_type,
        Inventory.prep_id == prefiltered.id
    ).first()
    
    # RBC 총 재고 계산
    total_rbc_qty = 0
    if prbc_inv:
        total_rbc_qty += prbc_inv.current_qty
    if prefiltered_inv:
        total_rbc_qty += prefiltered_inv.current_qty
    
    # 알림 기준 조회 (PRBC 기준 사용)
    safety_config = db.query(SafetyConfig).filter(
        SafetyConfig.blood_type == blood_type,
        SafetyConfig.prep_id == prbc.id
    ).first()
    
    if not safety_config:
        logger.warning(f"Safety config not found for {blood_type} PRBC")
        return None
    
    # 알림 체크
    if total_rbc_qty < safety_config.alert_threshold:
        alert_data = {
            'blood_type': blood_type,
            'preparation': 'RBC (PRBC + Prefiltered)',
            'current_qty': total_rbc_qty,
            'threshold': safety_config.alert_threshold,
            'prbc_qty': prbc_inv.current_qty if prbc_inv else 0,
            'prefiltered_qty': prefiltered_inv.current_qty if prefiltered_inv else 0
        }
        
        logger.info(f"Alert triggered for {blood_type} RBC: {total_rbc_qty} < {safety_config.alert_threshold}")
        return alert_data
    
    return None


def check_single_item_alert(db: Session, blood_type: str, prep_id: int) -> Optional[Dict]:
    """
    개별 제제의 재고 알림 체크
    
    Args:
        db: Database session
        blood_type: 혈액형
        prep_id: 제제 ID
        
    Returns:
        알림이 필요한 경우 알림 데이터, 아니면 None
    """
    # 재고 조회
    inventory = db.query(Inventory).filter(
        Inventory.blood_type == blood_type,
        Inventory.prep_id == prep_id
    ).first()
    
    if not inventory:
        return None
    
    # 제제 정보 조회
    blood_master = db.query(BloodMaster).filter(BloodMaster.id == prep_id).first()
    if not blood_master:
        return None
    
    # 안전 재고 설정 조회
    safety_config = db.query(SafetyConfig).filter(
        SafetyConfig.blood_type == blood_type,
        SafetyConfig.prep_id == prep_id
    ).first()
    
    if not safety_config:
        return None
    
    # 알림 체크
    if inventory.current_qty < safety_config.alert_threshold:
        alert_data = {
            'blood_type': blood_type,
            'preparation': blood_master.preparation,
            'component': blood_master.component,
            'current_qty': inventory.current_qty,
            'threshold': safety_config.alert_threshold
        }
        
        logger.info(f"Alert triggered for {blood_type} {blood_master.preparation}: "
                   f"{inventory.current_qty} < {safety_config.alert_threshold}")
        return alert_data
    
    return None
