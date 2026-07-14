from typing import Optional

from pydantic import BaseModel, field_validator, ValidationInfo, model_validator
from api.config.logging import get_logger
from api.utils.dynamodb_util import validate_position
from api.utils.stock_util import check_asset_available, fetch_live_snapshots

logger = get_logger(__name__)


class PositionBase(BaseModel):
    stock_symbol: str
    open_price: float
    quantity: int

    @field_validator("stock_symbol")
    @classmethod
    def check_stock(cls, stock_symbol: str, info: ValidationInfo) -> str:
        if not check_asset_available(stock_symbol):
            error_message = (
                f"{info.field_name} {stock_symbol} is not a valid stock symbol"
            )
            logger.error(error_message)
            raise ValueError(error_message)
        return stock_symbol

    @model_validator(mode="after")
    def check_open_price(self):

        curr_price = fetch_live_snapshots(self.stock_symbol).loc[self.stock_symbol][
            "Current_Price"
        ]

        lower_boundary = curr_price * 0.9
        uppder_boundary = curr_price * 1.1

        if self.open_price > uppder_boundary or self.open_price < lower_boundary:
            error_message = f"{self.stock_symbol} open price {self.open_price} is outside of lower boundary {lower_boundary:.2f} and upper boundary {uppder_boundary:.2f}"
            logger.error(error_message)
            raise ValueError(error_message)

        return self


class UpdatePositiontRequest(BaseModel):
    open_price: float
    quantity: int
    isOpen: Optional[bool] = True


class UpdatePositionMessageBase(BaseModel):
    position_id: str
    quantity: int

    @field_validator("position_id")
    @classmethod
    def check_stock(cls, position_id: str, info: ValidationInfo) -> str:
        if not validate_position(position_id):
            raise ValueError(
                f"{info.field_name} {position_id} is not a valid position ID"
            )
        return position_id
