"""
TiDB Cloud 데이터 검증 스크립트
"""
import pymysql
from datetime import datetime

# TiDB Cloud 연결 정보
connection_config = {
    'host': 'gateway01.ap-northeast-1.prod.aws.tidbcloud.com',
    'port': 4000,
    'user': '4Hv47XPrF3C3oHV.root',
    'password': 'qcu4ldWPyNVjiMxm',
    'database': 'test',
    'ssl_verify_cert': True,
    'ssl_verify_identity': True
}

def verify_inventory_data():
    """재고 데이터 검증"""
    try:
        # TiDB 연결
        connection = pymysql.connect(**connection_config)
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        print("=" * 80)
        print("SCHBC BBMS - TiDB Cloud 데이터 검증")
        print("=" * 80)
        print()
        
        # 1. blood_inventory 테이블 전체 조회
        print("📊 1. 전체 재고 현황")
        print("-" * 80)
        cursor.execute("""
            SELECT 
                i.id,
                i.blood_type,
                bm.preparation,
                bm.component,
                i.current_qty,
                i.updated_at
            FROM blood_inventory i
            JOIN blood_master bm ON i.prep_id = bm.id
            ORDER BY i.blood_type, bm.preparation
        """)
        
        inventory_data = cursor.fetchall()
        
        if inventory_data:
            for row in inventory_data:
                print(f"  {row['blood_type']}형 {row['preparation']:12} | "
                      f"현재고: {row['current_qty']:3}유닛 | "
                      f"업데이트: {row['updated_at']}")
        else:
            print("  ⚠️ 재고 데이터 없음")
        
        print()
        
        # 2. A형 RBC 재고 확인 (PRBC + Prefiltered)
        print("📊 2. A형 RBC 재고 상세 (5:5 비율 확인)")
        print("-" * 80)
        cursor.execute("""
            SELECT 
                bm.preparation,
                i.current_qty,
                sc.safety_qty,
                sc.alert_threshold
            FROM blood_inventory i
            JOIN blood_master bm ON i.prep_id = bm.id
            LEFT JOIN safety_config sc ON i.blood_type = sc.blood_type AND i.prep_id = sc.prep_id
            WHERE i.blood_type = 'A' 
            AND bm.preparation IN ('PRBC', 'Prefiltered')
            ORDER BY bm.preparation
        """)
        
        rbc_data = cursor.fetchall()
        
        total_rbc = 0
        for row in rbc_data:
            print(f"  {row['preparation']:12} | "
                  f"현재고: {row['current_qty']:3}유닛 | "
                  f"안전재고: {row['safety_qty'] if row['safety_qty'] else 'N/A':3} | "
                  f"알림기준: {row['alert_threshold'] if row['alert_threshold'] else 'N/A':3}")
            total_rbc += row['current_qty'] if row['current_qty'] else 0
        
        print(f"\n  총 RBC 재고: {total_rbc}유닛")
        
        if len(rbc_data) == 2:
            prbc_qty = rbc_data[0]['current_qty'] if rbc_data[0]['current_qty'] else 0
            prefiltered_qty = rbc_data[1]['current_qty'] if rbc_data[1]['current_qty'] else 0
            
            if total_rbc > 0:
                prbc_ratio = (prbc_qty / total_rbc) * 100
                prefiltered_ratio = (prefiltered_qty / total_rbc) * 100
                print(f"  비율: PRBC {prbc_ratio:.1f}% : Prefiltered {prefiltered_ratio:.1f}%")
        
        print()
        
        # 3. 최근 입력 로그 확인
        print("📊 3. 최근 재고 입력 로그 (최근 5건)")
        print("-" * 80)
        cursor.execute("""
            SELECT 
                sl.blood_type,
                bm.preparation,
                sl.in_qty,
                sl.out_qty,
                sl.remark,
                sl.created_at
            FROM stock_log sl
            JOIN blood_master bm ON sl.prep_id = bm.id
            ORDER BY sl.created_at DESC
            LIMIT 5
        """)
        
        log_data = cursor.fetchall()
        
        if log_data:
            for row in log_data:
                action = f"입고 {row['in_qty']}유닛" if row['in_qty'] > 0 else f"출고 {row['out_qty']}유닛"
                print(f"  {row['created_at']} | {row['blood_type']}형 {row['preparation']:12} | "
                      f"{action:12} | {row['remark']}")
        else:
            print("  ⚠️ 로그 데이터 없음")
        
        print()
        
        # 4. RBC 비율 설정 확인
        print("📊 4. RBC 비율 설정 (master_config)")
        print("-" * 80)
        cursor.execute("""
            SELECT config_key, config_value, description
            FROM master_config
            WHERE config_key = 'rbc_ratio_percent'
        """)
        
        config_data = cursor.fetchone()
        
        if config_data:
            print(f"  설정 키: {config_data['config_key']}")
            print(f"  설정 값: {config_data['config_value']}%")
            print(f"  설명: {config_data['description']}")
        else:
            print("  ⚠️ RBC 비율 설정 없음")
        
        print()
        print("=" * 80)
        print("✅ 데이터 검증 완료")
        print("=" * 80)
        
        cursor.close()
        connection.close()
        
        return True
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return False

if __name__ == "__main__":
    verify_inventory_data()
