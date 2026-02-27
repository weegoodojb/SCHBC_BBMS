"""
Email Service - Gmail SMTP 기반 위험재고 알람 발송
"""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List
import logging

logger = logging.getLogger(__name__)

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "goodojb@gmail.com"
SMTP_PASSWORD = "Joanne@0619"


def send_danger_alert(blood_type: str, rbc_qty: int, actual_ratio: float, danger_threshold: float, recipients: List[str]):
    """
    위험재고 발생 시 등록된 이메일 목록으로 알람 발송
    """
    if not recipients:
        logger.warning("알람 수신 이메일이 등록되지 않아 발송을 생략합니다.")
        return

    subject = f"🚨 [SCHBC BBMS] RBC {blood_type}형 위험재고 알람"
    body = f"""
<html>
<body style="font-family: Arial, sans-serif; padding: 20px;">
  <h2 style="color: #dc3545;">🚨 RBC 위험재고 알람</h2>
  <p>RBC 재고량이 위험재고비 이하로 떨어졌습니다.</p>
  <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse;">
    <tr><th style="background:#f8f9fa;">혈액형</th><td><strong>{blood_type}형</strong></td></tr>
    <tr><th style="background:#f8f9fa;">현재 RBC 재고량</th><td>{rbc_qty} Unit</td></tr>
    <tr><th style="background:#f8f9fa;">현재 재고비</th><td style="color:#dc3545;"><strong>{actual_ratio:.2f}</strong></td></tr>
    <tr><th style="background:#f8f9fa;">위험재고비 기준</th><td>{danger_threshold:.2f}</td></tr>
  </table>
  <p style="margin-top: 16px; color: #666;">즉시 재고 확인 및 조치가 필요합니다.</p>
  <p style="color: #999; font-size: 12px;">— SCHBC BBMS 자동 알람 시스템</p>
</body>
</html>
"""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = SMTP_USER
        msg["To"] = ", ".join(recipients)

        msg.attach(MIMEText(body, "html", "utf-8"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, recipients, msg.as_string())

        logger.info(f"위험재고 알람 발송 완료: {blood_type}형 → {recipients}")
    except Exception as e:
        logger.error(f"이메일 발송 실패: {e}")
