from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.sale_schema import SaleCreate, SaleRead
from app.services.sale_service import SaleService

router = APIRouter(prefix="/sales", tags=["Sales"])
service = SaleService()


@router.post("/", response_model=SaleRead, status_code=status.HTTP_201_CREATED)
def create_sale(data: SaleCreate, db: Session = Depends(get_db)):
    return service.create_sale(db, data)


@router.get("/{sale_id}", response_model=SaleRead)
def get_sale(sale_id: UUID, db: Session = Depends(get_db)):
    return service.get_sale(db, sale_id)
