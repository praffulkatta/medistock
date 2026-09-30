from sqlalchemy.orm import Session
from app.repositories.base_repository import BaseRepository
from app.models.transactions import Purchase

class PurchaseRepository(BaseRepository[Purchase]):
    def __init__(self):
        super().__init__(Purchase)
