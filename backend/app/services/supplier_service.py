from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.auth import Pharmacy
from app.models.inventory import Supplier
from app.schemas.supplier_schema import SupplierCreate, SupplierRead, SupplierUpdate


class SupplierService:
    def create(self, db: Session, data: SupplierCreate) -> SupplierRead:
        if db.query(Pharmacy.id).filter(Pharmacy.id == data.pharmacy_id).first() is None:
            raise HTTPException(status_code=404, detail="Pharmacy not found")
        if db.query(Supplier.id).filter(
            Supplier.pharmacy_id == data.pharmacy_id,
            func.lower(Supplier.name) == data.name.strip().lower(),
        ).first():
            raise HTTPException(status_code=409, detail="Supplier already exists in this pharmacy")
        supplier = Supplier(**data.model_dump(exclude={"name"}), name=data.name.strip())
        db.add(supplier)
        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(status_code=409, detail="Supplier already exists in this pharmacy") from exc
        db.refresh(supplier)
        return SupplierRead.model_validate(supplier)

    @staticmethod
    def get(db: Session, supplier_id: UUID) -> Supplier:
        supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
        if supplier is None:
            raise HTTPException(status_code=404, detail="Supplier not found")
        return supplier

    def list(self, db: Session, pharmacy_id: UUID, limit: int, offset: int) -> list[SupplierRead]:
        suppliers = db.query(Supplier).filter(Supplier.pharmacy_id == pharmacy_id).order_by(
            Supplier.name, Supplier.id
        ).offset(offset).limit(limit).all()
        return [SupplierRead.model_validate(supplier) for supplier in suppliers]

    def update(self, db: Session, supplier_id: UUID, data: SupplierUpdate) -> SupplierRead:
        supplier = self.get(db, supplier_id)
        updates = data.model_dump(exclude_unset=True)
        if "name" in updates:
            updates["name"] = updates["name"].strip()
            duplicate = db.query(Supplier.id).filter(
                Supplier.pharmacy_id == supplier.pharmacy_id,
                func.lower(Supplier.name) == updates["name"].lower(),
                Supplier.id != supplier.id,
            ).first()
            if duplicate:
                raise HTTPException(status_code=409, detail="Supplier already exists in this pharmacy")
        for key, value in updates.items():
            setattr(supplier, key, value)
        db.commit()
        db.refresh(supplier)
        return SupplierRead.model_validate(supplier)

    def delete(self, db: Session, supplier_id: UUID) -> None:
        supplier = self.get(db, supplier_id)
        db.delete(supplier)
        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(status_code=409, detail="Supplier is referenced by batches and cannot be deleted") from exc
