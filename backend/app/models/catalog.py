from uuid import uuid4
from sqlalchemy import Column, String, ForeignKey, Boolean, Text, Numeric, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin

class Category(Base, TimestampMixin):
    __tablename__ = "categories"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    pharmacy_id = Column(PGUUID(as_uuid=True), ForeignKey("pharmacies.id"), nullable=False)
    name = Column(String(100), nullable=False)

    pharmacy = relationship("Pharmacy", back_populates="categories")
    medicines = relationship("Medicine", back_populates="category")

    __table_args__ = (UniqueConstraint("pharmacy_id", "name", name="uq_category_pharmacy_name"),)

class Medicine(Base, TimestampMixin):
    __tablename__ = "medicines"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    pharmacy_id = Column(PGUUID(as_uuid=True), ForeignKey("pharmacies.id"), nullable=False)
    category_id = Column(PGUUID(as_uuid=True), ForeignKey("categories.id"), nullable=False)
    name = Column(String(255), nullable=False)
    generic_name = Column(String(255), nullable=False)
    manufacturer = Column(String(255), nullable=True)
    dosage_form = Column(String(100), nullable=True)
    strength = Column(String(50))
    prescription_required = Column(Boolean, default=False, nullable=False)
    description = Column(Text, nullable=True)
    min_stock_level = Column(Numeric(12, 3), nullable=False, default=0, server_default="0")

    pharmacy = relationship("Pharmacy", back_populates="medicines")
    category = relationship("Category", back_populates="medicines")
    batches = relationship("MedicineBatch", back_populates="medicine")

    __table_args__ = (
        UniqueConstraint("pharmacy_id", "name", "strength", name="uq_medicine_pharmacy_name_strength"),
        Index("ix_medicines_name_trgm", "name", postgresql_using="gin", postgresql_ops={"name": "gin_trgm_ops"}),
        Index("ix_medicines_generic_trgm", "generic_name", postgresql_using="gin", postgresql_ops={"generic_name": "gin_trgm_ops"}),
        Index("ix_medicines_manufacturer_trgm", "manufacturer", postgresql_using="gin", postgresql_ops={"manufacturer": "gin_trgm_ops"}),
    )
