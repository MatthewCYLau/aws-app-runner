import io
import os
import boto3
import pandas as pd

s3_client = boto3.client("s3")

PROCESSED_BUCKET = os.environ["PROCESSED_BUCKET"]


def lambda_handler(event, context):
    # Extract bucket and key from S3 trigger event
    raw_bucket = event["Records"][0]["s3"]["bucket"]["name"]
    raw_key = event["Records"][0]["s3"]["object"]["key"]

    # 1. Extract: Read CSV from S3
    response = s3_client.get_object(Bucket=raw_bucket, Key=raw_key)
    df = pd.read_csv(io.BytesIO(response["Body"].read()))

    # 2. Transform: Risk & PnL Metrics
    # Filter out cancelled/failed trades
    df = df[df["trade_status"] == "CONFIRMED"]

    # Calculate Net PnL per Portfolio
    df["net_pnl"] = df["realized_pnl"] + df["unrealized_pnl"]

    # Aggregate Risk Summary per Desk
    summary = (
        df.groupby("desk_id")
        .agg(
            total_net_pnl=("net_pnl", "sum"),
            total_exposure=("notional_usd", "sum"),
            var_95=("net_pnl", lambda x: x.quantile(0.05)),  # 95% Historical VaR
            trade_count=("trade_id", "count"),
        )
        .reset_index()
    )

    # Flag high risk desks (where 95% VaR loss exceeds threshold)
    summary["risk_flag"] = summary["var_95"] < -50000

    # 3. Load: Write transformed summary to Processed S3 Bucket as Parquet
    parquet_buffer = io.BytesIO()
    summary.to_parquet(parquet_buffer, index=False)

    processed_key = (
        f"risk_summaries/{raw_key.rsplit('/', 1)[-1].replace('.csv', '.parquet')}"
    )

    s3_client.put_object(
        Bucket=PROCESSED_BUCKET, Key=processed_key, Body=parquet_buffer.getvalue()
    )

    return {"status": "SUCCESS", "processed_key": processed_key}
