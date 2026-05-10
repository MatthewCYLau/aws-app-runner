from decimal import Decimal

import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)
dynamodb = boto3.resource("dynamodb")
stocks_pnl_table = dynamodb.Table("stocks_pnl")


def main(event, context):
    for record in event["Records"]:
        if record["eventName"] in ["INSERT", "MODIFY"]:
            # Get the new and old values to calculate the change
            new_image = record["dynamodb"].get("NewImage", {})
            old_image = record["dynamodb"].get("OldImage", {})

            ticker = new_image["StockSymbol"]["S"]
            new_pnl = Decimal(new_image["TotalPnL"]["N"])
            old_pnl = Decimal(old_image.get("TotalPnL", {}).get("N", 0))

            # Calculate the difference (delta)
            pnl_delta = new_pnl - old_pnl

            # Atomic update in the aggregate table
            stocks_pnl_table.update_item(
                Key={"StockSymbol": ticker},
                UpdateExpression="ADD TotalPnL :val",
                ExpressionAttributeValues={":val": pnl_delta},
            )
