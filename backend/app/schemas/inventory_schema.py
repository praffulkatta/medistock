from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class BatchCreate(BaseModel):
    medicine_id: UUID
    supplier_id: UUID
    batch_number: str = Field(min_length=1, max_length=100)
    manufacturing_date: date | None = None
    expiry_date: date
    cost_price: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    selling_price: Decimal = Field(ge=0, max_digits=12, decimal_places=2)


class BatchRead(BatchCreate):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PurchaseItemCreate(BaseModel):
    medicine_id: UUID
    batch_number: str = Field(min_length=1, max_length=100)
    manufacturing_date: date | None = None
    expiry_date: date
    cost_price: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    selling_price: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    quantity: Decimal = Field(gt=0, max_digits=12, decimal_places=3)
    location_id: UUID


class PurchaseCreate(BaseModel):
    pharmacy_id: UUID
    supplier_id: UUID
    purchase_date: datetime | None = None
    invoice_number: str | None = Field(default=None, max_length=100)
    items: list[PurchaseItemCreate] = Field(min_length=1)


class ReceivedItemRead(BaseModel):
    batch_id: UUID
    batch_number: str
    quantity: Decimal
    location_id: UUID


class PurchaseRead(BaseModel):
    id: UUID
    pharmacy_id: UUID
    supplier_id: UUID
    purchase_date: datetime
    invoice_number: str | None
    total_amount: Decimal
    items: list[ReceivedItemRead]


class TransferCreate(BaseModel):
    pharmacy_id: UUID
    batch_id: UUID
    source_location_id: UUID
    destination_location_id: UUID
    quantity: Decimal = Field(gt=0, max_digits=12, decimal_places=3)


class StockLocationRead(BaseModel):
    location_id: UUID
    location_path: list[str]
    quantity: Decimal


class BatchLocatorRead(BaseModel):
    batch_id: UUID
    batch_number: str
    expiry_date: date
    expiry_status: Literal["EXPIRED", "EXPIRING_SOON", "SAFE"]
    quantity: Decimal
    locations: list[StockLocationRead]


class MedicineSearchItem(BaseModel):
    medicine_id: UUID
    name: str
    generic_name: str
    manufacturer: str | None
    min_stock_level: Decimal
    total_quantity: Decimal
    batches: list[BatchLocatorRead]


class MedicineSearchRead(BaseModel):
    results: list[MedicineSearchItem]
    total: int
    limit: int
    offset: int


class StockTransactionRead(BaseModel):
    id: UUID
    batch_id: UUID
    location_id: UUID
    change_qty: Decimal
    reason: str
    created_at: datetime
    medicine_name: str
    batch_number: str
    location_name: str
