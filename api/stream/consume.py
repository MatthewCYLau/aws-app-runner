import json
import logging
import time
import boto3

from api.config.constants import STREAM_NAME, AWS_REGION, S3_DATA_SINK_BUCKET_NAME

BATCH_SIZE = 1

kinesis = boto3.client("kinesis", region_name=AWS_REGION)
s3 = boto3.client("s3", region_name=AWS_REGION)


logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def get_all_shard_iterators(iterator_type="TRIM_HORIZON"):
    """Fetches iterators for ALL open shards in the stream."""
    shards_response = kinesis.list_shards(StreamName=STREAM_NAME)
    iterators = {}

    for shard in shards_response.get("Shards", []):
        shard_id = shard["ShardId"]
        if "EndingSequenceNumber" not in shard.get("SequenceNumberRange", {}):
            resp = kinesis.get_shard_iterator(
                StreamName=STREAM_NAME,
                ShardId=shard_id,
                ShardIteratorType=iterator_type,
            )
            iterators[shard_id] = resp["ShardIterator"]

    return iterators


def write_to_s3(buffer):

    timestamp = int(time.time())
    s3_key = f"trades/raw_trades_{timestamp}.json"

    payload = "\n".join([json.dumps(record) for record in buffer])

    s3.put_object(
        Bucket=S3_DATA_SINK_BUCKET_NAME,
        Key=s3_key,
        Body=payload,
        ContentType="application/json",
    )
    logger.info(
        f"Uploaded {len(buffer)} records -> s3://{S3_DATA_SINK_BUCKET_NAME}/{s3_key}"
    )


def consume_stream():
    shard_iterators = get_all_shard_iterators(iterator_type="TRIM_HORIZON")
    buffer = []

    logger.info(
        f"Polling {STREAM_NAME} across {len(shard_iterators)} active shard(s)..."
    )

    for shard_id, iterator in list(shard_iterators.items()):
        if not iterator:
            continue

        try:
            response = kinesis.get_records(ShardIterator=iterator, Limit=100)
            # Advance iterator for this specific shard
            shard_iterators[shard_id] = response.get("NextShardIterator")

            records = response.get("Records", [])
            if records:
                logger.info(f"Fetched {len(records)} record(s) from shard {shard_id}")

            for record in records:
                payload = json.loads(record["Data"].decode("utf-8"))
                payload["processed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")
                buffer.append(payload)

                if len(buffer) >= BATCH_SIZE:
                    write_to_s3(buffer)
                    buffer.clear()

        except kinesis.exceptions.ExpiredIteratorException:
            logger.warning(f"Iterator expired for shard {shard_id}. Refreshing...")
            # Refresh iterator to latest sequence position
            resp = kinesis.get_shard_iterator(
                StreamName=STREAM_NAME,
                ShardId=shard_id,
                ShardIteratorType="LATEST",
            )
            shard_iterators[shard_id] = resp["ShardIterator"]

    time.sleep(1.0)
