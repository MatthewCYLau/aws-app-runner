from io import StringIO
import json
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
import boto3
import os
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
from botocore.exceptions import ClientError
from api.config.database import Base, engine
from api.config.logging import get_logger
from api.product.views import router as product_router

logger = get_logger(__name__)


Base.metadata.create_all(bind=engine)

bucket_name = os.environ.get("S3_BUCKET_NAME", "aws-app-runner-assets")
sqs_queue_url = os.environ.get(
    "SQS_QUEUE_URL",
    "https://sqs.us-east-1.amazonaws.com/830663695860/aws-app-task-queue",
)


def receive_sqs_messages():
    sqs_client = boto3.client("sqs", region_name="us-east-1")
    try:
        response = sqs_client.receive_message(
            QueueUrl=sqs_queue_url, WaitTimeSeconds=20
        )

        messages = response.get("Messages", [])
        for msg in messages:
            try:
                body = json.loads(msg["Body"])
                logger.info(body)
                sqs_client.delete_message(
                    QueueUrl=sqs_queue_url, ReceiptHandle=msg["ReceiptHandle"]
                )
                logger.info("Task completed and deleted.")
            except Exception as e:
                logger.error(f"Error processing message: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = BackgroundScheduler()
    scheduler.add_job(receive_sqs_messages, "interval", minutes=1)
    scheduler.start()
    yield


app = FastAPI(lifespan=lifespan)


app.include_router(product_router)


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
            Bucket=bucket_name,
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
    s3_client.put_object(Bucket=bucket_name, Key=object_key, Body=csv_buffer.getvalue())
    logger.info(f"Successfully uploaded to {object_key}")
    return {"file_key": object_key}


@app.get("/get-s3-presigned-url")
def get_s3_presigned_url(file_key: str):
    s3_client = boto3.client("s3")
    try:
        s3_client.head_object(Bucket=bucket_name, Key=file_key)
        logger.info(f"Object with key {file_key} found!")
        url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket_name, "Key": file_key},
            ExpiresIn=86400,
        )
        return {"file_key": file_key, "presigned_url": url}

    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sqs")
def publish_sqs():
    sqs_client = boto3.client("sqs", region_name="us-east-1")
    try:
        response = sqs_client.send_message(
            QueueUrl=sqs_queue_url,
            MessageBody=json.dumps({"counter": int(get_random_int())}),
        )
        return {"status": "queued", "message_id": response.get("MessageId")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
