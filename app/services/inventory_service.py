"""
재고 관리 서비스
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import logging

from app.database.models import BloodMaster, SafetyConfig, SystemSettings, Inventory, StockLog, MasterConfig
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)


def get_rbc_ratio(db: Session) -> float:
    """
    RBC 비율 조회 (PRBC vs Prefiltered) - master_config에서 읽기
    
    Returns:
        float: RBC 비율 (0.0 ~ 1.0), 기본값 0.5
    """
    config = db.query(MasterConfig).filter(
        MasterConfig.config_key == 'rbc_ratio_percent'
    ).first()
    
    if config:
        try:
            # Percentage를 비율로 변환 (50% -> 0.5)
            ratio_percent = float(config.config_value)
            return ratio_percent / 100.0
        except ValueError:
            logger.warning(f"Invalid RBC ratio value: {config.config_value}, using default 0.5")
            return 0.5
    
    logger.info("RBC ratio not found in master_config, using default 0.5")
    return 0.5


def calculate_rbc_targets(db: Session, blood_type: str) -> Dict[str, int]:
    """
    Calculate dynamic RBC target inventory based on ratio
    
    Args:
        db: Database session
        blood_type: Blood type (A, B, O, AB)
        
    Returns:
        Dictionary with PRBC and Prefiltered target quantities
    """
    # Get RBC ratio
    ratio = get_rbc_ratio(db)
    
    # Get RBC preparation IDs
    prbc = db.query(BloodMaster).filter(BloodMaster.preparation == 'PRBC').first()
    prefiltered = db.query(BloodMaster).filter(BloodMaster.preparation == 'Prefiltered').first()
    
    if not prbc or not prefiltered:
        return {'PRBC': 0, 'Prefiltered': 0}
    
    # Get safety configs for this blood type
    prbc_config = db.query(SafetyConfig).filter(
        SafetyConfig.blood_type == blood_type,
        SafetyConfig.prep_id == prbc.id
    ).first()
    
    prefiltered_config = db.query(SafetyConfig).filter(
        SafetyConfig.blood_type == blood_type,
        SafetyConfig.prep_id == prefiltered.id
    ).first()
    
    # Calculate total RBC safety stock
    total_safety = 0
    if prbc_config:
        total_safety += prbc_config.safety_qty
    if prefiltered_config:
        total_safety += prefiltered_config.safety_qty
    
    # Calculate targets based on ratio
    prbc_target = round(total_safety * ratio)
    prefiltered_target = round(total_safety * (1 - ratio))
    
    return {
        'PRBC': prbc_target,
        'Prefiltered': prefiltered_target
    }


def check_alert_status(current_qty: int, alert_threshold: int) -> bool:
    """
    Check if inventory is below alert threshold
    
    Args:
        current_qty: Current quantity
        alert_threshold: Alert threshold
        
    Returns:
        True if alert should be triggered
    """
    return current_qty < alert_threshold


def get_inventory_status(db: Session) -> Tuple[List[Dict], int, float]:
    """
    Get complete inventory status with calculations
    
    Args:
        db: Database session
        
    Returns:
        Tuple of (inventory_items, alert_count, rbc_ratio)
    """
    # Get RBC ratio
    rbc_ratio = get_rbc_ratio(db)
    
    # Get all inventory with related data
    inventories = db.query(Inventory).all()
    
    # Calculate RBC targets for each blood type
    rbc_targets = {}
    for blood_type in ['A', 'B', 'O', 'AB']:
        rbc_targets[blood_type] = calculate_rbc_targets(db, blood_type)
    
    # Build response items
    items = []
    alert_count = 0
    
    for inv in inventories:
        # Get related BloodMaster
        blood_master = db.query(BloodMaster).filter(BloodMaster.id == inv.prep_id).first()
        
        # Get SafetyConfig
        safety_config = db.query(SafetyConfig).filter(
            SafetyConfig.blood_type == inv.blood_type,
            SafetyConfig.prep_id == inv.prep_id
        ).first()
        
        if not blood_master or not safety_config:
            continue
        
        # Check alert status
        is_alert = check_alert_status(inv.current_qty, safety_config.alert_threshold)
        if is_alert:
            alert_count += 1
        
        # Determine target_qty for RBC preparations
        target_qty = None
        if blood_master.component == 'RBC':
            targets = rbc_targets.get(inv.blood_type, {})
            target_qty = targets.get(blood_master.preparation, None)
        
        item = {
            'id': inv.id,
            'blood_type': inv.blood_type,
            'prep_id': inv.prep_id,
            'preparation': blood_master.preparation,
            'component': blood_master.component,
            'current_qty': inv.current_qty,
            'safety_qty': safety_config.safety_qty,
            'alert_threshold': safety_config.alert_threshold,
            'target_qty': target_qty,
            'is_alert': is_alert,
            'remark': inv.remark
        }
        items.append(item)
    
    return items, alert_count, rbc_ratio


def update_inventory_and_log(
    db: Session,
    blood_type: str,
    prep_id: int,
    in_qty: int,
    out_qty: int,
    remark: str
) -> Tuple[Inventory, StockLog, int]:
    """
    Update inventory and create stock log entry
    
    Args:
        db: Database session
        blood_type: Blood type
        prep_id: Preparation ID
        in_qty: Incoming quantity
        out_qty: Outgoing quantity
        remark: Remark (required)
        
    Returns:
        Tuple of (updated_inventory, stock_log, previous_qty)
    """
    # Get inventory record
    inventory = db.query(Inventory).filter(
        Inventory.blood_type == blood_type,
        Inventory.prep_id == prep_id
    ).first()
    
    if not inventory:
        raise ValueError(f"Inventory not found for {blood_type} type, prep_id {prep_id}")
    
    # Store previous quantity
    previous_qty = inventory.current_qty
    
    # Calculate new quantity
    new_qty = previous_qty + in_qty - out_qty
    
    if new_qty < 0:
        raise ValueError(f"Insufficient inventory. Current: {previous_qty}, Requested out: {out_qty}")
    
    # Update inventory
    inventory.current_qty = new_qty
    inventory.remark = remark
    inventory.updated_at = datetime.now()
    
    # Create stock log
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
