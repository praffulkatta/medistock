from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.category_schema import CategoryCreate, CategoryRead, CategoryUpdate
from app.services.category_service import CategoryService

router = APIRouter(prefix="/categories", tags=["Categories"])
service = CategoryService()


@router.post("/", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(data: CategoryCreate, db: Session = Depends(get_db)):
    return service.create(db, data)


@router.get("/", response_model=list[CategoryRead])
def list_categories(
    pharmacy_id: UUID,
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    return service.list(db, pharmacy_id, limit, offset)


@router.get("/{category_id}", response_model=CategoryRead)
def get_category(category_id: UUID, db: Session = Depends(get_db)):
    return CategoryRead.model_validate(service.get(db, category_id))


@router.put("/{category_id}", response_model=CategoryRead)
def update_category(category_id: UUID, data: CategoryUpdate, db: Session = Depends(get_db)):
    return service.update(db, category_id, data)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: UUID, db: Session = Depends(get_db)):
    service.delete(db, category_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
