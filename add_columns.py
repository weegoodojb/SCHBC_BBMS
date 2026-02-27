import sys
from sqlalchemy import text
from app.database.database import SessionLocal

try:
    db = SessionLocal()
    db.execute(text('ALTER TABLE stock_log ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id);'))
    db.execute(text('ALTER TABLE stock_log ADD COLUMN IF NOT EXISTS expiry_ok BOOLEAN DEFAULT TRUE;'))
    db.execute(text('ALTER TABLE stock_log ADD COLUMN IF NOT EXISTS visual_ok BOOLEAN DEFAULT TRUE;'))
    db.commit()
    print('Columns added successfully')
except Exception as e:
    print(f'Error: {e}')
finally:
    db.close()
