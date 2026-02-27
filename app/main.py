"""
SCHBC BBMS FastAPI Application - Standalone (Railway 직접 서빙)
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import logging

from app.api import auth, inventory, config, users, analytics
from app.api import admin as admin_api
from app.api import alert_email as alert_email_api
from app.core.config import settings
from app.database.database import test_connection

logger = logging.getLogger(__name__)

templates = Jinja2Templates(directory="templates")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 SCHBC BBMS 시작 중...")
    ok = test_connection()
    if ok:
        logger.info("✅ Supabase PostgreSQL 연결 성공")
        try:
            from sqlalchemy import text
            from app.database.database import SessionLocal, engine
            from app.database.models import Base
            db = SessionLocal()
            # 자동으로 누락된 테이블(ex: InboundHistory) 생성
            Base.metadata.create_all(bind=engine)
            db.execute(text("ALTER TABLE stock_log ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id);"))
            db.execute(text("ALTER TABLE stock_log ADD COLUMN IF NOT EXISTS expiry_ok BOOLEAN DEFAULT TRUE;"))
            db.execute(text("ALTER TABLE stock_log ADD COLUMN IF NOT EXISTS visual_ok BOOLEAN DEFAULT TRUE;"))
            db.execute(text("ALTER TABLE master_config ADD COLUMN IF NOT EXISTS danger_factor FLOAT;"))
            db.commit()
            db.close()
            logger.info("✅ DB 스키마 마이그레이션 확인 (stock_log 확장 필드 및 신규 테이블 확인)")
        except Exception as e:
            logger.error(f"⚠️ DB 스키마 자동 패치 실패: {e}")
    else:
        logger.warning("⚠️ DB 연결 실패 - DATABASE_URL 확인 필요")
    yield
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

# Static files (CSS, JS, images 등 향후 사용)
app.mount("/static", StaticFiles(directory="static"), name="static")

# API 라우터
app.include_router(auth.router)
app.include_router(inventory.router)
app.include_router(config.router, prefix="/api/config", tags=["Configuration"])
app.include_router(users.router)
app.include_router(analytics.router)
app.include_router(admin_api.router)
app.include_router(alert_email_api.router, tags=["Alert Emails"])


@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    """메인 화면 - index.html 서빙"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/analytics", response_class=HTMLResponse)
def page_analytics(request: Request):
    """분석 대시보드 화면 - analytics.html 서빙"""
    return templates.TemplateResponse("analytics.html", {"request": request})


@app.get("/health")
def health_check():
    db_ok = test_connection()
    return {
        "status": "healthy" if db_ok else "degraded",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "database": "connected" if db_ok else "disconnected"
    }
