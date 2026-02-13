"""
SCHBC BBMS FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, inventory, config
from app.core.config import settings

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="순천향대학교 부천병원 혈액관리시스템 API"
)

# Configure CORS - Allow custom headers for tunnel bypass
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "Bypass-Tunnel-Reminder"],  # Allow custom header
    expose_headers=["*"]
)

# Include routers
app.include_router(auth.router)
app.include_router(inventory.router)
app.include_router(config.router, prefix="/api/config", tags=["Configuration"])


@app.get("/")
def root():
    """Root endpoint - API status"""
    return {
        "message": "SCHBC BBMS API is Running",
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION
    }
