import asyncio
from io import StringIO
import io
import json
import time
import aioboto3
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Response
import boto3
import matplotlib
import matplotlib.pyplot as plt

from pydantic import BaseModel
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from botocore.exceptions import ClientError
from api.config.constants import AWS_REGION, SQS_QUEUE_URL, S3_BUCKET_NAME
from api.config.database import Base, engine
from api.config.logging import get_logger
from api.config.metrics import AWS_TRANSACTION_COUNTER, TX_LATENCY
from api.product.views import router as product_router
from api.position.views import batch_update_pnl, router as position_router
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

logger = get_logger(__name__)

matplotlib.use("agg")

# Base.metadata.create_all(bind=engine)


class PlotRequest(BaseModel):
    file_key: str


def receive_sqs_messages():
    sqs_client = boto3.client("sqs", region_name=AWS_REGION)
    try:
        response = sqs_client.receive_message(
            QueueUrl=SQS_QUEUE_URL, WaitTimeSeconds=20
        )

        messages = response.get("Messages", [])
        for msg in messages:
            try:
                body = json.loads(msg["Body"])
                logger.info(body)
                sqs_client.delete_message(
                    QueueUrl=SQS_QUEUE_URL, ReceiptHandle=msg["ReceiptHandle"]
                )
                logger.info("Task completed and deleted.")
            except Exception as e:
                logger.error(f"Error processing message: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def process_message(message_body: str):
    logger.info("Processing message")
    message_dict = json.loads(message_body)
    logger.info(f"Counter is: {message_dict.get('counter')}")
    await asyncio.sleep(1)


async def poll_sqs_queue():
    logger.info("Starting SQS Polling consumer...")

    session = aioboto3.Session()

    async with session.client("sqs", region_name="us-east-1") as sqs_client:
        while True:
            try:
                response = await sqs_client.receive_message(
                    QueueUrl=SQS_QUEUE_URL,
                    MaxNumberOfMessages=10,
                    WaitTimeSeconds=20,
                    VisibilityTimeout=30,
                )

                messages = response.get("Messages", [])
                if not messages:
                    continue

                logger.info(f"Received {len(messages)} messages from SQS.")

                for message in messages:
                    try:
                        await process_message(message["Body"])

                        await sqs_client.delete_message(
                            QueueUrl=SQS_QUEUE_URL,
                            ReceiptHandle=message["ReceiptHandle"],
                        )
                    except Exception as msg_err:
                        logger.error(f"Failed to handle specific message: {msg_err}")

            except asyncio.CancelledError:
                logger.info(
                    "SQS Polling task caught cancellation signal. Exiting clean..."
                )
                break
            except Exception as e:
                logger.error(f"Error connection to SQS or polling: {e}")
                await asyncio.sleep(10)


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = AsyncIOScheduler()
    scheduler.add_job(receive_sqs_messages, "interval", minutes=1)
    scheduler.add_job(batch_update_pnl, "interval", minutes=1)
    scheduler.start()
    sqs_task = asyncio.create_task(poll_sqs_queue())

    yield

    logger.info("Shutting down background tasks...")
    scheduler.shutdown()

    sqs_task.cancel()
    try:
        await sqs_task
    except asyncio.CancelledError:
        logger.error("SQS Polling task successfully stopped.")


app = FastAPI(lifespan=lifespan)


app.include_router(product_router)
app.include_router(position_router)


@app.get("/")
def up():
    return "Up!"


def get_random_int(max: int = 100):
    return np.random.randint(max, size=1)[0]


def generate_df(size: int = 100):
    values = np.random.normal(loc=10, scale=size, size=size)
    series = pd.Series(values, index=list(range(size)), name="series")

    df = pd.DataFrame(series)
    return df


def stream_text_to_s3(text_content, object_key):

    s3_client = boto3.client("s3")

    try:
        s3_client.put_object(
            Body=text_content,
            Bucket=S3_BUCKET_NAME,
            Key=object_key,
            ContentType="text/plain",
        )
        logger.info(f"Successfully uploaded to {object_key}")
    except ClientError as e:
        logger.error(f"AWS Error: {e.response['Error']['Message']}")
    except Exception as e:
        logger.error(f"Contextual Error: {e}")


@app.post("/upload-s3")
def upload_s3():
    report_data = "Date,User,Action\n2026-04-17,Admin,Login"
    stream_text_to_s3(report_data, "daily_report.csv")
    return "Done!"


@app.post("/upload-dataframe-s3")
def upload_dataframe_s3():
    df = generate_df()
    s3_client = boto3.client("s3")

    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    object_key = f"{get_random_int()}_dataframe.csv"
    s3_client.put_object(
        Bucket=S3_BUCKET_NAME, Key=object_key, Body=csv_buffer.getvalue()
    )
    logger.info(f"Successfully uploaded to {object_key}")
    return {"file_key": object_key}


@app.get("/get-s3-presigned-url")
def get_s3_presigned_url(file_key: str):
    s3_client = boto3.client("s3")
    try:
        s3_client.head_object(Bucket=S3_BUCKET_NAME, Key=file_key)
        logger.info(f"Object with key {file_key} found!")

        s3_path = f"s3://{S3_BUCKET_NAME}/{file_key}"
        df = pd.read_csv(s3_path)

        logger.info(f"{'-' * 10}First ten values{'-' * 10}")

        logger.info(df.iloc[:10]["series"].values.tolist())

        url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": S3_BUCKET_NAME, "Key": file_key},
            ExpiresIn=86400,
        )
        return {"file_key": file_key, "presigned_url": url}

    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/plot-df-upload-s3")
def plot_df_upload_s3(request_data: PlotRequest):

    file_key = request_data.file_key

    s3_client = boto3.client("s3")
    s3_client.head_object(Bucket=S3_BUCKET_NAME, Key=file_key)
    logger.info(f"Object with key {file_key} found!")

    s3_path = f"s3://{S3_BUCKET_NAME}/{file_key}"
    df = pd.read_csv(s3_path)

    plot = df.plot(title="Series values")
    fig = plot.get_figure()

    img_buffer = io.BytesIO()
    fig.savefig(img_buffer, format="png")
    img_buffer.seek(0)

    s3 = boto3.client("s3")
    image_file_key = f"plots/{file_key.replace('.csv', '')}.png"

    try:
        s3.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=file_key,
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
    finally:
        plt.close(fig)  # Free up memory


@app.post("/sqs")
def publish_sqs():
    start_time = time.perf_counter()
    sqs_client = boto3.client("sqs", region_name="us-east-1")
    try:
        response = sqs_client.send_message(
            QueueUrl=SQS_QUEUE_URL,
            MessageBody=json.dumps({"counter": int(get_random_int())}),
        )
        AWS_TRANSACTION_COUNTER.labels(status="in_progress", type="sqs").inc()
        return {"status": "queued", "message_id": response.get("MessageId")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        end_time = time.perf_counter()
        duration = start_time - end_time
        TX_LATENCY.observe(duration)


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
