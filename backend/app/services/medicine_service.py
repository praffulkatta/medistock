from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.catalog import Category, Medicine
from app.models.inventory import Location, MedicineBatch, Stock
from app.schemas.medicine_schema import MedicineCreate, MedicineRead, MedicineUpdate


class MedicineService:
    def create(self, db: Session, data: MedicineCreate) -> MedicineRead:
        category = db.query(Category).filter(
            Category.id == data.category_id,
            Category.pharmacy_id == data.pharmacy_id,
        ).first()
        if category is None:
            raise HTTPException(status_code=404, detail="Category not found for this pharmacy")
        duplicate = db.query(Medicine.id).filter(
            Medicine.pharmacy_id == data.pharmacy_id,
            func.lower(Medicine.name) == data.name.strip().lower(),
            func.coalesce(Medicine.strength, "") == (data.strength or ""),
        ).first()
        if duplicate:
            raise HTTPException(status_code=409, detail="Medicine with this name and strength already exists")
        medicine = Medicine(**data.model_dump())
        db.add(medicine)
        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(status_code=409, detail="A medicine with this name and strength already exists") from exc
        db.refresh(medicine)
        return MedicineRead.model_validate(medicine)

    def get(self, db: Session, medicine_id: UUID) -> Medicine:
        medicine = db.query(Medicine).filter(Medicine.id == medicine_id).first()
        if medicine is None:
            raise HTTPException(status_code=404, detail="Medicine not found")
        return medicine

    def list(
        self, db: Session, pharmacy_id: UUID, limit: int, offset: int,
        category_id: UUID | None = None,
    ) -> list[MedicineRead]:
        query = db.query(Medicine).filter(Medicine.pharmacy_id == pharmacy_id)
        if category_id:
            query = query.filter(Medicine.category_id == category_id)
        return [MedicineRead.model_validate(item) for item in query.order_by(Medicine.name).offset(offset).limit(limit).all()]

    def update(self, db: Session, medicine_id: UUID, data: MedicineUpdate) -> MedicineRead:
        medicine = self.get(db, medicine_id)
        updates = data.model_dump(exclude_unset=True)
        if "category_id" in updates:
            category = db.query(Category).filter(
                Category.id == updates["category_id"], Category.pharmacy_id == medicine.pharmacy_id
            ).first()
            if category is None:
                raise HTTPException(status_code=404, detail="Category not found for this pharmacy")
        if "name" in updates or "strength" in updates:
            name = updates.get("name", medicine.name).strip()
            strength = updates.get("strength", medicine.strength) or ""
            duplicate = db.query(Medicine.id).filter(
                Medicine.pharmacy_id == medicine.pharmacy_id,
                func.lower(Medicine.name) == name.lower(),
                func.coalesce(Medicine.strength, "") == strength,
                Medicine.id != medicine.id,
            ).first()
            if duplicate:
                raise HTTPException(status_code=409, detail="Medicine with this name and strength already exists")
        for key, value in updates.items():
            setattr(medicine, key, value)
        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(status_code=409, detail="A medicine with this name and strength already exists") from exc
        db.refresh(medicine)
        return MedicineRead.model_validate(medicine)

    def delete(self, db: Session, medicine_id: UUID) -> None:
        medicine = self.get(db, medicine_id)
        db.delete(medicine)
        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(status_code=409, detail="Medicine has batches or stock and cannot be deleted") from exc

    def search(
        self, db: Session, pharmacy_id: UUID, query_text: str, limit: int, offset: int,
    ) -> dict:
        escaped = query_text.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        term = f"%{escaped}%"
        matching_batch = Medicine.batches.any(MedicineBatch.batch_number.ilike(term, escape="\\"))
        query = db.query(Medicine).filter(
            Medicine.pharmacy_id == pharmacy_id,
            or_(
                Medicine.name.ilike(term, escape="\\"),
                Medicine.generic_name.ilike(term, escape="\\"),
                Medicine.manufacturer.ilike(term, escape="\\"),
                matching_batch,
            ),
        )
        total = query.count()
        medicines = query.order_by(Medicine.name, Medicine.id).offset(offset).limit(limit).all()
        if not medicines:
            return {"results": [], "total": total, "limit": limit, "offset": offset}

        medicine_ids = [medicine.id for medicine in medicines]
        batches = db.query(MedicineBatch).filter(
            MedicineBatch.medicine_id.in_(medicine_ids)
        ).order_by(MedicineBatch.expiry_date, MedicineBatch.batch_number).all()
        stocks = db.query(Stock, MedicineBatch).join(
            MedicineBatch, Stock.batch_id == MedicineBatch.id
        ).filter(
            MedicineBatch.medicine_id.in_(medicine_ids), Stock.quantity > 0
        ).all()
        locations = db.query(Location).filter(Location.pharmacy_id == pharmacy_id).all()
        location_by_id = {location.id: location for location in locations}

        batches_by_medicine: dict[UUID, list[dict]] = {}
        batch_data: dict[UUID, dict] = {}
        today = date.today()
        for batch in batches:
            if batch.expiry_date < today:
                expiry_status = "EXPIRED"
            elif batch.expiry_date <= today + timedelta(days=30):
                expiry_status = "EXPIRING_SOON"
            else:
                expiry_status = "SAFE"
            entry = {
                "batch_id": batch.id,
                "batch_number": batch.batch_number,
                "expiry_date": batch.expiry_date,
                "expiry_status": expiry_status,
                "quantity": Decimal("0"),
                "locations": [],
            }
            batch_data[batch.id] = entry
            batches_by_medicine.setdefault(batch.medicine_id, []).append(entry)

        totals: dict[UUID, Decimal] = {medicine_id: Decimal("0") for medicine_id in medicine_ids}
        for stock, batch in stocks:
            entry = batch_data[batch.id]
            entry["quantity"] += stock.quantity
            totals[batch.medicine_id] += stock.quantity
            path: list[str] = []
            current = location_by_id.get(stock.location_id)
            seen: set[UUID] = set()
            while current is not None and current.id not in seen:
                seen.add(current.id)
                path.append(current.name)
                current = location_by_id.get(current.parent_id) if current.parent_id else None
            path.reverse()
            entry["locations"].append({
                "location_id": stock.location_id,
                "location_path": path,
                "quantity": stock.quantity,
            })

        results = [{
            "medicine_id": medicine.id,
            "name": medicine.name,
            "generic_name": medicine.generic_name,
            "manufacturer": medicine.manufacturer,
            "min_stock_level": medicine.min_stock_level,
            "total_quantity": totals[medicine.id],
            "batches": batches_by_medicine.get(medicine.id, []),
        } for medicine in medicines]
        return {"results": results, "total": total, "limit": limit, "offset": offset}
