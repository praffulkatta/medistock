from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from uuid import UUID
from datetime import datetime

class CategoryBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)

class CategoryCreate(CategoryBase):
    pharmacy_id: UUID

class CategoryUpdate(BaseModel):
    name: Optional[str] = None

class CategoryRead(CategoryBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
