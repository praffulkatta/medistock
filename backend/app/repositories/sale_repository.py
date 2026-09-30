from sqlalchemy.orm import Session
from app.repositories.base_repository import BaseRepository
from app.models.transactions import Sale

class SaleRepository(BaseRepository[Sale]):
    def __init__(self):
        super().__init__(Sale)
