"""
Database session management - Supabase PostgreSQL optimized
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Supabase Pooler 최적화 연결 설정
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,       # 연결 전 SELECT 1 자동 확인
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,        # 30분마다 연결 재생성
    connect_args={
        "sslmode": "require",
        "connect_timeout": 10,
        "application_name": "schbc_bbms",
    }
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Database session dependency for FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_connection() -> bool:
    """
    DB 연결 테스트 (SELECT 1)
    Returns: True if connection successful
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            row = result.fetchone()
            if row and row[0] == 1:
                logger.info("✅ Supabase PostgreSQL 연결 성공")
                return True
    except Exception as e:
        logger.error(f"❌ DB 연결 실패: {e}")
        return False
    return False
