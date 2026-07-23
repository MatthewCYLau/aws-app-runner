import csv
import io
import os
import uuid
import asyncio
import boto3
import statistics
import random
from httpx import AsyncClient, HTTPStatusError
from matplotlib import pyplot as plt
from api.config.constants import (
    POSITIONS_CSV_COLUMNS,
    POSITIONS_PNL_AGGREGATE,
    POSITIONS_PNL_TIMESERIES,
    STOCK_TRADING_POSITIONS_TABLE,
    STOCKS_PNL,
)
from api.config.metrics import OPEN_POSITIONS_GAUGE
from api.utils.date_util import validate_date_string
import yfinance as yf
import pandas as pd
from boto3.dynamodb.conditions import Key, Attr
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from fastapi import APIRouter, File, HTTPException, UploadFile, status
import numpy as np


from api.config.exception import BadRequestException, NotFoundException
from api.config.constants import S3_BUCKET_NAME
from api.config.logging import get_logger
from api.position.schemas import PositionBase, UpdatePositiontRequest
from api.utils.dynamodb_util import get_dynamodb_table_client
from api.utils.stock_util import fetch_live_snapshots
from api.utils.utils import custom_get_random_int

logger = get_logger(__name__)


router = APIRouter(prefix="/api/v1/positions", tags=["positions"])

daily_volatility = 0.02


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

    positions_table = get_dynamodb_table_client(STOCK_TRADING_POSITIONS_TABLE)

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
def insert_stock_position(position_data: PositionBase):

    timestamp = datetime.now(timezone.utc).isoformat()
    positions_table = get_dynamodb_table_client(STOCK_TRADING_POSITIONS_TABLE)

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
        OPEN_POSITIONS_GAUGE.inc()
        return response
    except Exception as e:
        logger.error(f"Error inserting record: {e}")


@router.get("/plot")
def plot_stock_positions():

    items = []
    stocks_pnl_table = get_dynamodb_table_client(STOCKS_PNL)
    response = stocks_pnl_table.scan()
    items.extend(response.get("Items", []))

    while "LastEvaluatedKey" in response:
        response = stocks_pnl_table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
        items.extend(response.get("Items", []))

    df = pd.DataFrame(items)

    if df.empty:
        raise NotFoundException("No positions found.")

    unique_stock_symbol_mask = ~df.duplicated(subset=["StockSymbol"], keep=False)
    unique_stock_symbol_df = df.loc[unique_stock_symbol_mask]

    logger.info(
        f"Unique stock symbols: {unique_stock_symbol_df['StockSymbol'].values.tolist()}"
    )

    df["TotalPnL"] = df["TotalPnL"].apply(
        lambda x: float(x) if isinstance(x, Decimal) else x
    )

    df = df.sort_values(by="TotalPnL", ascending=False)

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
            Bucket=S3_BUCKET_NAME,
            Key=image_file_key,
            Body=img_buffer,
            ContentType="image/png",
        )
        logger.info(f"Successfully uploaded to s3://{S3_BUCKET_NAME}/{image_file_key}")
        url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": S3_BUCKET_NAME, "Key": image_file_key},
            ExpiresIn=86400,
        )
        return {"file_key": image_file_key, "presigned_url": url}
    except Exception as e:
        logger.error(f"Error uploading: {e}")


@router.get("/{position_id}")
def get_position_by_id(
    position_id: uuid.UUID,
):
    logger.info(f"Getting position {position_id}")
    positions_table = get_dynamodb_table_client(STOCK_TRADING_POSITIONS_TABLE)

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
    positions_table = get_dynamodb_table_client(STOCK_TRADING_POSITIONS_TABLE)

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
    positions_table = get_dynamodb_table_client(STOCK_TRADING_POSITIONS_TABLE)

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


def get_historical_pnl(position_id, limit=30):
    positions_pnl_aggregate_table = get_dynamodb_table_client(POSITIONS_PNL_AGGREGATE)
    response = positions_pnl_aggregate_table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key("PositionId").eq(
            position_id
        ),
        ScanIndexForward=False,
        Limit=limit,
    )

    return response.get("Items", [])


def validate_new_pnl(historical_items, new_pnl, method="z_score", threshold=3.0):
    """
    Validates if the new PnL deviates heavily from historical norms.
    Returns (is_valid, message)
    """
    if not historical_items:
        return True, "No history available. Baseline established."

    df = pd.DataFrame(historical_items)

    # Ensure numerical types
    df["TotalPnL"] = pd.to_numeric(df["TotalPnL"])
    pnl_series = df["TotalPnL"]

    if len(pnl_series) < 1:
        return True, "Insufficient history for robust validation."

    if method == "z_score":
        mean = pnl_series.mean()
        std = pnl_series.std()

        if std == 0:
            std = 0.01

        z_score = abs(new_pnl - mean) / std

        if z_score > threshold:
            return (
                False,
                f"Rejected: Z-Score is {z_score:.2f} (Threshold: {threshold}). Expected mean around {mean:.2f}.",
            )

    return True, "Valid"


async def get_shock_percent_normal():
    await asyncio.sleep(1)
    pnl_shock_percent_normal = Decimal(
        str(np.random.uniform(-daily_volatility, daily_volatility))
    )
    return pnl_shock_percent_normal


async def get_random_number(async_client: AsyncClient, max_try: int = 3):
    for _ in range(max_try):
        try:
            res = await async_client.get("https://jsonplaceholder.typicode.com/posts")
            res.raise_for_status()
            res_data = res.json()
            random_id = random.choice(res_data)["id"]
            return random_id
        except HTTPStatusError as e:
            if isinstance(e, HTTPStatusError) and e.response.status_code <= 403:
                return None
            await asyncio.sleep(2)
    return None


