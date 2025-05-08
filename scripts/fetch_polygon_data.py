import os
import requests
import pandas as pd
from datetime import datetime, timedelta

# Environment variable for your Polygon.io API key
POLYGON_API_KEY = os.getenv('POLYGON_API_KEY')
assert POLYGON_API_KEY, "POLYGON_API_KEY not set in environment."

# Constants
BASE_URL = "https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/minute/{start}/{end}"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "../data")

# Ensure OUTPUT_DIR exists and is a directory
if os.path.exists(OUTPUT_DIR):
    if not os.path.isdir(OUTPUT_DIR):
        os.remove(OUTPUT_DIR)  # remove file that's blocking the path
        os.makedirs(OUTPUT_DIR)
else:
    os.makedirs(OUTPUT_DIR)

def fetch_intraday_data(ticker: str, start: str, end: str) -> pd.DataFrame:
    url = BASE_URL.format(ticker=ticker, start=start, end=end)
    params = {
        "adjusted": "true",
        "sort": "asc",
        "limit": 50000,
        "apiKey": POLYGON_API_KEY
    }
    print(f"[+] Fetching {ticker}: {start} to {end}")
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json().get("results", [])
    if not data:
        return pd.DataFrame()
    
    df = pd.DataFrame(data)
    df['timestamp'] = pd.to_datetime(df['t'], unit='ms')
    df = df[['timestamp', 'o', 'h', 'l', 'c', 'v']]
    df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    return df

def save_to_csv(df: pd.DataFrame, ticker: str):
    if df.empty:
        print(f"[!] No data for {ticker}. Skipping CSV.")
        return
    file_path = os.path.join(OUTPUT_DIR, f"{ticker}.csv")
    df.to_csv(file_path, index=False)
    print(f"[+] Saved {ticker} to {file_path}")

def download_and_save(ticker: str, start: str, end: str):
    df = fetch_intraday_data(ticker, start, end)
    save_to_csv(df, ticker)

if __name__ == "__main__":
    # Example usage
    ticker = "AAPL"
    start_date = "2023-12-01"
    end_date = "2023-12-07"
    download_and_save(ticker, start_date, end_date)
