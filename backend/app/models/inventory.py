from uuid import uuid4
from sqlalchemy import Column, String, ForeignKey, Numeric, Date, Integer, Index, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin

class Supplier(Base, TimestampMixin):
    __tablename__ = "suppliers"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    pharmacy_id = Column(PGUUID(as_uuid=True), ForeignKey("pharmacies.id"), nullable=False)
    name = Column(String(255), nullable=False)
    contact_info = Column(String(500))

    pharmacy = relationship("Pharmacy", back_populates="suppliers")
    batches = relationship("MedicineBatch", back_populates="supplier")

    __table_args__ = (UniqueConstraint("pharmacy_id", "name", name="uq_supplier_pharmacy_name"),)

class MedicineBatch(Base, TimestampMixin):
    __tablename__ = "medicine_batches"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    medicine_id = Column(PGUUID(as_uuid=True), ForeignKey("medicines.id"), nullable=False)
    supplier_id = Column(PGUUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=False)
    batch_number = Column(String(100), nullable=False)
    manufacturing_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=False)
    cost_price = Column(Numeric(12, 2), nullable=False)
    selling_price = Column(Numeric(12, 2), nullable=False)

    medicine = relationship("Medicine", back_populates="batches")
    supplier = relationship("Supplier", back_populates="batches")
    stock = relationship("Stock", back_populates="batch")
    transactions = relationship("StockTransaction", back_populates="batch")

    __table_args__ = (
        UniqueConstraint("medicine_id", "batch_number", name="uq_batch_medicine_number"),
        Index("ix_batch_number_trgm", "batch_number", postgresql_using="gin", postgresql_ops={"batch_number": "gin_trgm_ops"}),
        Index("ix_expiry_date", "expiry_date"),
        CheckConstraint("cost_price >= 0", name="check_batch_cost_nonnegative"),
        CheckConstraint("selling_price >= 0", name="check_batch_price_nonnegative"),
    )

class Location(Base, TimestampMixin):
    __tablename__ = "locations"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    pharmacy_id = Column(PGUUID(as_uuid=True), ForeignKey("pharmacies.id"), nullable=False)
    name = Column(String(50), nullable=False)
    type = Column(String(20), nullable=False) # 'Block', 'Rack', 'Shelf', 'Bin'
    parent_id = Column(PGUUID(as_uuid=True), ForeignKey("locations.id"), nullable=True)
    level = Column(Integer, nullable=False) # 1: Block, 2: Rack, 3: Shelf, 4: Bin

    pharmacy = relationship("Pharmacy", back_populates="locations")
    children = relationship("Location", backref="parent", remote_side=[id])
    stock = relationship("Stock", back_populates="location")

    __table_args__ = (
        Index("ix_location_parent", "parent_id"),
    )

class Stock(Base, TimestampMixin):
    __tablename__ = "stock"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    batch_id = Column(PGUUID(as_uuid=True), ForeignKey("medicine_batches.id"), nullable=False)
    location_id = Column(PGUUID(as_uuid=True), ForeignKey("locations.id"), nullable=False)
    quantity = Column(Numeric(12, 3), nullable=False)

    batch = relationship("MedicineBatch", back_populates="stock")
    location = relationship("Location", back_populates="stock")

    __table_args__ = (
        UniqueConstraint("batch_id", "location_id", name="uq_stock_batch_location"),
        Index("ix_stock_location", "location_id"),
        CheckConstraint("quantity >= 0", name="check_stock_quantity_positive"),
    )
