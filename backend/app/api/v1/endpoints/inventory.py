from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.inventory import MedicineBatch
from app.models.catalog import Medicine
from app.models.transactions import Purchase
from app.schemas.inventory_schema import (
    BatchCreate,
    BatchRead,
    PurchaseCreate,
    PurchaseRead,
    ReceivedItemRead,
    StockTransactionRead,
    TransferCreate,
)
from app.services.inventory_service import InventoryService

router = APIRouter(tags=["Inventory"])
service = InventoryService()


@router.post("/batches", response_model=BatchRead, status_code=status.HTTP_201_CREATED)
def create_batch(data: BatchCreate, db: Session = Depends(get_db)):
    return service.create_batch(db, data)


@router.get("/batches", response_model=list[BatchRead])
def list_batches(
    pharmacy_id: UUID,
    medicine_id: UUID | None = None,
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(MedicineBatch).join(Medicine).filter(Medicine.pharmacy_id == pharmacy_id)
    if medicine_id:
        query = query.filter(MedicineBatch.medicine_id == medicine_id)
    return query.order_by(MedicineBatch.expiry_date, MedicineBatch.batch_number).offset(offset).limit(limit).all()


@router.post("/purchases", response_model=PurchaseRead, status_code=status.HTTP_201_CREATED)
def receive_purchase(data: PurchaseCreate, db: Session = Depends(get_db)):
    return service.receive_purchase(db, data)


@router.get("/purchases", response_model=list[PurchaseRead])
def list_purchases(
    pharmacy_id: UUID,
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    purchases = db.query(Purchase).filter(Purchase.pharmacy_id == pharmacy_id).order_by(
        Purchase.purchase_date.desc(), Purchase.id
    ).offset(offset).limit(limit).all()
    return [{
        "id": purchase.id,
        "pharmacy_id": purchase.pharmacy_id,
        "supplier_id": purchase.supplier_id,
        "purchase_date": purchase.purchase_date,
        "invoice_number": purchase.invoice_number,
        "total_amount": purchase.total_amount or 0,
        "items": [ReceivedItemRead(
            batch_id=item.batch_id,
            batch_number=item.batch.batch_number,
            quantity=item.quantity,
            location_id=item.location_id,
        ) for item in purchase.items],
    } for purchase in purchases]


@router.post("/stock/transfers", status_code=status.HTTP_200_OK)
def transfer_stock(data: TransferCreate, db: Session = Depends(get_db)):
    return service.transfer(db, data)


@router.get("/stock")
def list_stock(
    pharmacy_id: UUID,
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    return service.list_stock(db, pharmacy_id, limit, offset)


@router.get("/transactions", response_model=list[StockTransactionRead])
def list_transactions(
    pharmacy_id: UUID,
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    return service.list_transactions(db, pharmacy_id, limit, offset)
