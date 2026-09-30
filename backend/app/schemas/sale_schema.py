from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime
from uuid import UUID
from decimal import Decimal
from decimal import Decimal

class SaleItemCreate(BaseModel):
    medicine_id: UUID
    quantity: Decimal = Field(..., gt=0, max_digits=12, decimal_places=3)
    unit_price: Decimal = Field(..., ge=0, max_digits=12, decimal_places=2)

class SaleCreate(BaseModel):
    pharmacy_id: UUID
    sale_date: Optional[datetime] = None
    items: List[SaleItemCreate] = Field(min_length=1)

class SaleItemRead(BaseModel):
    id: UUID
    batch_id: UUID
    quantity: Decimal
    unit_price: Decimal

    model_config = ConfigDict(from_attributes=True)

class SaleRead(BaseModel):
    id: UUID
    sale_date: datetime
    total_amount: Decimal
    items: List[SaleItemRead]

    model_config = ConfigDict(from_attributes=True)
