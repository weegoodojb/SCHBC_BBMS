"""
재고 관리 서비스 - RBC 재고비 기반 적정재고 계산
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime
from math import ceil
from typing import List, Dict, Optional, Tuple
import logging

from app.database.models import (
    BloodMaster, SafetyConfig, SystemSettings, Inventory,
    StockLog, MasterConfig, InventoryRatioHistory
)
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)

BLOOD_TYPES = ['A', 'B', 'O', 'AB']
RBC_PREPS = ['PRBC', 'Prefiltered']
O_TYPE_BONUS = 4  # O형 RBC 추가 적정재고


# ==================== RBC 설정 조회 ====================

def get_rbc_factors(db: Session, blood_type: str = None, prep_id: int = None) -> Dict[str, float]:
    """
    RBC 재고비 설정 조회 (우선순위: 혈액형/제제 특정값 > 공통값 > 기본값)

    Args:
        blood_type: 혈액형 (None=공통)
        prep_id: 제제 ID (None=공통)

    Returns:
        {'daily_consumption_rate': float, 'safety_factor': float}
    """
    defaults = {'daily_consumption_rate': 3.0, 'safety_factor': 2.0}

    # 1. 혈액형/제제별 특정 설정 조회
    if blood_type and prep_id:
        specific = db.query(MasterConfig).filter(
            MasterConfig.blood_type == blood_type,
            MasterConfig.prep_id == prep_id,
            MasterConfig.config_key == 'rbc_factors'
        ).first()
        if specific and specific.daily_consumption_rate is not None:
            return {
                'daily_consumption_rate': specific.daily_consumption_rate,
                'safety_factor': specific.safety_factor or defaults['safety_factor']
            }

    # 2. 공통 설정 조회 (blood_type=None, prep_id=None)
    common = db.query(MasterConfig).filter(
        MasterConfig.blood_type.is_(None),
        MasterConfig.prep_id.is_(None),
        MasterConfig.config_key == 'rbc_factors'
    ).first()

    if common and common.daily_consumption_rate is not None:
        return {
            'daily_consumption_rate': common.daily_consumption_rate,
            'safety_factor': common.safety_factor or defaults['safety_factor']
        }

    # 3. legacy: rbc_ratio_percent 키 조회 (하위 호환)
    ratio_config = db.query(MasterConfig).filter(
        MasterConfig.config_key == 'rbc_ratio_percent'
    ).first()
    if ratio_config:
        try:
            ratio = float(ratio_config.config_value) / 100.0
            return {'daily_consumption_rate': defaults['daily_consumption_rate'], 'safety_factor': ratio * 4}
        except ValueError:
            pass

    return defaults


def get_rbc_ratio(db: Session) -> float:
    """Legacy: RBC 비율 조회 (0.0 ~ 1.0), 기본값 0.5"""
    config = db.query(MasterConfig).filter(
        MasterConfig.config_key == 'rbc_ratio_percent'
    ).first()
    if config:
        try:
            return float(config.config_value) / 100.0
        except ValueError:
            pass
    return 0.5


# ==================== RBC 적정재고 계산 ====================

def calculate_target_qty(daily_consumption_rate: float, safety_factor: float,
                          blood_type: str, is_rbc: bool) -> int:
    """
    적정재고 계산
    - 일반 RBC: ceil(daily_consumption_rate × safety_factor)
    - O형 RBC:  ceil(daily_consumption_rate × safety_factor) + 4
    - 비RBC:    SafetyConfig.safety_qty 그대로 사용
    """
    if not is_rbc:
        return 0  # 비RBC는 safety_config.safety_qty 사용

    base = ceil(daily_consumption_rate * safety_factor)
    return base + O_TYPE_BONUS if blood_type == 'O' else base


def calculate_rbc_targets(db: Session, blood_type: str) -> Dict[str, int]:
    """혈액형별 PRBC/Prefiltered 적정재고 계산"""
    factors = get_rbc_factors(db, blood_type)
    dcr = factors['daily_consumption_rate']
    sf = factors['safety_factor']

    target = calculate_target_qty(dcr, sf, blood_type, is_rbc=True)

    # PRBC / Prefiltered 비율 분배 (legacy rbc_ratio_percent 활용)
    ratio = get_rbc_ratio(db)
    prbc_target = round(target * ratio)
    prefiltered_target = target - prbc_target  # 합계 보장

    return {
        'PRBC': prbc_target,
        'Prefiltered': prefiltered_target,
        'total': target,
        'daily_consumption_rate': dcr,
        'safety_factor': sf
    }


def check_alert_status(current_qty: int, alert_threshold: int) -> bool:
    return current_qty < alert_threshold


# ==================== 재고 현황 ====================

def get_inventory_status(db: Session) -> Tuple[List[Dict], int, float]:
    """전체 재고 현황 및 경고 현황 조회"""
    rbc_ratio = get_rbc_ratio(db)
    inventories = db.query(Inventory).all()

    rbc_targets = {bt: calculate_rbc_targets(db, bt) for bt in BLOOD_TYPES}

    items = []
    alert_count = 0

    for inv in inventories:
        blood_master = db.query(BloodMaster).filter(BloodMaster.id == inv.prep_id).first()
        safety_config = db.query(SafetyConfig).filter(
            SafetyConfig.blood_type == inv.blood_type,
            SafetyConfig.prep_id == inv.prep_id
        ).first()

        if not blood_master or not safety_config:
            continue

        is_alert = check_alert_status(inv.current_qty, safety_config.alert_threshold)
        if is_alert:
            alert_count += 1

        # 적정재고 결정
        if blood_master.component == 'RBC':
            targets = rbc_targets.get(inv.blood_type, {})
            target_qty = targets.get(blood_master.preparation, None)
        else:
            # 기본 설정은 SafetyConfig의 safety_qty를 활용
            target_qty = safety_config.safety_qty
            # [기능 추가] Cryo AB형의 적정재고는 10으로 강제
            if blood_master.component == 'Cryo' and inv.blood_type == 'AB':
                target_qty = 10

        request_qty = max(0, (target_qty or 0) - inv.current_qty)

        items.append({
            'id': inv.id,
            'blood_type': inv.blood_type,
            'prep_id': inv.prep_id,
            'preparation': blood_master.preparation,
            'component': blood_master.component,
            'current_qty': inv.current_qty,
            'safety_qty': safety_config.safety_qty,
            'alert_threshold': safety_config.alert_threshold,
            'target_qty': target_qty,
            'request_qty': request_qty,  # 신청량 = 적정재고 - 현재고
            'is_alert': is_alert,
            'remark': inv.remark
        })

    return items, alert_count, rbc_ratio


# ==================== 재고 업데이트 ====================

def update_inventory_and_log(
    db: Session, blood_type: str, prep_id: int,
    in_qty: int, out_qty: int, remark: str
) -> Tuple[Inventory, StockLog, int]:
    """재고 업데이트 및 로그 기록"""
    inventory = db.query(Inventory).filter(
        Inventory.blood_type == blood_type,
        Inventory.prep_id == prep_id
    ).first()

    if not inventory:
        raise ValueError(f"Inventory not found for {blood_type} type, prep_id {prep_id}")

    previous_qty = inventory.current_qty
    new_qty = previous_qty + in_qty - out_qty

    if new_qty < 0:
        raise ValueError(f"재고 부족. 현재: {previous_qty}, 출고 요청: {out_qty}")

    inventory.current_qty = new_qty
    inventory.remark = remark
    inventory.updated_at = datetime.now()

    stock_log = StockLog(
        log_date=datetime.now(),
        blood_type=blood_type,
        prep_id=prep_id,
        in_qty=in_qty,
        out_qty=out_qty,
        remark=remark
    )
    db.add(stock_log)
    db.commit()
    db.refresh(inventory)
    db.refresh(stock_log)

    return inventory, stock_log, previous_qty
