import os
import requests
import pandas as pd
from datetime import datetime, timedelta

POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
BASE_URL = "https://api.polygon.io/v2/aggs/ticker"

# Configure output directory
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
os.makedirs(OUTPUT_DIR, exist_ok=True)  # Ensure directory exists

def fetch_polygon_aggregates(ticker, start_date, end_date, timespan="minute", limit=5000):
    url = f"{BASE_URL}/{ticker}/range/1/{timespan}/{start_date}/{end_date}"
    params = {
        "adjusted": "true",
        "sort": "asc",
        "limit": limit,
        "apiKey": POLYGON_API_KEY
    }

    print(f"[+] Fetching {ticker}: {start_date} to {end_date}")
    response = requests.get(url, params=params)
    response.raise_for_status()

    data = response.json().get("results", [])
    if not data:
        print(f"[-] No data for {ticker} from {start_date} to {end_date}")
        return pd.DataFrame()

    df = pd.DataFrame(data)
    df['t'] = pd.to_datetime(df['t'], unit='ms')
    df.rename(columns={
        "t": "timestamp",
        "v": "volume",
        "o": "open",
        "h": "high",
        "l": "low",
        "c": "close"
    }, inplace=True)
    return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]

def save_to_csv(df, ticker):
    file_path = os.path.join(OUTPUT_DIR, f"{ticker}.csv")
    df.to_csv(file_path, index=False)
    print(f"[+] Saved {ticker} to {file_path}")
    return file_path

def download_and_save(ticker, start_date, end_date):
    df = fetch_polygon_aggregates(ticker, start_date, end_date)
    if not df.empty:
        return save_to_csv(df, ticker)
    return None

if __name__ == "__main__":
    # Example usage: download 1 week of data for AAPL
    ticker = "AAPL"
    end_date = datetime.today().date()
    start_date = end_date - timedelta(days=7)

    download_and_save(ticker, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
