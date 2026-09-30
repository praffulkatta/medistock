from sqlalchemy import Column, String, ForeignKey, UUID
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin

class Pharmacy(Base, TimestampMixin):
    __tablename__ = "pharmacies"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=lambda: __import__('uuid').uuid4())
    name = Column(String(255), nullable=False)
    address = Column(String(500))

    users = relationship("User", back_populates="pharmacy")
    categories = relationship("Category", back_populates="pharmacy")
    medicines = relationship("Medicine", back_populates="pharmacy")
    suppliers = relationship("Supplier", back_populates="pharmacy")
    locations = relationship("Location", back_populates="pharmacy")

class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=lambda: __import__('uuid').uuid4())
    pharmacy_id = Column(PGUUID(as_uuid=True), ForeignKey("pharmacies.id"), nullable=False)
    username = Column(String(50), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False) # 'Admin', 'Pharmacist', 'Staff'

    pharmacy = relationship("Pharmacy", back_populates="users")
