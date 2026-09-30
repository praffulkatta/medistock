import logging

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.api.v1.endpoints import categories, dashboard, inventory, locations, medicines, pharmacies, sales, suppliers
from app.core.config import settings
from app.db.session import get_db

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    debug=settings.DEBUG.strip().lower() in {"1", "true", "yes", "on"},
)


@app.get("/")
def root():
    return {"service": "medistock-api", "docs": "/docs", "health": "/health"}


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "service": "medistock-api", "database": "connected"}
    except Exception as exc:
        logger.exception("Database health check failed")
        raise HTTPException(status_code=503, detail="Database connection unavailable") from exc


app.include_router(categories.router, prefix=settings.API_V1_STR)
app.include_router(suppliers.router, prefix=settings.API_V1_STR)
app.include_router(medicines.router, prefix=settings.API_V1_STR)
app.include_router(locations.router, prefix=settings.API_V1_STR)
app.include_router(sales.router, prefix=settings.API_V1_STR)
app.include_router(pharmacies.router, prefix=settings.API_V1_STR)
app.include_router(inventory.router, prefix=settings.API_V1_STR)
app.include_router(dashboard.router, prefix=settings.API_V1_STR)
