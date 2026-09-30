from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.location_schema import LocationCreate, LocationHierarchyRead, LocationRead, LocationUpdate
from app.services.location_service import LocationService

router = APIRouter(prefix="/locations", tags=["Locations"])
service = LocationService()


@router.post("/", response_model=LocationRead, status_code=status.HTTP_201_CREATED)
def create_location(data: LocationCreate, db: Session = Depends(get_db)):
    return service.create(db, data)


@router.get("/", response_model=list[LocationRead])
def list_locations(
    pharmacy_id: UUID,
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    return service.list(db, pharmacy_id, limit, offset)


@router.get("/{location_id}/hierarchy", response_model=LocationHierarchyRead)
def get_location_hierarchy(location_id: UUID, db: Session = Depends(get_db)):
    return service.hierarchy(db, location_id)


@router.get("/{location_id}", response_model=LocationRead)
def get_location(location_id: UUID, db: Session = Depends(get_db)):
    return LocationRead.model_validate(service.get(db, location_id))


@router.put("/{location_id}", response_model=LocationRead)
def update_location(location_id: UUID, data: LocationUpdate, db: Session = Depends(get_db)):
    return service.update(db, location_id, data)


@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_location(location_id: UUID, db: Session = Depends(get_db)):
    service.delete(db, location_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
