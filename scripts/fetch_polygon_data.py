import requests
import pandas as pd
import os
from datetime import datetime, timedelta

# --- CONFIGURATION ---
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")  # Make sure this is set in your environment
BASE_URL = "https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/minute/{start}/{end}"
OUTPUT_DIR = "polygon_data"

def fetch_intraday_data(ticker, start_date, end_date):
    url = BASE_URL.format(
        ticker=ticker.upper(),
        start=start_date,
        end=end_date
    )
    params = {
        "adjusted": "true",
        "sort": "asc",
        "limit": 50000,
        "apiKey": POLYGON_API_KEY
    }

    print(f"Fetching data for {ticker} from {start_date} to {end_date}...")
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json().get("results", [])

    if not data:
        print(f"No data returned for {ticker}.")
        return None

    df = pd.DataFrame(data)
    df["timestamp"] = pd.to_datetime(df["t"], unit='ms')
    df = df.rename(columns={
        "o": "open",
        "h": "high",
        "l": "low",
        "c": "close",
        "v": "volume"
    })

    df = df[["timestamp", "open", "high", "low", "close", "volume"]]
    return df

def save_to_csv(df, ticker):
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    file_path = os.path.join(OUTPUT_DIR, f"{ticker.upper()}_1min.csv")
    df.to_csv(file_path, index=False)
    print(f"Saved: {file_path}")
    return file_path

def download_and_save(ticker, start_date, end_date):
    df = fetch_intraday_data(ticker, start_date, end_date)
    if df is not None:
        return save_to_csv(df, ticker)
    return None

# --- EXAMPLE USAGE ---
if __name__ == "__main__":
    ticker = "AAPL"
    start = "2023-12-01"
    end = "2023-12-07"
    download_and_save(ticker, start, end)
