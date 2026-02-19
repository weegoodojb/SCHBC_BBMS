"""
SCHBC BBMS FastAPI Application
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.api import auth, inventory, config
from app.core.config import settings
from app.database.database import test_connection

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작/종료 시 실행"""
    # Startup: DB 연결 테스트
    logger.info("🚀 SCHBC BBMS 시작 중...")
    ok = test_connection()
    if ok:
        logger.info("✅ Supabase PostgreSQL 연결 성공 (SELECT 1 확인)")
    else:
        logger.warning("⚠️ DB 연결 실패 - 환경변수 DATABASE_URL 확인 필요")
    yield
    # Shutdown
    logger.info("👋 SCHBC BBMS 종료")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="순천향대학교 부천병원 혈액관리시스템 API",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(inventory.router)
app.include_router(config.router, prefix="/api/config", tags=["Configuration"])


@app.get("/")
def root():
    return {
        "message": "SCHBC BBMS API is Running",
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
def health_check():
    db_ok = test_connection()
    return {
        "status": "healthy" if db_ok else "degraded",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "database": "connected" if db_ok else "disconnected"
    }
