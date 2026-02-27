from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.services.analytics_service import get_analytics_data
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

@router.get("/")
def get_dashboard_data(
    start_date: str = Query(None, description="시작일 (YYYY-MM-DD)"),
    end_date: str = Query(None, description="종료일 (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
    if not start_date:
        start_date = (datetime.strptime(end_date, "%Y-%m-%d") - timedelta(days=30)).strftime("%Y-%m-%d")
        
    try:
        data = get_analytics_data(db, start_date, end_date)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
