import os
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Set environment variable mock for testing if needed
# os.environ["DATABASE_URL"] = "your_actual_url_here"

from app.database.database import get_db, engine
from app.database.models import StockLog, InboundHistory

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

def main():
    try:
        # Check current row count
        count = db.query(InboundHistory).count()
        print(f"Current InboundHistory rows: {count}")
        
        if count == 0:
            print("Backfilling InboundHistory from StockLog ('엑셀 일괄 업로드' remarks)...")
            logs = db.query(StockLog).filter(StockLog.remark.like('%엑셀%'), StockLog.in_qty > 0).all()
            print(f"Found {len(logs)} excel upload logs to backfill.")
            
            for log in logs:
                ih = InboundHistory(
                    receive_date=log.log_date.date(),
                    blood_type=log.blood_type,
                    prep_id=log.prep_id,
                    qty=log.in_qty,
                    created_at=log.created_at
                )
                db.add(ih)
            db.commit()
            print("Backfill complete!")
            print(f"New InboundHistory rows: {db.query(InboundHistory).count()}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
