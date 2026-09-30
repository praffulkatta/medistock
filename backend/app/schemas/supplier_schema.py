from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from uuid import UUID
from datetime import datetime

class SupplierBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    contact_info: Optional[str] = Field(default=None, max_length=500)

class SupplierCreate(SupplierBase):
    pharmacy_id: UUID

class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    contact_info: Optional[str] = None

class SupplierRead(SupplierBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
