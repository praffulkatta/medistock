from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.auth import Pharmacy
from app.models.catalog import Medicine
from app.models.inventory import MedicineBatch, Stock
from app.models.transactions import Sale, SaleItem, StockTransaction
from app.schemas.sale_schema import SaleCreate, SaleRead


class SaleService:
    def create_sale(self, db: Session, sale_in: SaleCreate) -> SaleRead:
        pharmacy = db.query(Pharmacy.id).filter(Pharmacy.id == sale_in.pharmacy_id).first()
        if pharmacy is None:
            raise HTTPException(status_code=404, detail="Pharmacy not found")

        requested: dict[UUID, Decimal] = {}
        for item in sale_in.items:
            requested[item.medicine_id] = requested.get(item.medicine_id, Decimal("0")) + item.quantity
        medicine_ids = list(requested)
        found_ids = {
            row[0] for row in db.query(Medicine.id).filter(
                Medicine.id.in_(medicine_ids), Medicine.pharmacy_id == sale_in.pharmacy_id
            ).all()
        }
        if found_ids != set(medicine_ids):
            raise HTTPException(status_code=404, detail="One or more medicines were not found for this pharmacy")

        today = date.today()
        sale = Sale(
            pharmacy_id=sale_in.pharmacy_id,
            sale_date=sale_in.sale_date or datetime.now(timezone.utc),
            total_amount=Decimal("0.00"),
        )
        db.add(sale)
        total_amount = Decimal("0.00")
        try:
            db.flush()
            for item in sale_in.items:
                remaining = item.quantity
                rows = db.query(Stock, MedicineBatch).join(
                    MedicineBatch, Stock.batch_id == MedicineBatch.id
                ).filter(
                    MedicineBatch.medicine_id == item.medicine_id,
                    MedicineBatch.expiry_date >= today,
                    Stock.quantity > 0,
                ).order_by(
                    MedicineBatch.expiry_date.asc(),
                    MedicineBatch.id.asc(),
                    Stock.location_id.asc(),
                ).with_for_update().all()

                for stock, batch in rows:
                    if remaining <= 0:
                        break
                    quantity = min(stock.quantity, remaining)
                    stock.quantity -= quantity
                    remaining -= quantity
                    total_amount += quantity * item.unit_price
                    db.add(SaleItem(
                        sale_id=sale.id,
                        batch_id=batch.id,
                        quantity=quantity,
                        unit_price=item.unit_price,
                    ))
                    db.add(StockTransaction(
                        batch_id=batch.id,
                        location_id=stock.location_id,
                        change_qty=-quantity,
                        reason="SALE",
                    ))
                if remaining > 0:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Insufficient unexpired stock for medicine {item.medicine_id}; short by {remaining}",
                    )
            sale.total_amount = total_amount
            db.commit()
        except Exception:
            db.rollback()
            raise

        db.refresh(sale)
        return SaleRead.model_validate(sale)

    @staticmethod
    def get_sale(db: Session, sale_id: UUID) -> SaleRead:
        sale = db.query(Sale).filter(Sale.id == sale_id).first()
        if sale is None:
            raise HTTPException(status_code=404, detail="Sale not found")
        return SaleRead.model_validate(sale)
