from sqlalchemy.orm import Session
from app.repositories.base_repository import BaseRepository
from app.models.inventory import MedicineBatch

class BatchRepository(BaseRepository[MedicineBatch]):
    def __init__(self):
        super().__init__(MedicineBatch)

    def get_by_batch_number(self, db: Session, medicine_id: str, batch_number: str) -> MedicineBatch | None:
        return db.query(self.model).filter(
            self.model.medicine_id == medicine_id,
            self.model.batch_number == batch_number
        ).first()
