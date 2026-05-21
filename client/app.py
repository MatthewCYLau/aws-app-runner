import streamlit as st
import pandas as pd
import boto3

st.title("📈 Stock PnL Tracker")

dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
stocks_pnl_table = dynamodb.Table("stocks_pnl")

items = []
response = stocks_pnl_table.scan()
items.extend(response.get("Items", []))

while "LastEvaluatedKey" in response:
    response = stocks_pnl_table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
    items.extend(response.get("Items", []))

df = pd.DataFrame(items)
df = df.set_index("StockSymbol")

# 3. Display the raw data table below it
st.subheader("Raw Data Summary")
st.dataframe(df.tail(10))  # Shows the last 10 days of trading
