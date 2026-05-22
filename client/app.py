import streamlit as st
import pandas as pd
import boto3

st.title("📈 Stock PnL Tracker")

dynamodb = boto3.resource("dynamodb", region_name="us-east-1")


pnl_table = dynamodb.Table("positions_pnl")

items = []
response = pnl_table.scan()
items.extend(response.get("Items", []))

while "LastEvaluatedKey" in response:
    response = pnl_table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
    items.extend(response.get("Items", []))

df = pd.DataFrame(items)
df = df.set_index("PositionId")

st.subheader("PnL by postion ID")
st.dataframe(df.tail(10))

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
