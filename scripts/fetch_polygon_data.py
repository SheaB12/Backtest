import os
import requests
import pandas as pd
from datetime import datetime

# --- Configuration ---
API_KEY = os.getenv("POLYGON_API_KEY")  # Automatically set by GitHub Actions
BASE_URL = "https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/minute/{start}/{end}"
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

def fetch_polygon_data(ticker, start_date, end_date):
    if not API_KEY:
        raise ValueError("POLYGON_API_KEY environment variable not set.")

    url = BASE_URL.format(
        ticker=ticker.upper(),
        start=start_date,
        end=end_date
    )

    params = {
        "adjusted": "true",
        "sort": "asc",
        "limit": 50000,
        "apiKey": API_KEY
    }

    print(f"[+] Fetching {ticker}: {start_date} to {end_date}")
    response = requests.get(url, params=params)
    response.raise_for_status()
    raw_data = response.json().get("results", [])

    if not raw_data:
        print(f"[!] No data returned for {ticker}")
        return None

    df = pd.DataFrame(raw_data)
    df["timestamp"] = pd.to_datetime(df["t"], unit="ms")
    df.rename(columns={
        "o": "open",
        "h": "high",
        "l": "low",
        "c": "close",
        "v": "volume"
    }, inplace=True)
    df = df[["timestamp", "open", "high", "low", "close", "volume"]]
    return df

def save_to_csv(df, ticker):
    os.makedirs(DATA_DIR, exist_ok=True)
    file_path = os.path.join(DATA_DIR, f"{ticker.upper()}_1min.csv")
    df.to_csv(file_path, index=False)
    print(f"[+] Saved to {file_path}")
    return file_path

def download_and_save(ticker, start_date, end_date):
    df = fetch_polygon_data(ticker, start_date, end_date)
    if df is not None:
        return save_to_csv(df, ticker)
    return None

# --- Example usage ---
if __name__ == "__main__":
    ticker = "AAPL"
    start_date = "2023-12-01"
    end_date = "2023-12-07"
    download_and_save(ticker, start_date, end_date)
