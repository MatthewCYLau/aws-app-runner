import json
import random
import time
import boto3
import numpy as np
from api.config.constants import AWS_REGION, STREAM_NAME
from api.config.logging import get_logger

kinesis_client = boto3.client("kinesis", region_name=AWS_REGION)

BOOK_IDS = ["RATES-EU-01", "FX-DELTA-02", "EQ-ALPHA-01"]
TICKERS = ["EURUSD", "GBPUSD", "US10Y"]
logger = get_logger(__name__)


def generate_random_five_digit_int():
    digits = np.concatenate(
        [np.random.randint(1, 10, size=1), np.random.randint(0, 10, size=4)]
    )

    powers_of_ten = np.array([10_000, 1_000, 100, 10, 1])

    return int(np.sum(digits * powers_of_ten))


def generate_trade():
    book_id = random.choice(BOOK_IDS)
    return {
        "trade_id": f"TRD-{generate_random_five_digit_int()}",
        "book_id": book_id,
        "ticker": random.choice(TICKERS),
        "quantity": random.choice([100000, -50000, 250000, -100000]),
        "exec_price": round(random.uniform(100.0, 105.0), 4),
        "realized_pnl_impact": round(random.uniform(-500.0, 1500.0), 2),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def push_trade_to_stream():
    trade = generate_trade()
    response = kinesis_client.put_record(
        StreamName=STREAM_NAME,
        Data=json.dumps(trade),
        PartitionKey=trade["book_id"],
    )
    logger.info(
        f"Sent trade {trade['trade_id']} | Book: {trade['book_id']} | Shard: {response['SequenceNumber'][:15]}..."
    )
