from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.inventory import MedicineBatch, Stock
from app.repositories.base_repository import BaseRepository


class StockRepository(BaseRepository[Stock]):
    def __init__(self):
        super().__init__(Stock)

    def get_total_stock(self, db: Session, batch_id: str):
        return db.query(func.coalesce(func.sum(Stock.quantity), 0)).filter(Stock.batch_id == batch_id).scalar()

    def get_stock_by_medicine(self, db: Session, medicine_id: str) -> list[Stock]:
        return db.query(Stock).join(MedicineBatch).filter(MedicineBatch.medicine_id == medicine_id).all()

    def get_stock_by_location(self, db: Session, location_id: str) -> list[Stock]:
        return db.query(Stock).filter(Stock.location_id == location_id).all()

    def update_quantity(self, db: Session, batch_id: str, location_id: str, change_qty):
        stock = db.query(Stock).filter(
            Stock.batch_id == batch_id,
            Stock.location_id == location_id,
        ).with_for_update().first()
        if stock is None:
            stock = Stock(batch_id=batch_id, location_id=location_id, quantity=0)
            db.add(stock)
        stock.quantity += change_qty
        if stock.quantity < 0:
            raise ValueError("Stock quantity cannot be negative")
        db.flush()
        return stock
