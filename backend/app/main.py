"""
Punto de entrada FastAPI — M3.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.database import engine, Base
from app.models import *  # noqa: F401 — registra todos los modelos
from app.api.v1.router import api_router
from app.middleware.rate_limit import limiter
from app.routers import admin_backups
from app.middleware.maintenance import MaintenanceMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Crear tablas al arrancar si no existen
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Gestión de Flujo de Caja",
    description="API REST — Delegaciones Bata y Malabo",
    version="1.0.0",
    docs_url="/api/docs" if settings.ENV == "development" else None,
    redoc_url="/api/redoc" if settings.ENV == "development" else None,
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
app.include_router(admin_backups.router, prefix="/api/v1")


@app.get("/api/health", tags=["Sistema"])
async def health_check():
    return {"status": "ok", "env": settings.ENV, "version": "1.0.0"}
