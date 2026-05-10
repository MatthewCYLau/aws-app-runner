import boto3
import botocore


def lambda_handler(event, context):
    print(f"Boto3 version: {boto3.__version__}")
    print(f"Botocore version: {botocore.__version__}")
