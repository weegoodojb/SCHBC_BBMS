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
    """RBC 재고비 수정 요청 - 공통 적용 또는 혈액형/제제별 적용"""
    daily_consumption_rate: float = Field(..., ge=0.1, le=30.0, description="1일 재고비")
    safety_factor: float = Field(..., ge=0.5, le=10.0, description="적정재고비 배수")
    change_reason: str = Field(..., min_length=5, description="변경 사유 (5자 이상 필수)")
    blood_type: Optional[str] = Field(None, description="특정 혈액형 (미입력=전체 공통 적용)")
    prep_id: Optional[int] = Field(None, description="특정 제제 ID (미입력=전체 공통 적용)")
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
    RBC 재고비 수정 (관리자 전용)
    - blood_type/prep_id 미입력 → 전체 혈액형 공통 일괄 적용
    - blood_type/prep_id 입력 → 해당 혈액형/제제만 적용
    변경 사유 필수, 히스토리 자동 저장
    """
    blood_types = ['A', 'B', 'O', 'AB']

    def _upsert_config(blood_type: Optional[str], prep_id: Optional[int]):
        """단일 MasterConfig 행 upsert"""
        existing = db.query(MasterConfig).filter(
            MasterConfig.blood_type == blood_type if blood_type else MasterConfig.blood_type.is_(None),
            MasterConfig.prep_id == prep_id if prep_id else MasterConfig.prep_id.is_(None),
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
                blood_type=blood_type,
                prep_id=prep_id,
                config_key='rbc_factors',
                config_value=f"dcr={update.daily_consumption_rate},sf={update.safety_factor}",
                daily_consumption_rate=update.daily_consumption_rate,
                safety_factor=update.safety_factor
            )
            db.add(new_config)

        # 히스토리 저장 (dcr 기준)
        if old_dcr != update.daily_consumption_rate or old_sf != update.safety_factor:
            db.add(InventoryRatioHistory(
                blood_type=blood_type,
                prep_id=prep_id,
                config_key='daily_consumption_rate',
                old_factor=old_dcr,
                new_factor=update.daily_consumption_rate,
                change_reason=update.change_reason,
                changed_by=update.changed_by
            ))
            db.add(InventoryRatioHistory(
                blood_type=blood_type,
                prep_id=prep_id,
                config_key='safety_factor',
                old_factor=old_sf,
                new_factor=update.safety_factor,
                change_reason=update.change_reason,
                changed_by=update.changed_by
            ))

    # 공통 일괄 적용 (혈액형/제제별 미지정)
    if not update.blood_type and not update.prep_id:
        # 공통 행 저장
        _upsert_config(None, None)
        applied_to = "전체 공통 (공통 설정 행)"
    else:
        # 특정 혈액형/제제만 적용
        _upsert_config(update.blood_type, update.prep_id)
        applied_to = f"{update.blood_type or 'ALL'} / prep_id={update.prep_id or 'ALL'}"

    db.commit()

    return {
        "success": True,
        "applied_to": applied_to,
        "daily_consumption_rate": update.daily_consumption_rate,
        "safety_factor": update.safety_factor,
        "change_reason": update.change_reason,
        "message": f"RBC 재고비 업데이트 완료: {applied_to}"
    }


@router.get("/rbc-history", response_model=List[HistoryItem])
def get_rbc_history(limit: int = 50, db: Session = Depends(get_db)):
    """적정재고비 변경 히스토리 조회 (최신순)"""
    records = db.query(InventoryRatioHistory).order_by(
        InventoryRatioHistory.created_at.desc()
    ).limit(limit).all()
    return records
