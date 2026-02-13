"""
이메일 알림 서비스
"""
from datetime import datetime
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class EmailService:
    """이메일 알림 서비스 (GAS GmailApp 사용)"""
    
    @staticmethod
    def format_alert_email(alert_data: Dict) -> Dict[str, str]:
        """
        알림 이메일 포맷 생성
        
        Args:
            alert_data: 알림 데이터 (blood_type, current_qty, threshold 등)
            
        Returns:
            subject, body를 포함한 딕셔너리
        """
        blood_type = alert_data.get('blood_type', 'Unknown')
        current_qty = alert_data.get('current_qty', 0)
        threshold = alert_data.get('threshold', 0)
        prep_name = alert_data.get('preparation', 'RBC')
        
        subject = f"[SCHBC BBMS] {blood_type}형 {prep_name} 재고 부족 알림"
        
        body = f"""
순천향대학교 부천병원 혈액은행 재고 알림

{blood_type}형 {prep_name} 재고가 알림 기준치 이하입니다.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 재고 현황
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

혈액형: {blood_type}
제제명: {prep_name}
현재 재고: {current_qty} 단위
알림 기준: {threshold} 단위
부족 수량: {threshold - current_qty} 단위

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏰ 확인 정보
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

확인 시간: {datetime.now().strftime('%Y년 %m월 %d일 %H:%M:%S')}
시스템: SCHBC BBMS v1.0

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ 즉시 재고 확보가 필요합니다.

이 메일은 자동으로 발송되었습니다.
"""
        
        return {
            'subject': subject,
            'body': body
        }
    
    @staticmethod
    def log_alert(alert_data: Dict):
        """알림 로그 기록"""
        logger.warning(
            f"Low inventory alert: {alert_data.get('blood_type')} "
            f"{alert_data.get('preparation')} - "
            f"Current: {alert_data.get('current_qty')}, "
            f"Threshold: {alert_data.get('threshold')}"
        )
