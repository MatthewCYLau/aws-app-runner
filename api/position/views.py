import uuid
import yfinance as yf
import boto3
from boto3.dynamodb.conditions import Key
from datetime import datetime, timezone
from decimal import Decimal
from fastapi import APIRouter, status


from api.config.logging import get_logger
from api.position.schemas import PositiontBase

logger = get_logger(__name__)


router = APIRouter(prefix="/api/v1/positions", tags=["positions"])

dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
table = dynamodb.Table("stock_trading_positions")


def get_stock_current_price(stock_symbol: str):
    ticker = yf.Ticker(stock_symbol)
    return round(ticker.fast_info["last_price"], 2)


@router.post("/", status_code=status.HTTP_201_CREATED)
def insert_stock_position(position_data: PositiontBase):

    timestamp = datetime.now(timezone.utc).isoformat()

    try:
        response = table.put_item(
            Item={
                "PositionId": str(uuid.uuid4()),
                "StockSymbol": position_data.stock_symbol,
                "CreatedAt": timestamp,
                "OpenPrice": Decimal(str(position_data.open_price)),
                "Quantity": position_data.quantity,
                "Value": Decimal(
                    str(position_data.open_price * position_data.quantity)
                ),
                "Open": True,
            }
        )
        logger.info(
            f"Successfully inserted {position_data.stock_symbol} at {timestamp}"
        )
        return response
    except Exception as e:
        logger.error(f"Error inserting record: {e}")


@router.get("/{position_id}")
def get_position_by_id(
    position_id: uuid.UUID,
):
    logger.info(f"Getting position {position_id}")
    try:
        response = table.query(
            KeyConditionExpression=Key("PositionId").eq(str(position_id))
        )
        logger.info(f"Retrieved position {position_id}")
        return response.get("Items")[0]
    except Exception as e:
        logger.error(f"Failed to fetch position {position_id}: {e}")
        raise
