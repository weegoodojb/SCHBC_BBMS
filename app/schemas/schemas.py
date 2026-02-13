"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ============= Authentication Schemas =============

class LoginRequest(BaseModel):
    """Login request schema"""
    emp_id: str = Field(..., description="직원번호")
    password: str = Field(..., description="비밀번호")


class LoginResponse(BaseModel):
    """Login response schema"""
    access_token: str = Field(..., description="JWT 액세스 토큰")
    token_type: str = Field(default="bearer", description="토큰 타입")
    user_id: int = Field(..., description="사용자 ID")
    emp_id: str = Field(..., description="직원번호")
    name: str = Field(..., description="이름")
    email: Optional[str] = Field(None, description="이메일")


# ============= Inventory Schemas =============

class InventoryItem(BaseModel):
    """Individual inventory item with calculations"""
    id: int = Field(..., description="재고 ID")
    blood_type: str = Field(..., description="혈액형")
    prep_id: int = Field(..., description="제제 ID")
    preparation: str = Field(..., description="제제명")
    component: str = Field(..., description="혈액성분")
    current_qty: int = Field(..., description="현재재고량")
    safety_qty: int = Field(..., description="적정재고량")
    alert_threshold: int = Field(..., description="알람기준량")
    target_qty: Optional[int] = Field(None, description="목표재고량 (RBC 전용)")
    is_alert: bool = Field(..., description="알람 상태")
    remark: Optional[str] = Field(None, description="비고")
    
    class Config:
        from_attributes = True


class InventoryStatusResponse(BaseModel):
    """Inventory status response"""
    total_items: int = Field(..., description="총 재고 항목 수")
    alert_count: int = Field(..., description="알람 발생 항목 수")
    rbc_ratio: float = Field(..., description="RBC 비율 (PRBC:Prefiltered)")
    items: list[InventoryItem] = Field(..., description="재고 목록")


class InventoryUpdateRequest(BaseModel):
    """Inventory update request"""
    blood_type: str = Field(..., description="혈액형 (A, B, O, AB)")
    prep_id: int = Field(..., description="제제 ID")
    in_qty: int = Field(default=0, ge=0, description="입고량")
    out_qty: int = Field(default=0, ge=0, description="출고량")
    remark: str = Field(..., min_length=1, description="비고 (필수)")


class InventoryUpdateResponse(BaseModel):
    """Inventory update response"""
    success: bool = Field(..., description="성공 여부")
    message: str = Field(..., description="메시지")
    inventory_id: int = Field(..., description="재고 ID")
    blood_type: str = Field(..., description="혈액형")
    preparation: str = Field(..., description="제제명")
    previous_qty: int = Field(..., description="이전 재고량")
    current_qty: int = Field(..., description="현재 재고량")
    log_id: int = Field(..., description="로그 ID")
    alert: Optional[dict] = Field(None, description="알림 이메일 데이터 (subject, body)")


# ============= Common Schemas =============

class MessageResponse(BaseModel):
    """Generic message response"""
    message: str = Field(..., description="메시지")
    detail: Optional[str] = Field(None, description="상세 정보")
