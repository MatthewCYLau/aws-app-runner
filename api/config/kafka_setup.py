import asyncio
import os
from api.config.logging import get_logger
from aiokafka import AIOKafkaConsumer
from kafka import KafkaProducer
import json

logger = get_logger(__name__)

KAFKA_TOPIC = "market-events"
KAFKA_HOST = os.getenv("KAFKA_HOST")


def get_kafka_producer():
    kafka_producer = KafkaProducer(
        bootstrap_servers=KAFKA_HOST,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )
    return kafka_producer


async def consume_kafka_messages():

    if not KAFKA_HOST:
        return

    consumer = AIOKafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_HOST,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="latest",
    )
    logger.info("Starting Kafka Polling consumer...")
    await consumer.start()
    try:
        async for msg in consumer:
            event = msg.value
            logger.info(event)
    except asyncio.CancelledError:
        pass
    finally:
        await consumer.stop()
