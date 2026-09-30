from sqlalchemy.orm import Session
from app.repositories.base_repository import BaseRepository
from app.models.transactions import StockTransaction

class TransactionRepository(BaseRepository[StockTransaction]):
    def __init__(self):
        super().__init__(StockTransaction)

    def log_transaction(self, db: Session, batch_id: str, location_id: str, change_qty: float, reason: str):
        transaction = StockTransaction(
            batch_id=batch_id,
            location_id=location_id,
            change_qty=change_qty,
            reason=reason
        )
        db.add(transaction)
        db.flush()
        return transaction
