from pydantic import BaseModel


class PositiontBase(BaseModel):
    stock_symbol: str
    open_price: float
