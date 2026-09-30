from uuid import uuid4
from sqlalchemy import Column, String, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin

class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    pharmacy_id = Column(PGUUID(as_uuid=True), ForeignKey("pharmacies.id"), nullable=False)
    type = Column(String(50), nullable=False) # 'LOW_STOCK', 'EXPIRY_WARNING'
    message = Column(String(500), nullable=False)
    is_read = Column(Boolean, default=False, nullable=False, server_default="false")

    pharmacy = relationship("Pharmacy")
