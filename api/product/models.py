from datetime import datetime
from sqlalchemy import TIMESTAMP, Column, Index, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from api.config.database import Base
import uuid


class Product(Base):
    """Product model."""

    __tablename__ = "products"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    name = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.now())
    price = Column(Numeric, nullable=False)
    __table_args__ = (Index("ix_product_name_price", "name", "price"),)
