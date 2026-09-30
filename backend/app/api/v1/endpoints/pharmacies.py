from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.pharmacy_schema import PharmacyCreate, PharmacyRead
from app.services.pharmacy_service import PharmacyService

router = APIRouter(prefix="/pharmacies", tags=["Pharmacies"])
service = PharmacyService()


@router.get("/", response_model=list[PharmacyRead])
def list_pharmacies(
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    return service.list(db, limit, offset)


@router.post("/", response_model=PharmacyRead, status_code=status.HTTP_201_CREATED)
def create_pharmacy(data: PharmacyCreate, db: Session = Depends(get_db)):
    return service.create(db, data)
