from dataclasses import dataclass


@dataclass
class PositionResponse:
    position_id: str
    last_modified: str
    stock_symbol: str
    is_open: bool
    quantity: int
    open_price: float
    value: float
    created_at: str
