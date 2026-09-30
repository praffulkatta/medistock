from sqlalchemy.orm import Session
from app.repositories.base_repository import BaseRepository
from app.models.inventory import Supplier

class SupplierRepository(BaseRepository[Supplier]):
    def __init__(self):
        super().__init__(Supplier)
