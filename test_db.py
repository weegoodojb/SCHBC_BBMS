import sys
import math
from app.database.database import SessionLocal
from app.database.models import MasterConfig, SafetyConfig, BloodMaster

db = SessionLocal()
configs = db.query(MasterConfig).filter(MasterConfig.config_key.in_(['rbc_ratio_percent', 'rbc_factors'])).all()
for c in configs:
    print(c.config_key, c.blood_type, c.config_value)

safeties = db.query(SafetyConfig).all()
for s in safeties:
    print(s.blood_type, s.prep_id, s.safety_qty)

db.close()
