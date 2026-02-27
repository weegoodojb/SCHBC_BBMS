"""
Alert Email Management API & Danger Alert Log API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from app.database.database import get_db
from app.database.models import AlertEmail, DangerAlertLog, User

router = APIRouter()


# ── Schemas ──────────────────────────────────────────────────────────────────

class AlertEmailCreate(BaseModel):
    email: str

class AlertEmailResponse(BaseModel):
    id: int
    email: str
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True

class DangerAlertCreate(BaseModel):
    blood_type: str
    rbc_qty: int
    danger_threshold: Optional[float] = None
    actual_ratio: Optional[float] = None
    reason: Optional[str] = None
    user_id: Optional[int] = None

class DangerAlertResponse(BaseModel):
    id: int
    alert_date: datetime
    blood_type: str
    rbc_qty: int
    danger_threshold: Optional[float]
    actual_ratio: Optional[float]
    reason: Optional[str]
    user_name: Optional[str] = None
    class Config:
        from_attributes = True


# ── Alert Email Endpoints ─────────────────────────────────────────────────────

@router.get("/api/alert-emails/", response_model=List[AlertEmailResponse])
def list_alert_emails(db: Session = Depends(get_db)):
    """알람 수신 이메일 목록 조회"""
    return db.query(AlertEmail).order_by(AlertEmail.created_at.asc()).all()


@router.post("/api/alert-emails/", response_model=AlertEmailResponse, status_code=201)
def add_alert_email(body: AlertEmailCreate, db: Session = Depends(get_db)):
    """알람 수신 이메일 추가"""
    existing = db.query(AlertEmail).filter(AlertEmail.email == body.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다.")
    ae = AlertEmail(email=body.email, is_active=True)
    db.add(ae)
    db.commit()
    db.refresh(ae)
    return ae


@router.delete("/api/alert-emails/{email_id}")
def delete_alert_email(email_id: int, db: Session = Depends(get_db)):
    """알람 수신 이메일 삭제"""
    ae = db.query(AlertEmail).filter(AlertEmail.id == email_id).first()
    if not ae:
        raise HTTPException(status_code=404, detail="이메일을 찾을 수 없습니다.")
    db.delete(ae)
    db.commit()
    return {"message": "삭제 완료"}


# ── Danger Alert Log Endpoints ────────────────────────────────────────────────

@router.get("/api/danger-alerts/")
def list_danger_alerts(limit: int = 100, db: Session = Depends(get_db)):
    """위험재고 알람 기록 조회 (최신순)"""
    rows = db.query(DangerAlertLog, User.name)\
        .outerjoin(User, DangerAlertLog.user_id == User.id)\
        .order_by(DangerAlertLog.alert_date.desc())\
        .limit(limit).all()

    result = []
    for log, uname in rows:
        result.append({
            "id": log.id,
            "alert_date": log.alert_date.strftime("%Y-%m-%d %H:%M"),
            "blood_type": log.blood_type,
            "rbc_qty": log.rbc_qty,
            "danger_threshold": log.danger_threshold,
            "actual_ratio": log.actual_ratio,
            "reason": log.reason or "",
            "user_name": uname or "알 수 없음"
        })
    return result


@router.post("/api/danger-alerts/", status_code=201)
def create_danger_alert(body: DangerAlertCreate, db: Session = Depends(get_db)):
    """위험재고 알람 이벤트 기록 (사유 포함)"""
    log_entry = DangerAlertLog(
        alert_date=datetime.now(),
        blood_type=body.blood_type,
        rbc_qty=body.rbc_qty,
        danger_threshold=body.danger_threshold,
        actual_ratio=body.actual_ratio,
        reason=body.reason,
        user_id=body.user_id
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    return {"id": log_entry.id, "message": "위험재고 알람이 기록되었습니다."}
