from typing import List, Optional
from sqlalchemy.orm import Session
from app.repositories.base_repository import BaseRepository
from app.models.catalog import Medicine

class MedicineRepository(BaseRepository[Medicine]):
    def __init__(self):
        super().__init__(Medicine)

    def get_by_category(
        self,
        db: Session,
        category_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Medicine]:
        return db.query(self.model).filter(
            self.model.category_id == category_id
        ).offset(offset).limit(limit).all()

    def search_medicines(self, db: Session, query: str) -> List[Medicine]:
        from app.models.inventory import MedicineBatch
        from sqlalchemy import or_
        return db.query(self.model).filter(
            or_(
                self.model.name.ilike(f"%{query}%"),
                self.model.generic_name.ilike(f"%{query}%"),
                self.model.manufacturer.ilike(f"%{query}%"),
                self.model.batches.any(MedicineBatch.batch_number.ilike(f"%{query}%"))
            )
        ).all()

