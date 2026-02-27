from sqlalchemy.orm import Session
from sqlalchemy import func
import pandas as pd
from datetime import datetime, timedelta
from app.database.models import Inventory, StockLog, BloodMaster, SafetyConfig

def get_analytics_data(db: Session, start_date: str, end_date: str):
    """
    지정된 기간 동안의 분석 데이터를 생성합니다.
    - RBC 추이 (PRBC + Pre-R 합산)
    - FFP 추이
    - 요약 카드 데이터 (기간 내 입고량, 최소 재고, 평균 재고)
    - 목표 미달 경고 내역
    """
    start = datetime.strptime(start_date, '%Y-%m-%d').date()
    end = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # 1. 모든 `BloodMaster` 
    preps = db.query(BloodMaster).all()
    prep_map = {p.id: p.preparation for p in preps}
    
    # 2. 현재 재고 가져오기
    current_inv = db.query(Inventory).all()
    current_stock = {} # (blood_type, prep_id): qty
    for inv in current_inv:
        current_stock[(inv.blood_type, inv.prep_id)] = inv.current_qty
        
    # 3. 현재 목표 재고 가져오기
    safety_configs = db.query(SafetyConfig).all()
    target_stocks = {}
    for sc in safety_configs:
        target_stocks[(sc.blood_type, sc.prep_id)] = sc.safety_qty
        
    # 4. StockLog 전체 가져오기 및 역산
    # 오늘 포함 미래의 데이터부터 과거로 역산해야 함.
    # 안전하게 전체 StockLog를 들고 오되 쿼리를 가볍게... (메모리 로싱은 병원 데이터에선 크지 않음)
    logs = db.query(
        StockLog.log_date,
        StockLog.blood_type,
        StockLog.prep_id,
        StockLog.in_qty,
        StockLog.out_qty
    ).order_by(StockLog.log_date.desc()).all()
    
    df_logs = pd.DataFrame(logs)
    
    # 데일리 재고 저장소
    daily_stock_history = []
    
    # 날짜 범위 (end_date부터 과거로 하루 단위)
    # db.Inventory는 '오늘/현재'의 값이 반영된 상태.
    # 만약 오늘 발생한 로그가 있다면, 어제 자정 기준 재고 = 현재 재고 - 오늘 델타
    today = datetime.now().date()
    current_iter_date = today
    
    # iter_stock: 각 스텝에서의 기준 재고 (처음엔 current)
    iter_stock = current_stock.copy()
    
    # 로그가 없는 경우 빈 데이터프레임 방어
    if df_logs.empty:
        df_logs = pd.DataFrame(columns=['log_date', 'blood_type', 'prep_id', 'in_qty', 'out_qty'])
    else:
        df_logs['date'] = pd.to_datetime(df_logs['log_date']).dt.date
        df_logs['delta'] = df_logs['in_qty'] - df_logs['out_qty']

    # 기간 구하기
    # start부터 end까지 (+ today ~ end) 역산
    date_range = []
    d = today
    while d >= start:
        date_range.append(d)
        d -= timedelta(days=1)
        
    for d in date_range:
        # 하루치 재고 스냅샷 저장 (해당 날짜의 종료시점 재고)
        for (bt, pid), qty in iter_stock.items():
            daily_stock_history.append({
                'date': d.strftime('%Y-%m-%d'),
                'blood_type': bt,
                'prep_id': pid,
                'qty': qty
            })
            
        # d 일자에 발생한 로그의 델타를 빼서 (과거로 가니까) d-1 종가 산출
        if not df_logs.empty:
            day_logs = df_logs[df_logs['date'] == d]
            for _, row in day_logs.iterrows():
                key = (row['blood_type'], row['prep_id'])
                if key in iter_stock:
                    iter_stock[key] -= row['delta']
                    if iter_stock[key] < 0:
                        iter_stock[key] = 0

    df_stock = pd.DataFrame(daily_stock_history)
    # 기간 필터
    df_stock['date_obj'] = pd.to_datetime(df_stock['date']).dt.date
    df_period = df_stock[(df_stock['date_obj'] >= start) & (df_stock['date_obj'] <= end)]
    
    # 매핑 이름 조인
    if not df_period.empty:
        df_period['prep_name'] = df_period['prep_id'].map(prep_map)
    else:
        return {"error": "데이터가 없습니다."} # UI를 위해 빈 통계라도 리턴해야함

    # -- 통계 및 차트 추출 --
    
    # 1. RBC 합산 (PRBC + Pre-R)
    rbc_preps = [k for k,v in prep_map.items() if v in ["PRBC", "Pre-R", "Prefiltered"]]
    df_rbc = df_period[df_period['prep_id'].isin(rbc_preps)].groupby(['date', 'blood_type'])['qty'].sum().reset_index()
    
    # 2. FFP
    ffp_preps = [k for k,v in prep_map.items() if v == "FFP"]
    df_ffp = df_period[df_period['prep_id'].isin(ffp_preps)].groupby(['date', 'blood_type'])['qty'].sum().reset_index()
    
    # 날짜 정렬 (과거 -> 현재)
    dates = sorted(list(set(df_period['date'].tolist())))
    
    # 차트 데이터 생성 유틸
    def make_chart_data(df_group):
        series = {'A': [], 'B': [], 'O': [], 'AB': []}
        for d in dates:
            day_data = df_group[df_group['date'] == d]
            for bt in ['A', 'B', 'O', 'AB']:
                val = day_data[day_data['blood_type'] == bt]['qty'].sum()
                series[bt].append(int(val))
        return {'dates': dates, 'series': series}

    chart_rbc = make_chart_data(df_rbc)
    chart_ffp = make_chart_data(df_ffp)
    
    # -- 3. 목표 미달 알람(Alert) 히스토리 추출 (해당 기간) --
    alerts = []
    # RBC의 타겟을 조회하여 daily RBC와 비교
    for d in dates:
        day_rbc = df_rbc[df_rbc['date'] == d]
        for bt in ['A', 'B', 'O', 'AB']:
            # RBC 타겟 합산 (PRBC + Pre-R)
            target = 0
            for pid in rbc_preps:
                target += target_stocks.get((bt, pid), 0)
                
            qty = day_rbc[day_rbc['blood_type'] == bt]['qty'].sum() if not day_rbc.empty else 0
            if qty < target:
                alerts.append({
                    'date': d,
                    'blood_type': bt,
                    'component': 'RBC 합산',
                    'qty': int(qty),
                    'target': int(target),
                    'reason': '목표 재고량 미만'
                })
                
    # FFP 타겟 비교
    # FFP도 알람 띄우면 좋지만 유저가 "PRBC"만 명시했음. 일단 RBC만.
    alerts = sorted(alerts, key=lambda x: x['date'], reverse=True)
    
    # -- 요약 카드 (해당 기간내) --
    total_in = 0
    total_out = 0
    if not df_logs.empty:
        df_logs_period = df_logs[(df_logs['date'] >= start) & (df_logs['date'] <= end)]
        total_in = int(df_logs_period['in_qty'].sum())
        total_out = int(df_logs_period['out_qty'].sum())
        
    avg_rbc = float(df_rbc['qty'].sum() / len(dates)) if len(dates) > 0 and not df_rbc.empty else 0
    min_rbc = int(df_rbc.groupby('date')['qty'].sum().min()) if not df_rbc.empty else 0
    
    return {
        "summary": {
            "total_in": total_in,
            "total_out": total_out,
            "avg_rbc": round(avg_rbc, 1),
            "min_rbc": min_rbc
        },
        "chart_rbc": chart_rbc,
        "chart_ffp": chart_ffp,
        "alerts": alerts
    }
