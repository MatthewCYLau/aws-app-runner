from prometheus_client import Counter, Histogram, Gauge

AWS_TRANSACTION_COUNTER = Counter(
    "aws_transactions_total",
    "Total number of aws transactions",
    ["status", "type"],
)


TX_LATENCY = Histogram(
    "tx_duration_seconds",
    "Time spent processing transaction",
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0),
)


OPEN_POSITIONS_GAUGE = Gauge("open_positions", "Current open positions")
