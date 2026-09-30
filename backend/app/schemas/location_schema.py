from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from typing import Optional, List, Literal
from datetime import datetime

class LocationBase(BaseModel):
    name: str = Field(..., max_length=50)
    type: Literal["Block", "Rack", "Shelf", "Bin"]
    level: int = Field(..., ge=1, le=4, description="1: Block, 2: Rack, 3: Shelf, 4: Bin")
    parent_id: Optional[UUID] = None

class LocationCreate(LocationBase):
    pharmacy_id: UUID

class LocationUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=50)
    type: Optional[Literal["Block", "Rack", "Shelf", "Bin"]] = None
    parent_id: Optional[UUID] = None

class LocationRead(LocationBase):
    id: UUID
    pharmacy_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class LocationHierarchyRead(BaseModel):
    location_id: UUID
    path: List[str] # e.g., ["Block A", "Rack 03", "Shelf 02", "Bin 04"]
    display_name: str # e.g., "Block A -> Rack 03 -> Shelf 02 -> Bin 04"
