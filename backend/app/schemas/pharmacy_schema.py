from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PharmacyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    address: str | None = Field(default=None, max_length=500)


class PharmacyRead(PharmacyCreate):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
