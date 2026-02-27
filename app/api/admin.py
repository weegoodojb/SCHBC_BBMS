"""
Admin API - DB 진단 및 데이터 초기화 전용 엔드포인트
용도: 서버 측에서 직접 DB 테이블 확인 및 초기화
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database.database import get_db
from app.database.models import Base, InboundHistory, Inventory, StockLog
from app.database.database import engine

router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.get("/db-check")
def db_check(db: Session = Depends(get_db)):
    """DB 테이블 목록 및 inbound_history 상태 확인"""
    try:
        result = db.execute(text(
            "SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name"
        ))
        tables = [row[0] for row in result.fetchall()]
        
        inbound_count = 0
        inbound_exists = 'inbound_history' in tables
        if inbound_exists:
            inbound_count = db.query(InboundHistory).count()
        
        inventory_count = db.query(Inventory).count()
        stocklog_count = db.query(StockLog).count()
        
        return {
            "tables": tables,
            "inbound_history_exists": inbound_exists,
            "inbound_history_rows": inbound_count,
            "inventory_rows": inventory_count,
            "stocklog_rows": stocklog_count
        }
    except Exception as e:
        return {"error": str(e)}


@router.post("/create-missing-tables")
def create_missing_tables():
    """누락된 테이블(inbound_history 등) 생성"""
    try:
        Base.metadata.create_all(bind=engine)
        return {"message": "테이블 생성/확인 완료. inbound_history 포함 모든 테이블이 준비되었습니다."}
    except Exception as e:
        return {"error": str(e)}


@router.post("/reset-data")
def reset_data(db: Session = Depends(get_db)):
    """재고 수량 0 초기화, stock_log 및 inbound_history 전체 삭제"""
    try:
        # inbound_history 전체 삭제
        deleted_inbound = db.query(InboundHistory).delete()
        # stock_log 전체 삭제
        deleted_stocklog = db.query(StockLog).delete()
        # inventory 수량 0으로 초기화
        reset_count = db.query(Inventory).update({"current_qty": 0})
        db.commit()
        return {
            "message": "데이터 초기화 완료",
            "inventory_reset": reset_count,
            "stocklog_deleted": deleted_stocklog,
            "inbound_deleted": deleted_inbound
        }
    except Exception as e:
        db.rollback()
        return {"error": str(e)}
