"""
Database session management - Supabase PostgreSQL optimized
psycopg2-binary를 명시적 드라이버로 강제 지정
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


def _get_db_url() -> str:
    """
    DATABASE_URL에서 드라이버를 postgresql+psycopg2://로 강제 지정.
    Railway 환경에서 postgresql:// 또는 postgres:// 모두 처리.
    """
    url = settings.DATABASE_URL
    # postgres:// → postgresql:// (Heroku/Railway 호환)
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    # postgresql:// → postgresql+psycopg2:// (드라이버 명시)
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url


DB_URL = _get_db_url()

# Supabase Pooler 최적화 연결 설정
engine = create_engine(
    DB_URL,
    pool_pre_ping=True,        # 연결 전 SELECT 1 자동 확인
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,         # 30분마다 연결 재생성
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
