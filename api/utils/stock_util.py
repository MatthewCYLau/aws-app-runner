import yfinance as yf
import pandas as pd


def check_asset_available(asset: str) -> bool:
    info = yf.Ticker(asset).history(period="7d", interval="1d")
    return len(info) > 0

def fetch_live_snapshots(stock_symbol: str) -> pd.DataFrame:
    live_data = yf.download([stock_symbol], period="1d", interval="1m")
    
    latest_prices = live_data['Close'].ffill().iloc[-1]
    
    snapshot_df = pd.DataFrame({
        'Ticker': latest_prices.index,
        'Current_Price': latest_prices.values
    }).set_index('Ticker')
    
    return snapshot_df