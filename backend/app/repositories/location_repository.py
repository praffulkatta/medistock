from sqlalchemy.orm import Session
from app.repositories.base_repository import BaseRepository
from app.models.inventory import Location

class LocationRepository(BaseRepository[Location]):
    def __init__(self):
        super().__init__(Location)

    def get_ancestors(self, db: Session, location_id: str) -> list:
        """Recursively fetch ancestors from Bin up to Block."""
        ancestors = []
        current_id = location_id

        while current_id:
            loc = self.get_by_id(db, current_id)
            if not loc:
                break
            ancestors.append(loc)
            current_id = loc.parent_id

        return ancestors

    def has_children(self, db: Session, location_id: str) -> bool:
        """Check if a location has any child locations."""
        return db.query(Location).filter(Location.parent_id == location_id).first() is not None
