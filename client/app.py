import yfinance as yf
import streamlit as st
import pandas as pd
import boto3

AWS_REGION = "us-east-1"
st.title("📈 Stock PnL Tracker")


def plot_position_daily_pnl(open_price: float, quantity: int, stock_symbol: str):

    data = yf.Ticker(stock_symbol)
    df = data.history(period="1mo")

    df["Daily PnL"] = (df["Close"] - open_price) * quantity
    dail_pnl_df = df[["Close", "Daily PnL"]]

    st.subheader(f"{stock_symbol} daily PnL")
    st.line_chart(dail_pnl_df)


def plot_position_pnl_timeseries(df: pd.DataFrame, position_id: str):

    position_df = df.loc[df["PositionId"] == position_id]

    if len(position_df):
        shocked_pnl_df = position_df[["ShockedPnL"]]

        st.subheader("Shocked PnL")
        st.line_chart(shocked_pnl_df)


dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
positions_pnl_aggregate_table = dynamodb.Table("positions_pnl_aggregate")

positions = []
response = positions_pnl_aggregate_table.scan()
positions.extend(response.get("Items", []))

while "LastEvaluatedKey" in response:
    response = positions_pnl_aggregate_table.scan(
        ExclusiveStartKey=response["LastEvaluatedKey"]
    )
    positions.extend(response.get("Items", []))

df = pd.DataFrame(positions)
df = df.set_index("PositionId")

st.subheader("Aggregate PnL by postion ID")
st.dataframe(df.tail(10))

positions_pnl_timeseries_table = dynamodb.Table("positions_pnl_timeseries")

positions_timeseries_data = []
response = positions_pnl_timeseries_table.scan()
positions_timeseries_data.extend(response.get("Items", []))

while "LastEvaluatedKey" in response:
    response = positions_pnl_timeseries_table.scan(
        ExclusiveStartKey=response["LastEvaluatedKey"]
    )
    positions_timeseries_data.extend(response.get("Items", []))

positions_timeseries_df = pd.DataFrame(positions_timeseries_data)
positions_timeseries_df = positions_timeseries_df.set_index("CreatedAt")
positions_timeseries_df["ShockedPnL"] = pd.to_numeric(
    positions_timeseries_df["ShockedPnL"]
)

for stock_position in positions:
    open_price = float(stock_position.get("OpenPrice"))
    quantity = int(stock_position.get("Quantity"))
    stock_symbol = stock_position.get("StockSymbol")
    plot_position_daily_pnl(open_price, quantity, stock_symbol)
    plot_position_pnl_timeseries(
        positions_timeseries_df, str(stock_position.get("PositionId"))
    )

stocks_pnl_table = dynamodb.Table("stocks_pnl")

items = []
response = stocks_pnl_table.scan()
items.extend(response.get("Items", []))

while "LastEvaluatedKey" in response:
    response = stocks_pnl_table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
    items.extend(response.get("Items", []))

df = pd.DataFrame(items)
df = df.set_index("StockSymbol")

st.subheader("PnL by stock symbol")
st.dataframe(df.tail(10))
