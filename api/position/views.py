import uuid
import yfinance as yf
import boto3
from boto3.dynamodb.conditions import Key
from datetime import datetime, timezone
from decimal import Decimal
from fastapi import APIRouter, status


from api.config.exception import NotFoundException
from api.config.logging import get_logger
from api.position.schemas import PositiontBase

logger = get_logger(__name__)


router = APIRouter(prefix="/api/v1/positions", tags=["positions"])

dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
positions_table = dynamodb.Table("stock_trading_positions")
pnl_table = dynamodb.Table("positions_pnl")


def get_stock_current_price(stock_symbol: str):
    ticker = yf.Ticker(stock_symbol)
    return round(ticker.fast_info["last_price"], 2)


@router.get("/")
def get_stock_positions():
    items = []
    response = positions_table.scan()
    items.extend(response.get("Items", []))

    while "LastEvaluatedKey" in response:
        response = positions_table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
        items.extend(response.get("Items", []))

    return items


@router.post("/", status_code=status.HTTP_201_CREATED)
def insert_stock_position(position_data: PositiontBase):

    timestamp = datetime.now(timezone.utc).isoformat()

    try:
        response = positions_table.put_item(
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
        response = positions_table.query(
            KeyConditionExpression=Key("PositionId").eq(str(position_id))
        )
        logger.info(f"Retrieved position {position_id}")
        if not response.get("Items"):
            raise NotFoundException(f"Position with id {position_id} not found")
        return response.get("Items")[0]
    except Exception as e:
        logger.error(f"Failed to fetch position {position_id}: {e}")
        raise


def batch_update_pnl():

    positions = positions_table.scan().get("Items", [])

    with pnl_table.batch_writer() as batch:
        for pos in positions:
            position_id = pos["PositionId"]
            stock_symbol = pos["StockSymbol"]
            created_at = pos["CreatedAt"]
            curr_price = Decimal(str(get_stock_current_price(stock_symbol)))
            open_price = pos["OpenPrice"]
            quantity = pos["Quantity"]

            total_pnl = round(((curr_price - open_price) * quantity), 2)
            timestamp = datetime.now(timezone.utc).isoformat()

            batch.put_item(
                Item={
                    "PositionId": position_id,
                    "StockSymbol": stock_symbol,
                    "CreatedAt": created_at,
                    "LastModified": timestamp,
                    "OpenPrice": Decimal(str(open_price)),
                    "CurrentPrice": curr_price,
                    "Quantity": quantity,
                    "TotalPnL": Decimal(str(total_pnl)),
                }
            )

    logger.info(f"Batch update complete for {len(positions)} records.")
