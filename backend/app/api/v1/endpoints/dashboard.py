from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.inventory_service import InventoryService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])
service = InventoryService()


@router.get("/{pharmacy_id}")
def get_dashboard(pharmacy_id: UUID, db: Session = Depends(get_db)):
    return service.dashboard(db, pharmacy_id)
