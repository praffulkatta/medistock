from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.catalog import Medicine
from app.models.inventory import Location, MedicineBatch, Stock, Supplier
from app.models.transactions import Purchase, PurchaseItem, Sale, StockTransaction
from app.schemas.inventory_schema import BatchCreate, BatchRead, PurchaseCreate, TransferCreate


class InventoryService:
    @staticmethod
    def _validate_location(db: Session, pharmacy_id: UUID, location_id: UUID) -> Location:
        location = db.query(Location).filter(
            Location.id == location_id, Location.pharmacy_id == pharmacy_id
        ).first()
        if location is None:
            raise HTTPException(status_code=404, detail="Location not found for this pharmacy")
        if location.level != 4 or location.type != "Bin":
            raise HTTPException(status_code=400, detail="Stock must be assigned to a Bin location")
        return location

    def create_batch(self, db: Session, data: BatchCreate) -> BatchRead:
        medicine = db.query(Medicine).filter(Medicine.id == data.medicine_id).first()
        if medicine is None:
            raise HTTPException(status_code=404, detail="Medicine not found")
        if db.query(Supplier).filter(
            Supplier.id == data.supplier_id, Supplier.pharmacy_id == medicine.pharmacy_id
        ).first() is None:
            raise HTTPException(status_code=404, detail="Supplier not found for this pharmacy")
        if data.manufacturing_date and data.manufacturing_date >= data.expiry_date:
            raise HTTPException(status_code=400, detail="Manufacturing date must precede expiry date")
        if db.query(MedicineBatch).filter(
            MedicineBatch.medicine_id == data.medicine_id,
            MedicineBatch.batch_number == data.batch_number,
        ).first():
            raise HTTPException(status_code=409, detail="Batch number already exists for this medicine")
        batch = MedicineBatch(**data.model_dump())
        db.add(batch)
        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(status_code=409, detail="Batch number already exists for this medicine") from exc
        db.refresh(batch)
        return BatchRead.model_validate(batch)

    def receive_purchase(self, db: Session, data: PurchaseCreate) -> dict:
        supplier = db.query(Supplier).filter(
            Supplier.id == data.supplier_id,
            Supplier.pharmacy_id == data.pharmacy_id,
        ).first()
        if supplier is None:
            raise HTTPException(status_code=404, detail="Supplier not found for this pharmacy")

        purchase_date = data.purchase_date or datetime.now(timezone.utc)
        purchase = Purchase(
            pharmacy_id=data.pharmacy_id,
            supplier_id=data.supplier_id,
            purchase_date=purchase_date,
            invoice_number=data.invoice_number,
            total_amount=Decimal("0"),
        )
        db.add(purchase)
        received: list[dict] = []
        total = Decimal("0")
        try:
            db.flush()
            for item in data.items:
                medicine = db.query(Medicine).filter(
                    Medicine.id == item.medicine_id,
                    Medicine.pharmacy_id == data.pharmacy_id,
                ).first()
                if medicine is None:
                    raise HTTPException(status_code=404, detail="Medicine not found for this pharmacy")
                location = self._validate_location(db, data.pharmacy_id, item.location_id)
                if item.expiry_date <= date.today():
                    raise HTTPException(status_code=400, detail="Cannot receive a batch that is already expired")
                if item.manufacturing_date and item.manufacturing_date >= item.expiry_date:
                    raise HTTPException(status_code=400, detail="Manufacturing date must precede expiry date")

                batch = db.query(MedicineBatch).filter(
                    MedicineBatch.medicine_id == medicine.id,
                    MedicineBatch.batch_number == item.batch_number,
                ).with_for_update().first()
                if batch is None:
                    batch = MedicineBatch(
                        medicine_id=medicine.id,
                        supplier_id=supplier.id,
                        batch_number=item.batch_number,
                        manufacturing_date=item.manufacturing_date,
                        expiry_date=item.expiry_date,
                        cost_price=item.cost_price,
                        selling_price=item.selling_price,
                    )
                    db.add(batch)
                    db.flush()
                else:
                    if batch.expiry_date != item.expiry_date or batch.supplier_id != supplier.id:
                        raise HTTPException(status_code=409, detail="Existing batch details do not match this purchase")
                    batch.cost_price = item.cost_price
                    batch.selling_price = item.selling_price

                stock = db.query(Stock).filter(
                    Stock.batch_id == batch.id, Stock.location_id == location.id
                ).with_for_update().first()
                if stock is None:
                    stock = Stock(batch_id=batch.id, location_id=location.id, quantity=Decimal("0"))
                    db.add(stock)
                    db.flush()
                stock.quantity += item.quantity
                db.add(PurchaseItem(
                    purchase_id=purchase.id,
                    batch_id=batch.id,
                    location_id=location.id,
                    quantity=item.quantity,
                ))
                db.add(StockTransaction(
                    batch_id=batch.id, location_id=location.id,
                    change_qty=item.quantity, reason="PURCHASE",
                ))
                total += item.quantity * item.cost_price
                received.append({
                    "batch_id": batch.id,
                    "batch_number": batch.batch_number,
                    "quantity": item.quantity,
                    "location_id": location.id,
                })
            purchase.total_amount = total
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(status_code=409, detail="The purchase conflicts with an existing batch or stock row") from exc
        except Exception:
            db.rollback()
            raise

        return {
            "id": purchase.id,
            "pharmacy_id": purchase.pharmacy_id,
            "supplier_id": purchase.supplier_id,
            "purchase_date": purchase.purchase_date,
            "invoice_number": purchase.invoice_number,
            "total_amount": purchase.total_amount,
            "items": received,
        }

    def transfer(self, db: Session, data: TransferCreate) -> dict:
        if data.source_location_id == data.destination_location_id:
            raise HTTPException(status_code=400, detail="Source and destination must be different")
        batch = db.query(MedicineBatch).join(Medicine).filter(
            MedicineBatch.id == data.batch_id, Medicine.pharmacy_id == data.pharmacy_id
        ).first()
        if batch is None:
            raise HTTPException(status_code=404, detail="Batch not found for this pharmacy")
        source_location = self._validate_location(db, data.pharmacy_id, data.source_location_id)
        destination_location = self._validate_location(db, data.pharmacy_id, data.destination_location_id)
        try:
            source = db.query(Stock).filter(
                Stock.batch_id == batch.id, Stock.location_id == source_location.id
            ).with_for_update().first()
            if source is None or source.quantity < data.quantity:
                available = source.quantity if source else Decimal("0")
                raise HTTPException(status_code=400, detail=f"Insufficient stock at source. Available: {available}")
            destination = db.query(Stock).filter(
                Stock.batch_id == batch.id, Stock.location_id == destination_location.id
            ).with_for_update().first()
            if destination is None:
                destination = Stock(batch_id=batch.id, location_id=destination_location.id, quantity=Decimal("0"))
                db.add(destination)
                db.flush()
            source.quantity -= data.quantity
            destination.quantity += data.quantity
            db.add_all([
                StockTransaction(batch_id=batch.id, location_id=source_location.id,
                                 change_qty=-data.quantity, reason="TRANSFER_OUT"),
                StockTransaction(batch_id=batch.id, location_id=destination_location.id,
                                 change_qty=data.quantity, reason="TRANSFER_IN"),
            ])
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(status_code=409, detail="The transfer conflicts with an existing stock row") from exc
        except Exception:
            db.rollback()
            raise
        return {
            "batch_id": batch.id,
            "source_location_id": source_location.id,
            "source_quantity": source.quantity,
            "destination_location_id": destination_location.id,
            "destination_quantity": destination.quantity,
            "transferred_quantity": data.quantity,
        }

    def dashboard(self, db: Session, pharmacy_id: UUID) -> dict:
        today = date.today()
        expiry_cutoff = today + timedelta(days=30)
        totals = db.query(
            Medicine.id.label("medicine_id"),
            func.coalesce(func.sum(Stock.quantity), 0).label("quantity"),
        ).outerjoin(MedicineBatch, MedicineBatch.medicine_id == Medicine.id).outerjoin(
            Stock, Stock.batch_id == MedicineBatch.id
        ).filter(Medicine.pharmacy_id == pharmacy_id).group_by(Medicine.id).subquery()
        low_stock = db.query(func.count(Medicine.id)).join(
            totals, totals.c.medicine_id == Medicine.id
        ).filter(Medicine.pharmacy_id == pharmacy_id, totals.c.quantity <= Medicine.min_stock_level).scalar() or 0
        expired_quantity = db.query(func.coalesce(func.sum(Stock.quantity), 0)).join(
            MedicineBatch, Stock.batch_id == MedicineBatch.id
        ).join(Medicine, MedicineBatch.medicine_id == Medicine.id).filter(
            Medicine.pharmacy_id == pharmacy_id, MedicineBatch.expiry_date < today, Stock.quantity > 0
        ).scalar() or Decimal("0")
        expiring_quantity = db.query(func.coalesce(func.sum(Stock.quantity), 0)).join(
            MedicineBatch, Stock.batch_id == MedicineBatch.id
        ).join(Medicine, MedicineBatch.medicine_id == Medicine.id).filter(
            Medicine.pharmacy_id == pharmacy_id,
            MedicineBatch.expiry_date >= today,
            MedicineBatch.expiry_date <= expiry_cutoff,
            Stock.quantity > 0,
        ).scalar() or Decimal("0")
        now = datetime.now(timezone.utc)
        start_of_day = datetime.combine(today, time.min, tzinfo=timezone.utc)
        sales_today = db.query(func.coalesce(func.sum(Sale.total_amount), 0)).filter(
            Sale.pharmacy_id == pharmacy_id,
            Sale.sale_date >= start_of_day,
            Sale.sale_date <= now,
        ).scalar() or Decimal("0")
        medicine_count = db.query(func.count(Medicine.id)).filter(Medicine.pharmacy_id == pharmacy_id).scalar() or 0
        total_stock = db.query(func.coalesce(func.sum(Stock.quantity), 0)).join(
            MedicineBatch, Stock.batch_id == MedicineBatch.id
        ).join(Medicine, MedicineBatch.medicine_id == Medicine.id).filter(Medicine.pharmacy_id == pharmacy_id).scalar() or Decimal("0")
        low_stock_rows = db.query(
            Medicine.id, Medicine.name, totals.c.quantity, Medicine.min_stock_level
        ).join(totals, totals.c.medicine_id == Medicine.id).filter(
            Medicine.pharmacy_id == pharmacy_id,
            totals.c.quantity <= Medicine.min_stock_level,
        ).order_by(Medicine.name).limit(10).all()
        expiring_rows = db.query(
            MedicineBatch.id, Medicine.name, MedicineBatch.batch_number,
            MedicineBatch.expiry_date, func.sum(Stock.quantity).label("quantity"),
        ).join(Medicine, MedicineBatch.medicine_id == Medicine.id).join(
            Stock, Stock.batch_id == MedicineBatch.id
        ).filter(
            Medicine.pharmacy_id == pharmacy_id,
            MedicineBatch.expiry_date <= expiry_cutoff,
            Stock.quantity > 0,
        ).group_by(MedicineBatch.id, Medicine.id).order_by(
            MedicineBatch.expiry_date, Medicine.name
        ).limit(10).all()
        recent_rows = db.query(StockTransaction, Medicine, MedicineBatch, Location).join(
            MedicineBatch, StockTransaction.batch_id == MedicineBatch.id
        ).join(Medicine, MedicineBatch.medicine_id == Medicine.id).join(
            Location, StockTransaction.location_id == Location.id
        ).filter(
            Medicine.pharmacy_id == pharmacy_id
        ).order_by(StockTransaction.created_at.desc()).limit(10).all()
        return {
            "medicine_count": medicine_count,
            "total_stock": total_stock,
            "low_stock_count": low_stock,
            "expiring_soon_quantity": expiring_quantity,
            "expired_quantity": expired_quantity,
            "sales_today": sales_today,
            "low_stock_items": [{
                "medicine_id": row.id,
                "name": row.name,
                "quantity": row.quantity,
                "minimum": row.min_stock_level,
            } for row in low_stock_rows],
            "expiry_alerts": [{
                "batch_id": row.id,
                "medicine_name": row.name,
                "batch_number": row.batch_number,
                "expiry_date": row.expiry_date,
                "quantity": row.quantity,
                "status": "EXPIRED" if row.expiry_date < today else "EXPIRING_SOON",
            } for row in expiring_rows],
            "recent_movements": [{
                "id": transaction.id,
                "medicine_name": medicine.name,
                "batch_number": batch.batch_number,
                "location_name": location.name,
                "change_qty": transaction.change_qty,
                "reason": transaction.reason,
                "created_at": transaction.created_at,
            } for transaction, medicine, batch, location in recent_rows],
        }

    def list_stock(self, db: Session, pharmacy_id: UUID, limit: int, offset: int) -> list[dict]:
        rows = db.query(Stock, MedicineBatch, Medicine, Location).join(
            MedicineBatch, Stock.batch_id == MedicineBatch.id
        ).join(Medicine, MedicineBatch.medicine_id == Medicine.id).join(
            Location, Stock.location_id == Location.id
        ).filter(Medicine.pharmacy_id == pharmacy_id).order_by(
            Medicine.name, MedicineBatch.expiry_date, Location.name
        ).offset(offset).limit(limit).all()
        return [{
            "medicine_id": medicine.id,
            "medicine_name": medicine.name,
            "batch_id": batch.id,
            "batch_number": batch.batch_number,
            "expiry_date": batch.expiry_date,
            "expired": batch.expiry_date < date.today(),
            "location_id": location.id,
            "location_name": location.name,
            "quantity": stock.quantity,
        } for stock, batch, medicine, location in rows]

    def list_transactions(self, db: Session, pharmacy_id: UUID, limit: int, offset: int) -> list[dict]:
        rows = db.query(StockTransaction, Medicine, MedicineBatch, Location).join(
            MedicineBatch, StockTransaction.batch_id == MedicineBatch.id
        ).join(Medicine, MedicineBatch.medicine_id == Medicine.id).join(
            Location, StockTransaction.location_id == Location.id
        ).filter(
            Medicine.pharmacy_id == pharmacy_id
        ).order_by(StockTransaction.created_at.desc()).offset(offset).limit(limit).all()
        return [{
            "id": transaction.id,
            "batch_id": transaction.batch_id,
            "location_id": transaction.location_id,
            "change_qty": transaction.change_qty,
            "reason": transaction.reason,
            "created_at": transaction.created_at,
            "medicine_name": medicine.name,
            "batch_number": batch.batch_number,
            "location_name": location.name,
        } for transaction, medicine, batch, location in rows]
