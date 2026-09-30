from sqlalchemy.orm import Session

from app.models.auth import Pharmacy
from app.schemas.pharmacy_schema import PharmacyCreate, PharmacyRead


class PharmacyService:
    @staticmethod
    def list(db: Session, limit: int, offset: int) -> list[PharmacyRead]:
        rows = db.query(Pharmacy).order_by(Pharmacy.name, Pharmacy.id).offset(offset).limit(limit).all()
        return [PharmacyRead.model_validate(row) for row in rows]

    @staticmethod
    def create(db: Session, data: PharmacyCreate) -> PharmacyRead:
        pharmacy = Pharmacy(name=data.name.strip(), address=data.address)
        db.add(pharmacy)
        db.commit()
        db.refresh(pharmacy)
        return PharmacyRead.model_validate(pharmacy)
