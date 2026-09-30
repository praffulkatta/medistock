from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.inventory import Location, Stock
from app.schemas.location_schema import (
    LocationCreate,
    LocationHierarchyRead,
    LocationRead,
    LocationUpdate,
)


class LocationService:
    _LEVELS = {"Block": 1, "Rack": 2, "Shelf": 3, "Bin": 4}

    @classmethod
    def _validate_type_level(cls, location_type: str, level: int) -> None:
        if cls._LEVELS.get(location_type) != level:
            raise HTTPException(status_code=400, detail="Location type and hierarchy level do not match")

    def create(self, db: Session, data: LocationCreate) -> LocationRead:
        self._validate_type_level(data.type, data.level)
        if data.parent_id:
            parent = db.query(Location).filter(
                Location.id == data.parent_id, Location.pharmacy_id == data.pharmacy_id
            ).first()
            if parent is None:
                raise HTTPException(status_code=404, detail="Parent location not found for this pharmacy")
            if data.level != parent.level + 1:
                raise HTTPException(status_code=400, detail="Child location must be exactly one level below its parent")
        elif data.level != 1:
            raise HTTPException(status_code=400, detail="Root locations must be Blocks at level 1")

        location = Location(**data.model_dump())
        db.add(location)
        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(status_code=400, detail="Invalid location hierarchy") from exc
        db.refresh(location)
        return LocationRead.model_validate(location)

    @staticmethod
    def get(db: Session, location_id: UUID) -> Location:
        location = db.query(Location).filter(Location.id == location_id).first()
        if location is None:
            raise HTTPException(status_code=404, detail="Location not found")
        return location

    def list(self, db: Session, pharmacy_id: UUID, limit: int, offset: int) -> list[LocationRead]:
        locations = db.query(Location).filter(Location.pharmacy_id == pharmacy_id).order_by(
            Location.level, Location.name, Location.id
        ).offset(offset).limit(limit).all()
        return [LocationRead.model_validate(location) for location in locations]

    def update(self, db: Session, location_id: UUID, data: LocationUpdate) -> LocationRead:
        location = self.get(db, location_id)
        updates = data.model_dump(exclude_unset=True)
        new_type = updates.get("type", location.type)
        self._validate_type_level(new_type, location.level)
        if "parent_id" in updates:
            parent_id = updates["parent_id"]
            if parent_id is None:
                if location.level != 1:
                    raise HTTPException(status_code=400, detail="Only a Block can be a root location")
            else:
                if parent_id == location.id:
                    raise HTTPException(status_code=400, detail="A location cannot be its own parent")
                parent = db.query(Location).filter(
                    Location.id == parent_id, Location.pharmacy_id == location.pharmacy_id
                ).first()
                if parent is None:
                    raise HTTPException(status_code=404, detail="Parent location not found for this pharmacy")
                if parent.level + 1 != location.level:
                    raise HTTPException(status_code=400, detail="Parent must be exactly one level above this location")
                ancestor = parent
                while ancestor is not None:
                    if ancestor.id == location.id:
                        raise HTTPException(status_code=400, detail="Location hierarchy cannot contain a cycle")
                    ancestor = db.query(Location).filter(Location.id == ancestor.parent_id).first() if ancestor.parent_id else None
        for key, value in updates.items():
            setattr(location, key, value)
        db.commit()
        db.refresh(location)
        return LocationRead.model_validate(location)

    def delete(self, db: Session, location_id: UUID) -> None:
        location = self.get(db, location_id)
        if db.query(Location.id).filter(Location.parent_id == location_id).first():
            raise HTTPException(status_code=409, detail="Cannot delete a location that has child locations")
        if db.query(Stock.id).filter(Stock.location_id == location_id).first():
            raise HTTPException(status_code=409, detail="Cannot delete a location while it has stock records")
        db.delete(location)
        db.commit()

    def hierarchy(self, db: Session, location_id: UUID) -> LocationHierarchyRead:
        current = self.get(db, location_id)
        names: list[str] = []
        seen: set[UUID] = set()
        while current is not None and current.id not in seen:
            seen.add(current.id)
            names.append(current.name)
            current = db.query(Location).filter(Location.id == current.parent_id).first() if current.parent_id else None
        names.reverse()
        return LocationHierarchyRead(location_id=location_id, path=names, display_name=" -> ".join(names))
