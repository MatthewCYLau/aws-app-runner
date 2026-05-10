import boto3
import botocore
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def main(event, context):
    logger.info(f"Boto3 version: {boto3.__version__}")
    logger.info(f"Botocore version: {botocore.__version__}")
