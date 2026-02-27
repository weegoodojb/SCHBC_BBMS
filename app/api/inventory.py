"""
Inventory API endpoints
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from sqlalchemy.orm import Session
from app.database.database import get_db
from sqlalchemy import desc
from app.database.models import BloodMaster, Inventory, StockLog, InboundHistory, User
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
from app.services.excel_service import parse_excel_inventory

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

from typing import List

@router.post("/upload")
async def upload_excel_inventory(files: List[UploadFile] = File(...), db: Session = Depends(get_db)):
    """
    (통계용) 엑셀 파일(여러 개 가능)을 업로드하여 입고 내역(InboundHistory)에 즉시 저장합니다.
    주의: 이 데이터는 재고량(Inventory)이나 실사로그(StockLog)에 반영되지 않는 순수 통계 데이터입니다.
    """
    total_processed = 0
    total_saved = 0
    
    # 혈액제제명 -> prep_id 매핑을 위해 BloodMaster 조회
    preps = db.query(BloodMaster).all()
    prep_map = {p.preparation: p.id for p in preps}
    
    for file in files:
        if not file.filename.endswith((".xlsx", ".xls")):
            continue # 확장자 안맞는 파일은 조용히 무시 (혹은 에러처리)
            
        try:
            contents = await file.read()
            # 엑셀 파싱 (기존 서비스 재활용 - 반환 포맷: {"items": [{"blood_type": "A", "preparation": "PRBC", "qty": 10, ...}], ...})
            result = parse_excel_inventory(contents)
            total_processed += 1
            
            for item in result["items"]:
                # 매핑된(시스템에 존재하는) 제제명만 저장
                if item["is_mapped"] and item["preparation"] in prep_map:
                    inbound_record = InboundHistory(
                        receive_date=datetime.now().date(), # 실제론 엑셀 기준일을 뽑아야 하나, 현재 parse_excel_inventory는 집계만 하므로 업로드일 사용
                        blood_type=item["blood_type"],
                        prep_id=prep_map[item["preparation"]],
                        qty=item["qty"]
                    )
                    db.add(inbound_record)
                    total_saved += item["qty"]
                    
        except Exception as e:
            # 여러 파일 중 하나가 실패하더라도 전체를 롤백할지, 스킵할지 결정
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"엑셀 파일({file.filename}) 처리 중 오류: {str(e)}"
            )
            
    db.commit()
    
    return {
        "message": "입고 통계 저장 완료",
        "files_processed": total_processed,
        "total_qty_saved": total_saved
    }

@router.get("/logs")
def get_audit_logs(limit: int = 100, db: Session = Depends(get_db)):
    """
    재고 실사 기록(StockLog) 최신순 조회
    - InboundHistory(엑셀업로드 통계)는 포함하지 않음. 오직 수동 실사내역만.
    """
    logs = db.query(StockLog, User.name, BloodMaster.preparation)\
        .outerjoin(User, StockLog.user_id == User.id)\
        .outerjoin(BloodMaster, StockLog.prep_id == BloodMaster.id)\
        .order_by(desc(StockLog.log_date))\
        .limit(limit)\
        .all()
    
    result = []
    for log, uname, prep in logs:
        delta = log.in_qty - log.out_qty
        result.append({
            "id": log.id,
            "log_date": log.log_date.strftime("%Y-%m-%d %H:%M"),
            "blood_type": log.blood_type,
            "preparation": prep or "알 수 없음",
            "delta": delta,
            "remark": log.remark or "",
            "user_name": uname or "시스템/알 수 없음",
            "expiry_ok": log.expiry_ok,
            "visual_ok": log.visual_ok
        })
    return result