async def batch_update_pnl():

    positions_table = get_dynamodb_table_client(STOCK_TRADING_POSITIONS_TABLE)
    response = positions_table.scan(FilterExpression=Attr("Open").eq(True))
    positions_to_update = response.get("Items", [])

    while "LastEvaluatedKey" in response:
        response = positions_table.scan(
            FilterExpression=Attr("Open").eq(True),
            ExclusiveStartKey=response["LastEvaluatedKey"],
        )
        positions_to_update.extend(response.get("Items", []))

    for pos in positions_to_update:
        position_id = pos["PositionId"]
        stock_symbol = pos["StockSymbol"]
        created_at = pos["CreatedAt"]

        curr_price = Decimal(
            str(fetch_live_snapshots(stock_symbol).loc[stock_symbol]["Current_Price"])
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        open_price = Decimal(str(pos["OpenPrice"]))
        quantity = Decimal(str(pos["Quantity"]))

        total_pnl = ((curr_price - open_price) * quantity).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        pnl_shock_percent = Decimal(
            str(np.random.normal(loc=0.0, scale=daily_volatility))
        )
        pnl_shock_percent_rounded = pnl_shock_percent.quantize(
            Decimal("0.0001"), rounding=ROUND_HALF_UP
        )

        async with AsyncClient() as client:
            tasks = [get_random_number(client) for _ in range(custom_get_random_int())]
            res = await asyncio.gather(*tasks)

        random_number = statistics.mean(res)
        logger.info(f"Random number from async client: {random_number}")

        tasks = [
            get_shock_percent_normal()
            for _ in range(np.random.randint(1, 10, size=1)[0])
        ]
        pnl_shock_percent_normal_values = await asyncio.gather(*tasks)

        pnl_shock_percent_normal_rounded = statistics.mean(
            pnl_shock_percent_normal_values
        ).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

        logger.info(
            f"Shock percent values: {(pnl_shock_percent_rounded, pnl_shock_percent_normal_rounded)}"
        )

        shocked_pnl = (
            total_pnl
            * (Decimal("1") + pnl_shock_percent_rounded)
            * (Decimal("1") + pnl_shock_percent_normal_rounded)
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        timestamp = datetime.now(timezone.utc).isoformat()

        history = get_historical_pnl(position_id, limit=50)
        is_valid, message = validate_new_pnl(
            history, total_pnl, method="iqr", threshold=3.0
        )

        if not is_valid:
            logger.warn(f"CRITICAL: Data validation failed! {message}")
            continue

        logger.info("Metrics healthy. Writing to DynamoDB...")

        positions_pnl_aggregate_table = get_dynamodb_table_client(
            POSITIONS_PNL_AGGREGATE
        )
        with positions_pnl_aggregate_table.batch_writer() as batch:
            batch.put_item(
                Item={
                    "PositionId": position_id,
                    "StockSymbol": stock_symbol,
                    "CreatedAt": created_at,
                    "LastModified": timestamp,
                    "OpenPrice": open_price,
                    "CurrentPrice": curr_price,
                    "Quantity": quantity,
                    "TotalPnL": total_pnl,
                    "PnlShockPercent": pnl_shock_percent_rounded * 100,
                    "ShockedPnL": shocked_pnl,
                }
            )

        positions_pnl_timeseries_table = get_dynamodb_table_client(
            POSITIONS_PNL_TIMESERIES
        )
        with positions_pnl_timeseries_table.batch_writer() as batch:
            batch.put_item(
                Item={
                    "PositionId": position_id,
                    "StockSymbol": stock_symbol,
                    "CreatedAt": datetime.now(timezone.utc).isoformat(),
                    "OpenPrice": open_price,
                    "CurrentPrice": curr_price,
                    "Quantity": quantity,
                    "ShockedPnL": shocked_pnl,
                }
            )

    logger.info(f"Batch update complete for {len(positions_to_update)} records.")


@router.post("/upload-csv", status_code=status.HTTP_201_CREATED)
async def upload_csv(upload_file: UploadFile = File(...)):

    if not upload_file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Please upload a CSV file.",
        )

    try:
        contents = await upload_file.read()
        csv_file = io.StringIO(contents.decode("utf-8"))
        reader = csv.DictReader(csv_file)

        timestamp = datetime.now(timezone.utc).isoformat()
        positions_table = get_dynamodb_table_client(STOCK_TRADING_POSITIONS_TABLE)

        with positions_table.batch_writer() as batch:
            counter = 0

            if not all(key in POSITIONS_CSV_COLUMNS for key in reader.fieldnames):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid CSV column headers",
                )

            for row in reader:
                item = {k: v for k, v in row.items() if v != ""}

                if item:
                    Item = {
                        "PositionId": str(uuid.uuid4()),
                        "StockSymbol": item["stock symbol"],
                        "CreatedAt": timestamp,
                        "LastModified": timestamp,
                        "OpenPrice": Decimal(str(item["open price"])),
                        "Quantity": item["quantity"],
                        "Value": Decimal(
                            str(float(item["open price"]) * int(item["quantity"]))
                        ),
                        "Open": True,
                    }
                    batch.put_item(Item=Item)
                    logger.info(
                        f"Successfully inserted {item['stock symbol']} at {timestamp}"
                    )
                    OPEN_POSITIONS_GAUGE.inc()
                    counter += 1

            return {
                "message": "CSV positions data successfully uploaded to DynamoDB",
                "positions_inserted": counter,
            }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )
    finally:
        await upload_file.close()
