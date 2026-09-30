from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from uuid import UUID
from datetime import datetime

class MedicineBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    generic_name: str = Field(min_length=1, max_length=255)
    manufacturer: Optional[str] = Field(default=None, max_length=255)
    category_id: UUID
    dosage_form: Optional[str] = None
    strength: Optional[str] = None
    prescription_required: bool = False
    description: Optional[str] = None
    min_stock_level: float = Field(default=0, ge=0)

class MedicineCreate(MedicineBase):
    pharmacy_id: UUID

class MedicineUpdate(BaseModel):
    name: Optional[str] = None
    generic_name: Optional[str] = None
    manufacturer: Optional[str] = None
    category_id: Optional[UUID] = None
    dosage_form: Optional[str] = None
    strength: Optional[str] = None
    prescription_required: Optional[bool] = None
    description: Optional[str] = None
    min_stock_level: Optional[float] = Field(default=None, ge=0)

class MedicineRead(MedicineBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
