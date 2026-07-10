import os

AWS_REGION = "us-east-1"
STOCK_TRADING_POSITIONS_TABLE = "stock_trading_positions"
POSITIONS_PNL_AGGREGATE = "positions_pnl_aggregate"
POSITIONS_PNL_TIMESERIES = "positions_pnl_timeseries"
STOCKS_PNL = "stocks_pnl"
S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME", "aws-app-runner-assets")
SQS_QUEUE_URL = os.environ.get(
    "SQS_QUEUE_URL",
    "https://sqs.us-east-1.amazonaws.com/830663695860/aws-app-task-queue",
)
MOUNT_PATH = "/data"
POSITIONS_CSV_COLUMNS = ["stock symbol", "open price", "quantity"]
