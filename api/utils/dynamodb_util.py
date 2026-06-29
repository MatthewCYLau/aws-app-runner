import boto3

from api.config.constants import AWS_REGION, STOCK_TRADING_POSITIONS_TABLE


def get_dynamodb_table_client(table_name: str):
    dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
    return dynamodb.Table(table_name)


def validate_position(position_id: str):
    positions_table = get_dynamodb_table_client(STOCK_TRADING_POSITIONS_TABLE)
    response = positions_table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key("PositionId").eq(
            str(position_id)
        )
    )
    items = response.get("Items", [])
    return items
