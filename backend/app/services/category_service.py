from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.auth import Pharmacy
from app.models.catalog import Category
from app.schemas.category_schema import CategoryCreate, CategoryRead, CategoryUpdate


class CategoryService:
    def create(self, db: Session, data: CategoryCreate) -> CategoryRead:
        if db.query(Pharmacy.id).filter(Pharmacy.id == data.pharmacy_id).first() is None:
            raise HTTPException(status_code=404, detail="Pharmacy not found")
        if db.query(Category.id).filter(
            Category.pharmacy_id == data.pharmacy_id,
            func.lower(Category.name) == data.name.strip().lower(),
        ).first():
            raise HTTPException(status_code=409, detail="Category already exists in this pharmacy")
        category = Category(pharmacy_id=data.pharmacy_id, name=data.name.strip())
        db.add(category)
        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(status_code=409, detail="Category already exists in this pharmacy") from exc
        db.refresh(category)
        return CategoryRead.model_validate(category)

    @staticmethod
    def get(db: Session, category_id: UUID) -> Category:
        category = db.query(Category).filter(Category.id == category_id).first()
        if category is None:
            raise HTTPException(status_code=404, detail="Category not found")
        return category

    def list(self, db: Session, pharmacy_id: UUID, limit: int, offset: int) -> list[CategoryRead]:
        categories = db.query(Category).filter(Category.pharmacy_id == pharmacy_id).order_by(
            Category.name, Category.id
        ).offset(offset).limit(limit).all()
        return [CategoryRead.model_validate(category) for category in categories]

    def update(self, db: Session, category_id: UUID, data: CategoryUpdate) -> CategoryRead:
        category = self.get(db, category_id)
        updates = data.model_dump(exclude_unset=True)
        if "name" in updates:
            updates["name"] = updates["name"].strip()
            duplicate = db.query(Category.id).filter(
                Category.pharmacy_id == category.pharmacy_id,
                func.lower(Category.name) == updates["name"].lower(),
                Category.id != category.id,
            ).first()
            if duplicate:
                raise HTTPException(status_code=409, detail="Category already exists in this pharmacy")
        for key, value in updates.items():
            setattr(category, key, value)
        db.commit()
        db.refresh(category)
        return CategoryRead.model_validate(category)

    def delete(self, db: Session, category_id: UUID) -> None:
        category = self.get(db, category_id)
        db.delete(category)
        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(status_code=409, detail="Category is used by medicines and cannot be deleted") from exc
