from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.supplier_schema import SupplierCreate, SupplierRead, SupplierUpdate
from app.services.supplier_service import SupplierService

router = APIRouter(prefix="/suppliers", tags=["Suppliers"])
service = SupplierService()


@router.post("/", response_model=SupplierRead, status_code=status.HTTP_201_CREATED)
def create_supplier(data: SupplierCreate, db: Session = Depends(get_db)):
    return service.create(db, data)


@router.get("/", response_model=list[SupplierRead])
def list_suppliers(
    pharmacy_id: UUID,
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    return service.list(db, pharmacy_id, limit, offset)


@router.get("/{supplier_id}", response_model=SupplierRead)
def get_supplier(supplier_id: UUID, db: Session = Depends(get_db)):
    return SupplierRead.model_validate(service.get(db, supplier_id))


@router.put("/{supplier_id}", response_model=SupplierRead)
def update_supplier(supplier_id: UUID, data: SupplierUpdate, db: Session = Depends(get_db)):
    return service.update(db, supplier_id, data)


@router.delete("/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_supplier(supplier_id: UUID, db: Session = Depends(get_db)):
    service.delete(db, supplier_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
