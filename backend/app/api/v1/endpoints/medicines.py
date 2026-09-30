from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.inventory_schema import MedicineSearchRead
from app.schemas.medicine_schema import MedicineCreate, MedicineRead, MedicineUpdate
from app.services.medicine_service import MedicineService

router = APIRouter(prefix="/medicines", tags=["Medicines"])
service = MedicineService()


@router.get("/search", response_model=MedicineSearchRead)
def search_medicines(
    pharmacy_id: UUID,
    q: str = Query(min_length=1, max_length=100),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    if not q.strip():
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail="Search query cannot be blank")
    return service.search(db, pharmacy_id, q, limit, offset)


@router.post("/", response_model=MedicineRead, status_code=status.HTTP_201_CREATED)
def create_medicine(data: MedicineCreate, db: Session = Depends(get_db)):
    return service.create(db, data)


@router.get("/", response_model=list[MedicineRead])
def list_medicines(
    pharmacy_id: UUID,
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0),
    category_id: UUID | None = None,
    db: Session = Depends(get_db),
):
    return service.list(db, pharmacy_id, limit, offset, category_id)


@router.get("/{medicine_id}", response_model=MedicineRead)
def get_medicine(medicine_id: UUID, db: Session = Depends(get_db)):
    return MedicineRead.model_validate(service.get(db, medicine_id))


@router.put("/{medicine_id}", response_model=MedicineRead)
def update_medicine(medicine_id: UUID, data: MedicineUpdate, db: Session = Depends(get_db)):
    return service.update(db, medicine_id, data)


@router.delete("/{medicine_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_medicine(medicine_id: UUID, db: Session = Depends(get_db)):
    service.delete(db, medicine_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
