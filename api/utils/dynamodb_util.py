import boto3


def get_dynamodb_table_client(table_name: str):
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    return dynamodb.Table(table_name)
