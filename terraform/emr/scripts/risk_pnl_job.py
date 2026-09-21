import sys
from pyspark.sql import SparkSession
from pyspark.sql import functions as F


def main():
    if len(sys.argv) < 3:
        print("Usage: risk_pnl_job.py <input_s3_path> <output_s3_path>")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]

    spark = SparkSession.builder.appName("RiskPnLCalculator").getOrCreate()

    # Read trades data
    df = spark.read.parquet(input_path)

    # Compute Net Quantities & Cash Flows
    pnl_df = (
        df.withColumn(
            "signed_quantity",
            F.when(F.col("side") == "BUY", F.col("quantity")).otherwise(
                -F.col("quantity")
            ),
        )
        .withColumn("cash_flow", -F.col("signed_quantity") * F.col("price"))
        .groupBy("portfolio_id", "ticker")
        .agg(
            F.sum("signed_quantity").alias("net_position"),
            F.sum("cash_flow").alias("net_cash_flow"),
        )
    )

    # Output partitioned Parquet back to S3
    pnl_df.write.mode("overwrite").partitionBy("portfolio_id").parquet(output_path)

    spark.stop()


if __name__ == "__main__":
    main()
