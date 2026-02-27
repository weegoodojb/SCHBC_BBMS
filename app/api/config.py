"""
Configuration API endpoints - RBC 재고비 관리 (혈액형/제제별 + 공통 일괄 적용)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from app.database.database import get_db
from app.database.models import MasterConfig, InventoryRatioHistory, BloodMaster

router = APIRouter()


# ==================== Schemas ====================

class RBCRatioResponse(BaseModel):
    ratio_percent: int = Field(..., description="RBC 비율 (0-100%)")
    description: str

    class Config:
        from_attributes = True


class RBCRatioUpdate(BaseModel):
    ratio_percent: int = Field(..., ge=0, le=100)


class RBCFactorsResponse(BaseModel):
    blood_type: Optional[str] = Field(None, description="혈액형 (None=공통)")
    prep_id: Optional[int] = Field(None, description="제제 ID (None=공통)")
    daily_consumption_rate: float = Field(..., description="1일 재고비")
    safety_factor: float = Field(..., description="적정재고비 (배수)")
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class RBCFactorsUpdate(BaseModel):
    """RBC 재고비 수정 요청 - 개별 혈액형 적용"""
    daily_consumption_rate: float = Field(..., ge=0.1, le=30.0, description="1일 재고비")
    safety_factor: float = Field(..., ge=0.5, le=10.0, description="적정재고비 배수")
    change_reason: str = Field("", description="변경 사유 (SF 변경시 5자 이상 필수, 프론트 검증)")
    blood_type: str = Field(..., description="특정 혈액형 (필수)")
    prep_id: Optional[int] = Field(None, description="특정 제제 ID")
    changed_by: Optional[str] = Field(None, description="변경자 사번")


class HistoryItem(BaseModel):
    id: int
    blood_type: Optional[str]
    prep_id: Optional[int]
    config_key: str
    old_factor: Optional[float]
    new_factor: float
    change_reason: str
    changed_by: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Endpoints ====================

@router.get("/rbc-ratio", response_model=RBCRatioResponse)
def get_rbc_ratio_config(db: Session = Depends(get_db)):
    """RBC 비율 설정 조회 (legacy)"""
    config = db.query(MasterConfig).filter(
        MasterConfig.config_key == 'rbc_ratio_percent'
    ).first()
    if not config:
        raise HTTPException(status_code=404, detail="RBC ratio configuration not found")
    return RBCRatioResponse(
        ratio_percent=int(config.config_value),
        description=config.description or "PRBC vs Prefiltered RBC ratio"
    )


@router.put("/rbc-ratio", response_model=RBCRatioResponse)
def update_rbc_ratio_config(update: RBCRatioUpdate, db: Session = Depends(get_db)):
    """RBC 비율 설정 업데이트 (legacy)"""
    config = db.query(MasterConfig).filter(
        MasterConfig.config_key == 'rbc_ratio_percent'
    ).first()
    if not config:
        config = MasterConfig(
            config_key='rbc_ratio_percent',
            config_value=str(update.ratio_percent),
            description='PRBC vs Prefiltered RBC ratio percentage'
        )
        db.add(config)
    else:
        config.config_value = str(update.ratio_percent)
    db.commit()
    db.refresh(config)
    return RBCRatioResponse(
        ratio_percent=int(config.config_value),
        description=config.description or "PRBC vs Prefiltered RBC ratio"
    )


@router.get("/rbc-factors", response_model=List[RBCFactorsResponse])
def get_rbc_factors(db: Session = Depends(get_db)):
    """
    RBC 재고비 설정 목록 조회
    - 공통 설정 + 혈액형/제제별 설정 모두 반환
    """
    configs = db.query(MasterConfig).filter(
        MasterConfig.config_key == 'rbc_factors'
    ).all()

    result = []
    for c in configs:
        result.append(RBCFactorsResponse(
            blood_type=c.blood_type,
            prep_id=c.prep_id,
            daily_consumption_rate=c.daily_consumption_rate or 3.0,
            safety_factor=c.safety_factor or 2.0,
            updated_at=c.updated_at
        ))

    # 설정 없으면 기본값 반환
    if not result:
        result.append(RBCFactorsResponse(
            blood_type=None,
            prep_id=None,
            daily_consumption_rate=3.0,
            safety_factor=2.0,
            updated_at=None
        ))
    return result


@router.put("/rbc-factors", response_model=dict)
def update_rbc_factors(update: RBCFactorsUpdate, db: Session = Depends(get_db)):
    """
    RBC 재고비 개별 혈액형별 수정 적용
    """
    import math
    from app.database.models import SafetyConfig

    if update.blood_type not in ['A', 'B', 'O', 'AB']:
        raise HTTPException(status_code=400, detail="Invalid blood_type")

    # 1. MasterConfig upsert
    existing = db.query(MasterConfig).filter(
        MasterConfig.blood_type == update.blood_type,
        MasterConfig.prep_id == update.prep_id if update.prep_id else MasterConfig.prep_id.is_(None),
        MasterConfig.config_key == 'rbc_factors'
    ).first()

    old_dcr = existing.daily_consumption_rate if existing else None
    old_sf = existing.safety_factor if existing else None

    if existing:
        existing.daily_consumption_rate = update.daily_consumption_rate
        existing.safety_factor = update.safety_factor
        existing.updated_at = datetime.now()
    else:
        new_config = MasterConfig(
            blood_type=update.blood_type,
            prep_id=update.prep_id,
            config_key='rbc_factors',
            config_value=f"dcr={update.daily_consumption_rate},sf={update.safety_factor}",
            daily_consumption_rate=update.daily_consumption_rate,
            safety_factor=update.safety_factor
        )
        db.add(new_config)

    # 히스토리 추가
    if old_dcr != update.daily_consumption_rate:
        db.add(InventoryRatioHistory(
            blood_type=update.blood_type,
            prep_id=update.prep_id,
            config_key='daily_consumption_rate',
            old_factor=old_dcr,
            new_factor=update.daily_consumption_rate,
            change_reason=update.change_reason,
            changed_by=update.changed_by
        ))
    if old_sf != update.safety_factor:
        db.add(InventoryRatioHistory(
            blood_type=update.blood_type,
            prep_id=update.prep_id,
            config_key='safety_factor',
            old_factor=old_sf,
            new_factor=update.safety_factor,
            change_reason=update.change_reason,
            changed_by=update.changed_by
        ))

    # 2. SafetyConfig 즉시 업데이트 (목표 재고수량 연산)
    target = math.ceil(update.daily_consumption_rate * update.safety_factor)
    if update.blood_type == 'O':
        target += 4

    # PRBC(1), Prefiltered(2)에 대한 target 분배 (Legacy ratio 기능 사용)
    from app.services.inventory_service import get_rbc_ratio
    ratio = get_rbc_ratio(db)
    
    # 올바른 분배: 총합(target)을 PRBC와 Pre-R로 분배. 기본값이 0.5(50%)임.
    prbc_target = round(target * ratio)
    prefiltered_target = target - prbc_target

    # SafetyConfig 갱신
    db.query(SafetyConfig).filter(
        SafetyConfig.blood_type == update.blood_type,
        SafetyConfig.prep_id == 1
    ).update({"safety_qty": prbc_target})

    db.query(SafetyConfig).filter(
        SafetyConfig.blood_type == update.blood_type,
        SafetyConfig.prep_id == 2
    ).update({"safety_qty": prefiltered_target})

    db.commit()

    return {
        "success": True,
        "applied_to": update.blood_type,
        "daily_consumption_rate": update.daily_consumption_rate,
        "safety_factor": update.safety_factor,
        "change_reason": update.change_reason,
        "message": f"RBC 재고비 업데이트 완료: {update.blood_type}"
    }


@router.get("/rbc-history", response_model=List[HistoryItem])
def get_rbc_history(limit: int = 50, db: Session = Depends(get_db)):
    """적정재고비 변경 히스토리 조회 (최신순)"""
    records = db.query(InventoryRatioHistory).order_by(
        InventoryRatioHistory.created_at.desc()
    ).limit(limit).all()
    return records
