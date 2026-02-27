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
    is_admin: int = Field(default=0, description="관리자 권한 여부")


class UserResponse(BaseModel):
    id: int
    emp_id: str
    name: str
    email: Optional[str] = None
    is_admin: int
    remark: Optional[str] = None

    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    emp_id: str
    name: str
    password: str
    email: Optional[str] = None
    is_admin: int = 0
    remark: Optional[str] = None

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    is_admin: Optional[int] = None
    remark: Optional[str] = None

class UserPasswordReset(BaseModel):
    new_password: str


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


# ============= Bulk Save Schemas =============

class BulkSaveItem(BaseModel):
    """Matrix 테이블 단일 셀 데이터 - 절대값(현재 재고량)으로 저장"""
    blood_type: str  = Field(..., description="혈액형 (A/B/O/AB)")
    prep_id:    int  = Field(..., ge=1, description="제제 ID (BloodMaster.id)")
    qty:        int  = Field(..., ge=0, description="사용자가 입력한 현재 재고 수량(절대값)")

class BulkSaveRequest(BaseModel):
    """Matrix 전체 한 번에 저장 요청"""
    items:  list[BulkSaveItem] = Field(..., min_length=1, description="입력된 셀 목록")
    remark: Optional[str]      = Field(None, description="공통 비고")
    user_id: Optional[int]     = Field(None, description="저장 작업자 ID")
    expiry_ok: bool            = Field(default=True, description="유효기간 확인됨")
    visual_ok: bool            = Field(default=True, description="육안/성상 확인됨")

class BulkSaveResult(BaseModel):
    """개별 셀 저장 결과"""
    blood_type:   str
    prep_id:      int
    preparation:  str
    previous_qty: int
    new_qty:      int
    delta:        int   # new_qty - previous_qty (양수=입고, 음수=출고)
    success:      bool
    error:        Optional[str] = None

class BulkSaveResponse(BaseModel):
    """Bulk Save 전체 결과"""
    total:    int = Field(..., description="처리 시도 항목 수")
    success:  int = Field(..., description="성공 항목 수")
    failed:   int = Field(..., description="실패 항목 수")
    results:  list[BulkSaveResult]
    danger_alerts: list = Field(default=[], description="위험재고 발생 혈액형 목록")


# ============= Common Schemas =============

class MessageResponse(BaseModel):
    """Generic message response"""
    message: str = Field(..., description="메시지")
    detail: Optional[str] = Field(None, description="상세 정보")
