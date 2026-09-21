# generate_mock_trades.py
import pandas as pd
import numpy as np

np.random.seed(42)
n_rows = 1000

df = pd.DataFrame(
    {
        "trade_id": [f"TRD-{i:05d}" for i in range(n_rows)],
        "portfolio_id": np.random.choice(
            ["TECH_DESK", "MACRO_DESK", "FX_DESK"], n_rows
        ),
        "ticker": np.random.choice(["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"], n_rows),
        "side": np.random.choice(["BUY", "SELL"], n_rows, p=[0.55, 0.45]),
        "quantity": np.random.randint(10, 500, n_rows),
        "price": np.round(np.random.uniform(100.0, 500.0, n_rows), 2),
        "timestamp": pd.date_range(start="2026-01-01", periods=n_rows, freq="min"),
    }
)

# Save locally and push to S3
df.to_parquet("trades.parquet", index=False)
