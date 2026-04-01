from pydantic import BaseModel, ConfigDict
from datetime import datetime
import uuid


class ProductBase(BaseModel):
    name: str
    price: float


class ProductResponse(ProductBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    created_at: datetime
