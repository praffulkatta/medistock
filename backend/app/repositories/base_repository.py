from typing import TypeVar, Generic, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

T = TypeVar("T")

class BaseRepository(Generic[T]):
    def __init__(self, model: Any):
        self.model = model

    def get_by_id(self, db: Session, id: Any) -> Optional[T]:
        return db.query(self.model).filter(self.model.id == id).first()

    def get_all(
        self,
        db: Session,
        limit: int = 100,
        offset: int = 0,
        sort_by: Optional[str] = None,
        order: str = "asc"
    ) -> List[T]:
        query = db.query(self.model)
        if sort_by:
            column = getattr(self.model, sort_by, None)
            if column is not None:
                query = query.order_by(column.desc() if order == "desc" else column.asc())
        return query.offset(offset).limit(limit).all()

    def create(self, db: Session, obj_in: Any) -> T:
        db_obj = self.model(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, id: Any, obj_in: Any) -> Optional[T]:
        db_obj = self.get_by_id(db, id)
        if db_obj:
            update_data = obj_in.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_obj, field, value)
            db.commit()
            db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, id: Any) -> bool:
        db_obj = self.get_by_id(db, id)
        if db_obj:
            db.delete(db_obj)
            db.commit()
            return True
        return False
