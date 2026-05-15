import io
import os
import uuid

from matplotlib import pyplot as plt
from api.utils.date_util import validate_date_string
import yfinance as yf
import boto3
import pandas as pd
from boto3.dynamodb.conditions import Key, Attr
from datetime import datetime, timezone
from decimal import Decimal
from fastapi import APIRouter, status


from api.config.exception import BadRequestException, NotFoundException
from api.config.logging import get_logger
from api.position.schemas import PositiontBase, UpdatePositiontRequest

logger = get_logger(__name__)


router = APIRouter(prefix="/api/v1/positions", tags=["positions"])

dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
bucket_name = os.environ.get("S3_BUCKET_NAME", "aws-app-runner-assets")
positions_table = dynamodb.Table("stock_trading_positions")
pnl_table = dynamodb.Table("positions_pnl")
stocks_pnl_table = dynamodb.Table("stocks_pnl")


def get_stock_current_price(stock_symbol: str):
    ticker = yf.Ticker(stock_symbol)
    return round(ticker.fast_info["last_price"], 2)


@router.get("/")
def get_stock_positions(startDate: str = None, endDate: str = None):

    dates_input = [startDate, endDate]

    if all(dates_input) and not all([validate_date_string(i) for i in dates_input]):
        raise BadRequestException(
            detail="Invalid date input. Must be in format YYYY-MM-DD"
        )

    if startDate and endDate:
        response = positions_table.scan(
            FilterExpression=Attr("CreatedAt").between(startDate, endDate)
        )
        items = response["Items"]
        return items

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
                "LastModified": timestamp,
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


@router.get("/plot")
def plot_stock_positions():

    items = []
    response = stocks_pnl_table.scan()
    items.extend(response.get("Items", []))

    while "LastEvaluatedKey" in response:
        response = positions_table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
        items.extend(response.get("Items", []))

    df = pd.DataFrame(items)
    df["TotalPnL"] = df["TotalPnL"].apply(
        lambda x: float(x) if isinstance(x, Decimal) else x
    )

    df = df.sort_values(by="TotalPnL", ascending=False)

    logger.info(df)

    _ = plt.figure(num=1, clear=True, figsize=(10, 6))
    colors = ["green" if x > 0 else "red" for x in df["TotalPnL"]]

    plt.bar(df["StockSymbol"], df["TotalPnL"], color=colors)

    plt.axhline(0, color="black", linewidth=0.8)
    plt.title("Portfolio PnL by stock symbol")
    plt.xlabel("Stock symbol")
    plt.ylabel("Profit / Loss ($)")
    plt.xticks(rotation=45)
    plt.grid(axis="y", linestyle="--", alpha=0.7)

    fig_to_upload = plt.gcf()
    img_buffer = io.BytesIO()
    fig_to_upload.savefig(img_buffer, format="png")
    img_buffer.seek(0)

    s3_client = boto3.client("s3")
    file_key = str(datetime.now(timezone.utc).timestamp())
    image_file_key = f"plots/{file_key}.png"

    try:
        s3_client.put_object(
            Bucket=bucket_name,
            Key=image_file_key,
            Body=img_buffer,
            ContentType="image/png",
        )
        logger.info(f"Successfully uploaded to s3://{bucket_name}/{image_file_key}")
        url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket_name, "Key": image_file_key},
            ExpiresIn=86400,
        )
        return {"file_key": image_file_key, "presigned_url": url}
    except Exception as e:
        logger.error(f"Error uploading: {e}")
    finally:
        plt.close(fig_to_upload)


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


@router.delete("/{position_id}")
def delete_position_by_id(
    position_id: uuid.UUID,
):
    logger.info(f"Delete position {position_id}")
    try:

        response = positions_table.query(
            KeyConditionExpression=Key("PositionId").eq(str(position_id))
        )
        items = response.get("Items", [])

        if not items:
            raise NotFoundException(f"Position with id {position_id} not found")

        for item in items:
            positions_table.delete_item(
                Key={"PositionId": item["PositionId"], "CreatedAt": item["CreatedAt"]}
            )

        logger.info("Delete successful")
    except Exception as e:
        logger.error(f"Failed to delete position {position_id}: {e}")
        raise


@router.put("/{position_id}")
def update_position_by_id(
    position_id: uuid.UUID, position_data: UpdatePositiontRequest
):
    logger.info(f"Updating position {position_id}")
    try:
        response = positions_table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key("PositionId").eq(
                str(position_id)
            )
        )

        items = response.get("Items", [])

        if not items:
            raise NotFoundException(f"Position with id {position_id} not found")

        sort_key_value = items[0]["CreatedAt"]

        response = positions_table.update_item(
            Key={"PositionId": str(position_id), "CreatedAt": sort_key_value},
            UpdateExpression="SET OpenPrice = :p, Quantity = :q, #o = :o, #v = :v, LastModified = :lm",
            ExpressionAttributeNames={
                "#v": "Value",  # 'Value' is a reserved keyword in DynamoDB
                "#o": "Open",  # 'Value' is a reserved keyword in DynamoDB
            },
            ExpressionAttributeValues={
                ":p": Decimal(str(position_data.open_price)),
                ":q": position_data.quantity,
                ":o": position_data.isOpen,
                ":v": Decimal(str(position_data.open_price * position_data.quantity)),
                ":lm": datetime.now(timezone.utc).isoformat(),
            },
            ReturnValues="ALL_NEW",
        )

        logger.info(f"Successfully updated position {position_id}")
        return response

    except Exception as e:
        logger.error(f"Failed to fetch position {position_id}: {e}")
        raise


def batch_update_pnl():

    response = positions_table.scan(FilterExpression=Attr("Open").eq(True))
    positions_to_update = response.get("Items", [])

    while "LastEvaluatedKey" in response:
        response = positions_table.scan(
            FilterExpression=Attr("Open").eq(True),
            ExclusiveStartKey=response["LastEvaluatedKey"],
        )
        positions_to_update.extend(response.get("Items", []))

    with pnl_table.batch_writer() as batch:
        for pos in positions_to_update:
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

    logger.info(f"Batch update complete for {len(positions_to_update)} records.")
