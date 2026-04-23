import json

from fastapi import FastAPI, HTTPException
import boto3
import os
from botocore.exceptions import ClientError
from api.config.database import Base, engine
from api.config.logging import get_logger
from api.product.views import router as product_router

logger = get_logger(__name__)


Base.metadata.create_all(bind=engine)


app = FastAPI()

app.include_router(product_router)

bucket_name = os.environ.get("S3_BUCKET_NAME")
sqs_queue_url = os.environ.get("SQS_QUEUE_URL")


@app.get("/")
def up():
    return "Up!"


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


@app.get("/get-s3-presigned-url")
def get_s3_presigned_url(file_key: str):
    s3_client = boto3.client("s3")
    try:
        url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket_name, "Key": file_key},
            ExpiresIn=86400,
        )
        return {"file_key": file_key, "presigned_url": url}

    except ClientError as e:
        # Log the error and return a 500 status
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sqs")
def publish_sqs():
    sqs_client = boto3.client("sqs", region_name="us-east-1")
    try:
        response = sqs_client.send_message(
            QueueUrl=sqs_queue_url, MessageBody=json.dumps({"body": "hello world!"})
        )
        return {"status": "queued", "message_id": response.get("MessageId")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sqs")
def received_sqs():
    sqs_client = boto3.client("sqs", region_name="us-east-1")
    try:
        response = sqs_client.receive_message(
            QueueUrl=sqs_queue_url, MaxNumberOfMessages=1, WaitTimeSeconds=20
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
