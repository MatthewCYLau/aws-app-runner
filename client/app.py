import yfinance as yf
import streamlit as st
import pandas as pd
import boto3

from config.constants import AWS_REGION, columns_rename_map

st.title("📈 Stock PnL Tracker")


def plot_position_daily_pnl(open_price: float, quantity: int, stock_symbol: str):

    data = yf.Ticker(stock_symbol)
    df = data.history(period="1mo")

    df["Daily PnL"] = (df["Close"] - open_price) * quantity
    dail_pnl_df = df[["Close", "Daily PnL"]]

    st.subheader(f"{stock_symbol} daily PnL")
    st.line_chart(dail_pnl_df)


def plot_position_pnl_timeseries(df: pd.DataFrame, position_id: str):

    position_df = df.loc[df["Position Id"] == position_id]

    if len(position_df):
        shocked_pnl_df = position_df[["Shocked PnL"]]

        st.subheader("Shocked PnL")
        st.line_chart(shocked_pnl_df)


dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
positions_pnl_aggregate_table = dynamodb.Table("positions_pnl_aggregate")

positions_pnl_aggregate = []
response = positions_pnl_aggregate_table.scan()
positions_pnl_aggregate.extend(response.get("Items", []))

while "LastEvaluatedKey" in response:
    response = positions_pnl_aggregate_table.scan(
        ExclusiveStartKey=response["LastEvaluatedKey"]
    )
    positions_pnl_aggregate.extend(response.get("Items", []))

positions_pnl_aggregate_df = pd.DataFrame(positions_pnl_aggregate)

if not positions_pnl_aggregate_df.empty:
    positions_pnl_aggregate_df = positions_pnl_aggregate_df.rename(
        columns=columns_rename_map
    )
    positions_pnl_aggregate_df = positions_pnl_aggregate_df.set_index("Position Id")
    st.subheader("Aggregate PnL by postion ID")
    st.dataframe(positions_pnl_aggregate_df.tail(10))

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

if not positions_timeseries_df.empty:
    positions_timeseries_df = positions_timeseries_df.rename(columns=columns_rename_map)
    positions_timeseries_df = positions_timeseries_df.set_index("Created at")
    positions_timeseries_df["Shocked PnL"] = pd.to_numeric(
        positions_timeseries_df["Shocked PnL"]
    )

    mean_shocked_pnl = positions_timeseries_df.groupby(['Stock symbol'])['Shocked PnL'].mean()
    st.subheader("Mean shocked PnL by stock symbol")
    st.dataframe(mean_shocked_pnl.tail(10))


for stock_position in positions_pnl_aggregate:
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

stocks_pnl_df = pd.DataFrame(items)
if not stocks_pnl_df.empty:
    stocks_pnl_df = stocks_pnl_df.rename(columns=columns_rename_map)
    stocks_pnl_df = stocks_pnl_df.set_index("Stock symbol")

    st.subheader("PnL by stock symbol")
    st.dataframe(stocks_pnl_df.tail(10))
