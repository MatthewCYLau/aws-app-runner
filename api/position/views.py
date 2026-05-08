import boto3
from datetime import datetime, timezone
from decimal import Decimal
from fastapi import APIRouter, status


from api.config.logging import get_logger
from api.position.schemas import PositiontBase

logger = get_logger(__name__)


router = APIRouter(prefix="/api/v1/positions", tags=["positions"])

dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
table = dynamodb.Table("stock_trading_positions")


@router.post("/", status_code=status.HTTP_201_CREATED)
def insert_stock_position(position_data: PositiontBase):

    delta = Decimal(str(position_data.current_price)) - Decimal(
        str(position_data.open_price)
    )

    timestamp = int(datetime.now(timezone.utc).timestamp())

    try:
        response = table.put_item(
            Item={
                "StockSymbol": position_data.stock_symbol,
                "Timestamp": timestamp,
                "OpenPrice": Decimal(str(position_data.open_price)),
                "CurrentPrice": Decimal(str(position_data.current_price)),
                "Delta": delta,
            }
        )
        logger.info(
            f"Successfully inserted {position_data.stock_symbol} at {timestamp}"
        )
        return response
    except Exception as e:
        logger.error(f"Error inserting record: {e}")
