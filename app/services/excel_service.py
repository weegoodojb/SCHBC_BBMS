import pandas as pd
import io
import math
from typing import List, Dict, Any

def parse_excel_inventory(file_bytes: bytes) -> Dict[str, Any]:
    """
    Excel 파일 바이트를 읽어서 혈액형/제제명별 수량을 집계합니다.
    매핑되지 않은 혈액명 목록도 함께 반환하여 UI에서 연결할 수 있도록 지원합니다.
    """
    try:
        df = pd.read_excel(io.BytesIO(file_bytes))
    except Exception as e:
        raise ValueError("엑셀 파일을 읽을 수 없습니다. 올바른 파일인지 확인해주세요.")
    
    # 필수 컬럼 검사 (최소한 혈액형과 제제명/혈액명과 유사한 단어가 있는지 찾기)
    cols = list(df.columns)
    bt_col = next((c for c in cols if "혈액형" in str(c)), None)
    prep_col = next((c for c in cols if "혈액명" in str(c) or "제제명" in str(c) or "성분" in str(c)), None)
    
    if not bt_col or not prep_col:
        raise ValueError(f"'혈액형' 및 '혈액명'(또는 제제명) 컬럼이 엑셀에 존재해야 합니다. 현재 컬럼: {cols}")
    
    # 사전 정의된 매핑 딕셔너리
    PREP_MAPPING = {
        "농축적혈구": "PRBC",
        "PRBC": "PRBC",
        "백혈구여과제거적혈구": "Pre-R",
        "백혈구여과제거적혈구(Pre-storage)": "Pre-R",
        "PRE-R": "Pre-R",
        "농축혈소판": "PC",
        "PC": "PC",
        "성분채집혈소판": "SDP",
        "SDP": "SDP",
        "신선동결혈장": "FFP",
        "FFP": "FFP",
        "동결침전제제": "Cryo",
        "CRYO": "Cryo"
    }
    
    BT_MAPPING = {
        "A+": "A", "A-": "A", "A": "A",
        "B+": "B", "B-": "B", "B": "B",
        "O+": "O", "O-": "O", "O": "O",
        "AB+": "AB", "AB-": "AB", "AB": "AB"
    }

    tally = {}
    unmapped_preps = set()
    mapped_rows = []

    for index, row in df.iterrows():
        raw_bt = str(row[bt_col]).strip()
        raw_prep = str(row[prep_col]).strip()
        
        # 값이 없는 행 무시
        if pd.isna(row[bt_col]) or pd.isna(row[prep_col]) or raw_bt == "nan" or raw_prep == "nan":
            continue
            
        # 혈액형 매핑 (A+, B 등에서 + 제거 등)
        bt_norm = raw_bt.upper()
        if bt_norm in BT_MAPPING:
            bt = BT_MAPPING[bt_norm]
        else:
            # 기본적으로 A, B, O, AB만 추출
            bt = next((b for b in ["AB", "A", "B", "O"] if b in bt_norm), None)
            if not bt:
                continue # 알 수 없는 혈액형 스킵

        # 제제명 매핑
        prep_norm = raw_prep.upper()
        # 정확한 일치나 부분 치환
        prep = None
        for k, v in PREP_MAPPING.items():
            if k.upper() in prep_norm:
                prep = v
                break
        
        if not prep:
            unmapped_preps.add(raw_prep)
            prep = raw_prep # 그대로 넣고 이따가 unmapped로 처리
            
        key = (bt, prep)
        tally[key] = tally.get(key, 0) + 1

        mapped_rows.append({
            "original_bt": raw_bt,
            "original_prep": raw_prep,
            "mapped_bt": bt,
            "mapped_prep": prep
        })

    # 집계 결과를 리스트 포맷으로
    items = []
    for (bt, prep), qty in tally.items():
        is_mapped = prep not in unmapped_preps
        items.append({
            "blood_type": bt,
            "preparation": prep,
            "qty": qty,
            "is_mapped": is_mapped
        })

    return {
        "items": items,
        "unmapped": list(unmapped_preps),
        "total_rows_processed": len(mapped_rows)
    }
