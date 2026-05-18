import streamlit as st
import pandas as pd
import numpy as np

st.title("📈 Simple Stock PnL Tracker")

# 1. Create a minimal dummy dataset
np.random.seed(42)
dates = pd.date_range(start="2026-01-01", periods=30, freq="D")

df = pd.DataFrame(
    {
        "Date": dates,
        "AAPL": np.random.normal(50, 200, size=30).cumsum(),
        "TSLA": np.random.normal(20, 400, size=30).cumsum(),
        "NVDA": np.random.normal(100, 300, size=30).cumsum(),
    }
)
df = df.set_index("Date")

# 2. Display an interactive line chart of the PnL
st.subheader("Cumulative Position PnL ($)")
st.line_chart(df)

# 3. Display the raw data table below it
st.subheader("Raw Data Summary")
st.dataframe(df.tail(10))  # Shows the last 10 days of trading
