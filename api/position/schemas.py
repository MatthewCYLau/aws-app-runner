from typing import Optional

from pydantic import BaseModel, field_validator, ValidationInfo

from api.utils.stock_util import check_asset_available


class PositiontBase(BaseModel):
    stock_symbol: str
    open_price: float
    quantity: int

    @field_validator("stock_symbol")
    @classmethod
    def check_stock(cls, stock_symbol: str, info: ValidationInfo) -> str:
        if not check_asset_available(stock_symbol):
            raise ValueError(f"{info.field_name} is not a valid stock symbol")
        return stock_symbol


class UpdatePositiontRequest(BaseModel):
    open_price: float
    quantity: int
    isOpen: Optional[bool] = True
