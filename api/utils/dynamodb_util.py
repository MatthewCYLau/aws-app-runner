import boto3

from api.config.constants import AWS_REGION


def get_dynamodb_table_client(table_name: str):
    dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
    return dynamodb.Table(table_name)
