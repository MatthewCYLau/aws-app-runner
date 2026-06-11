import yfinance as yf
import streamlit as st
import pandas as pd
import boto3
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from config.constants import AWS_REGION, columns_rename_map

st.set_page_config(page_title="Stock Analytics", layout="wide")
st.title("📈 Stock PnL Tracker")
st.sidebar.header("User Input")
stock_sectors = pd.Series(["Tech", "Finance"], index=["AAPL", "JPM"])
positions_data = {}


def plot_position_daily_pnl(
    position_id: str,
    open_price: float,
    quantity: int,
    stock_symbol: str,
    period_input: str = "1mo",
):

    data = yf.Ticker(stock_symbol)
    df = data.history(period=period_input)

    df["Daily PnL"] = (df["Close"] - open_price) * quantity
    dail_pnl_df = df[["Close", "Daily PnL"]]

    st.subheader(f"{position_id} {stock_symbol} daily PnL")
    st.line_chart(dail_pnl_df)

    df["Daily Change %"] = df["Close"].pct_change() * 100
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["Close"],
            name="Close Price",
            line=dict(color="#1f77b4", width=2),
        ),
        secondary_y=False,
    )

    fig.add_trace(
        go.Bar(
            x=df.index,
            y=df["Daily Change %"],
            name="Daily Change %",
            marker=dict(color="#ff7f0e"),
            opacity=0.4,
        ),
        secondary_y=True,
    )

    fig.update_layout(
        title=f"{stock_symbol} Performance Summary",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=60, b=20),
        height=600,
    )

    fig.update_yaxes(title_text="Stock Price ($)", secondary_y=False)
    fig.update_yaxes(title_text="Daily Change (%)", secondary_y=True)

    st.plotly_chart(fig, width="stretch")


def plot_position_pnl_timeseries(df: pd.DataFrame, position_id: str):

    position_df = df.loc[df["Position Id"] == position_id]

    if len(position_df):
        shocked_pnl_df = position_df[["Shocked PnL"]]

        st.subheader(f"{position_id} Shocked PnL")
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

    positions_pnl_aggregate_df["Sector"] = positions_pnl_aggregate_df[
        "Stock symbol"
    ].map(stock_sectors)
    positions_pnl_aggregate_df["Sector"] = positions_pnl_aggregate_df["Sector"].fillna(
        "Unknown"
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

    mean_shocked_pnl = positions_timeseries_df.groupby(["Stock symbol"])[
        "Shocked PnL"
    ].agg(["mean", "max", "min"])
    st.subheader("Mean, max, and min shocked PnL by stock symbol")
    st.dataframe(mean_shocked_pnl.tail(10))

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
    stocks_pnl_df.sort_index(ascending=True, inplace=True)
    st.subheader("PnL by stock symbol")
    st.dataframe(stocks_pnl_df.tail(10))


for stock_position in positions_pnl_aggregate:
    postion_id = stock_position.get("PositionId")
    open_price = float(stock_position.get("OpenPrice"))
    quantity = int(stock_position.get("Quantity"))
    stock_symbol = stock_position.get("StockSymbol")
    positions_data[postion_id] = {
        "open_price": open_price,
        "quantity": quantity,
        "stock_symbol": stock_symbol,
    }

position_input = st.sidebar.selectbox("Position ID", positions_data.keys(), index=0)
period_input = st.sidebar.selectbox(
    "Time Period", ["1mo", "3mo", "6mo", "1y", "2y"], index=3
)

if position_input and period_input:
    open_price = positions_data[position_input]["open_price"]
    quantity = positions_data[position_input]["quantity"]
    stock_symbol = positions_data[position_input]["stock_symbol"]
    plot_position_daily_pnl(
        position_input, open_price, quantity, stock_symbol, period_input
    )
    plot_position_pnl_timeseries(
        positions_timeseries_df, str(stock_position.get("PositionId"))
    )
