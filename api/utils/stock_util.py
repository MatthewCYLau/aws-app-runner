import yfinance as yf


def check_asset_available(asset: str) -> bool:
    info = yf.Ticker(asset).history(period="7d", interval="1d")
    return len(info) > 0
