"""
Inventory API endpoints
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.database.models import BloodMaster, Inventory, StockLog
from app.schemas.schemas import (
    InventoryStatusResponse,
    InventoryItem,
    InventoryUpdateRequest,
    InventoryUpdateResponse,
    BulkSaveRequest,
    BulkSaveResponse,
    BulkSaveResult,
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


@router.post("/bulk-save", response_model=BulkSaveResponse)
def bulk_save_inventory(request: BulkSaveRequest, db: Session = Depends(get_db)):
    """
    Matrix UI에서 입력한 재고 수량을 한 번에 저장 (Bulk Insert/Update)

    - qty는 절대값(입력한 새 재고량). 서버에서 delta 자동 계산.
    - delta > 0 → in_qty,  delta < 0 → out_qty 로 StockLog 기록
    - updated_at은 서버 시간 기준으로 자동 기록
    """
    results: list[BulkSaveResult] = []
    success_count = 0
    fail_count = 0

    for item in request.items:
        try:
            # 제제 정보 조회
            bm = db.query(BloodMaster).filter(BloodMaster.id == item.prep_id).first()
            if not bm:
                results.append(BulkSaveResult(
                    blood_type=item.blood_type, prep_id=item.prep_id,
                    preparation="unknown", previous_qty=0, new_qty=item.qty,
                    delta=0, success=False, error=f"prep_id {item.prep_id} 없음"
                ))
                fail_count += 1
                continue

            # 현재 재고 조회 (없으면 0으로 신규 생성)
            inv = db.query(Inventory).filter(
                Inventory.blood_type == item.blood_type,
                Inventory.prep_id   == item.prep_id
            ).first()

            if inv is None:
                inv = Inventory(
                    blood_type=item.blood_type,
                    prep_id=item.prep_id,
                    current_qty=0
                )
                db.add(inv)
                db.flush()

            previous_qty = inv.current_qty
            delta        = item.qty - previous_qty
            now          = datetime.now()

            # 재고 업데이트 (절대값으로 덮어쓰기 + 서버 타임스탬프)
            inv.current_qty = item.qty
            inv.updated_at  = now

            # 재고 변동이 있을 때만 StockLog 기록
            if delta != 0:
                log = StockLog(
                    log_date   = now,
                    blood_type = item.blood_type,
                    prep_id    = item.prep_id,
                    in_qty     = delta  if delta > 0 else 0,
                    out_qty    = -delta if delta < 0 else 0,
                    remark     = request.remark or f"{item.blood_type} {bm.preparation} 재고 갱신",
                    user_id    = request.user_id,
                    expiry_ok  = request.expiry_ok,
                    visual_ok  = request.visual_ok
                )
                db.add(log)

            results.append(BulkSaveResult(
                blood_type   = item.blood_type,
                prep_id      = item.prep_id,
                preparation  = bm.preparation,
                previous_qty = previous_qty,
                new_qty      = item.qty,
                delta        = delta,
                success      = True
            ))
            success_count += 1

        except Exception as e:
            db.rollback()
            results.append(BulkSaveResult(
                blood_type=item.blood_type, prep_id=item.prep_id,
                preparation="error", previous_qty=0, new_qty=item.qty,
                delta=0, success=False, error=str(e)
            ))
            fail_count += 1

    # 성공 항목 일괄 커밋
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"DB 커밋 실패: {str(e)}"
        )

    return BulkSaveResponse(
        total   = len(request.items),
        success = success_count,
        failed  = fail_count,
        results = results
    )
