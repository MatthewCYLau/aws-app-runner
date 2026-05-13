from typing import Optional

from pydantic import BaseModel


class PositiontBase(BaseModel):
    stock_symbol: str
    open_price: float
    quantity: int


class UpdatePositiontRequest(BaseModel):
    open_price: float
    quantity: int
    isOpen: Optional[bool] = True
