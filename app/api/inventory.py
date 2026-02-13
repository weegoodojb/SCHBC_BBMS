"""
Inventory API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.database.models import BloodMaster
from app.schemas.schemas import (
    InventoryStatusResponse,
    InventoryItem,
    InventoryUpdateRequest,
    InventoryUpdateResponse
)
from app.services.inventory_service import (
    get_inventory_status,
    update_inventory_and_log
)
from app.services.alert_service import check_blood_type_rbc_alert, check_single_item_alert
from app.services.email_service import EmailService

router = APIRouter(prefix="/api/inventory", tags=["Inventory"])


@router.get("/status", response_model=InventoryStatusResponse)
def get_status(db: Session = Depends(get_db)):
    """
    현재 재고 현황 조회
    
    - RBC 제제는 동적 목표재고 계산 포함
    - 알람 상태 체크 (현재재고 < 알람기준)
    
    Args:
        db: Database session
        
    Returns:
        재고 현황 및 통계
    """
    try:
        items, alert_count, rbc_ratio = get_inventory_status(db)
        
        # Convert to InventoryItem models
        inventory_items = [InventoryItem(**item) for item in items]
        
        return InventoryStatusResponse(
            total_items=len(inventory_items),
            alert_count=alert_count,
            rbc_ratio=rbc_ratio,
            items=inventory_items
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"재고 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/update", response_model=InventoryUpdateResponse)
def update_inventory(request: InventoryUpdateRequest, db: Session = Depends(get_db)):
    """
    재고 업데이트 및 로그 기록
    
    - Inventory 테이블 업데이트
    - StockLog에 입출고 기록
    - 비고(remark) 필수
    
    Args:
        request: 재고 업데이트 요청
        db: Database session
        
    Returns:
        업데이트 결과 및 로그 정보
        
    Raises:
        HTTPException: 재고 부족 또는 업데이트 실패 시
    """
    try:
        # Get preparation name
        blood_master = db.query(BloodMaster).filter(BloodMaster.id == request.prep_id).first()
        if not blood_master:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"제제 ID {request.prep_id}를 찾을 수 없습니다."
            )
        
        # Update inventory and create log
        inventory, stock_log, previous_qty = update_inventory_and_log(
            db=db,
            blood_type=request.blood_type,
            prep_id=request.prep_id,
            in_qty=request.in_qty,
            out_qty=request.out_qty,
            remark=request.remark
        )
        
        # Check for alerts after update
        alert_data = None
        
        # Check if this is an RBC preparation
        if blood_master.component == 'RBC':
            # Check total RBC for this blood type
            alert_data = check_blood_type_rbc_alert(db, request.blood_type)
        else:
            # Check individual item alert
            alert_data = check_single_item_alert(db, request.blood_type, request.prep_id)
        
        # Format alert email if needed (GAS will send it)
        alert_email = None
        if alert_data:
            alert_email = EmailService.format_alert_email(alert_data)
            EmailService.log_alert(alert_data)
        
        return InventoryUpdateResponse(
            success=True,
            message="재고가 성공적으로 업데이트되었습니다.",
            inventory_id=inventory.id,
            blood_type=inventory.blood_type,
            preparation=blood_master.preparation,
            previous_qty=previous_qty,
            current_qty=inventory.current_qty,
            log_id=stock_log.id,
            alert=alert_email  # Alert email data for GAS
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"재고 업데이트 중 오류가 발생했습니다: {str(e)}"
        )
