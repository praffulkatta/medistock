from sqlalchemy.orm import Session
from app.repositories.base_repository import BaseRepository
from app.models.catalog import Category

class CategoryRepository(BaseRepository[Category]):
    def __init__(self):
        super().__init__(Category)
