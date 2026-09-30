from uuid import uuid4
from sqlalchemy import Column, String, ForeignKey, Numeric, DateTime, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin

class Purchase(Base, TimestampMixin):
    __tablename__ = "purchases"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    supplier_id = Column(PGUUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=False)
    pharmacy_id = Column(PGUUID(as_uuid=True), ForeignKey("pharmacies.id"), nullable=False)
    purchase_date = Column(DateTime, nullable=False)
    invoice_number = Column(String(100), nullable=True)
    total_amount = Column(Numeric(12, 2))

    supplier = relationship("Supplier")
    items = relationship("PurchaseItem", back_populates="purchase")

class PurchaseItem(Base, TimestampMixin):
    __tablename__ = "purchase_items"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    purchase_id = Column(PGUUID(as_uuid=True), ForeignKey("purchases.id"), nullable=False)
    batch_id = Column(PGUUID(as_uuid=True), ForeignKey("medicine_batches.id"), nullable=False)
    location_id = Column(PGUUID(as_uuid=True), ForeignKey("locations.id"), nullable=False)
    quantity = Column(Numeric(12, 3), nullable=False)

    __table_args__ = (CheckConstraint("quantity > 0", name="check_purchase_item_quantity_positive"),)

    purchase = relationship("Purchase", back_populates="items")
    batch = relationship("MedicineBatch")
    location = relationship("Location")

class Sale(Base, TimestampMixin):
    __tablename__ = "sales"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    pharmacy_id = Column(PGUUID(as_uuid=True), ForeignKey("pharmacies.id"), nullable=False)
    sale_date = Column(DateTime(timezone=True), nullable=False)
    total_amount = Column(Numeric(12, 2))

    items = relationship("SaleItem", back_populates="sale")

    __table_args__ = (Index("ix_sales_pharmacy_date", "pharmacy_id", "sale_date"),)

class SaleItem(Base, TimestampMixin):
    __tablename__ = "sale_items"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    sale_id = Column(PGUUID(as_uuid=True), ForeignKey("sales.id"), nullable=False)
    batch_id = Column(PGUUID(as_uuid=True), ForeignKey("medicine_batches.id"), nullable=False)
    quantity = Column(Numeric(12, 3), nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)

    __table_args__ = (
        CheckConstraint("quantity > 0", name="check_sale_item_quantity_positive"),
        CheckConstraint("unit_price >= 0", name="check_sale_item_price_nonnegative"),
    )

    sale = relationship("Sale", back_populates="items")
    batch = relationship("MedicineBatch")

class StockTransaction(Base, TimestampMixin):
    __tablename__ = "stock_transactions"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    batch_id = Column(PGUUID(as_uuid=True), ForeignKey("medicine_batches.id"), nullable=False)
    location_id = Column(PGUUID(as_uuid=True), ForeignKey("locations.id"), nullable=False)
    change_qty = Column(Numeric(12, 3), nullable=False)
    reason = Column(String(50), nullable=False) # 'PURCHASE', 'SALE', 'ADJUSTMENT', 'EXPIRED'

    batch = relationship("MedicineBatch", back_populates="transactions")
    location = relationship("Location")
