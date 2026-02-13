"""
Configuration API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional

from app.database.database import get_db
from app.database.models import MasterConfig

router = APIRouter()


# ==================== Schemas ====================

class RBCRatioResponse(BaseModel):
    """RBC 비율 응답"""
    ratio_percent: int = Field(..., description="RBC 비율 (0-100%)")
    description: str = Field(..., description="설명")
    
    class Config:
        from_attributes = True


class RBCRatioUpdate(BaseModel):
    """RBC 비율 업데이트 요청"""
    ratio_percent: int = Field(..., ge=0, le=100, description="RBC 비율 (0-100%)")


# ==================== Endpoints ====================

@router.get("/rbc-ratio", response_model=RBCRatioResponse)
def get_rbc_ratio_config(db: Session = Depends(get_db)):
    """
    RBC 비율 설정 조회
    
    Returns:
        현재 RBC 비율 설정 (PRBC vs Prefiltered)
    """
    config = db.query(MasterConfig).filter(
        MasterConfig.config_key == 'rbc_ratio_percent'
    ).first()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="RBC ratio configuration not found"
        )
    
    return RBCRatioResponse(
        ratio_percent=int(config.config_value),
        description=config.description or "PRBC vs Prefiltered RBC ratio"
    )


@router.put("/rbc-ratio", response_model=RBCRatioResponse)
def update_rbc_ratio_config(
    update: RBCRatioUpdate,
    db: Session = Depends(get_db)
):
    """
    RBC 비율 설정 업데이트
    
    Args:
        update: 새로운 RBC 비율 (0-100%)
        
    Returns:
        업데이트된 RBC 비율 설정
    """
    config = db.query(MasterConfig).filter(
        MasterConfig.config_key == 'rbc_ratio_percent'
    ).first()
    
    if not config:
        # Create new config if not exists
        config = MasterConfig(
            config_key='rbc_ratio_percent',
            config_value=str(update.ratio_percent),
            description='PRBC vs Prefiltered RBC ratio percentage'
        )
        db.add(config)
    else:
        # Update existing config
        config.config_value = str(update.ratio_percent)
    
    db.commit()
    db.refresh(config)
    
    return RBCRatioResponse(
        ratio_percent=int(config.config_value),
        description=config.description or "PRBC vs Prefiltered RBC ratio"
    )
