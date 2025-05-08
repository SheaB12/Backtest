import os
import time
import requests
import pandas as pd
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

# === CONFIG ===
API_KEY = os.getenv("POLYGON_API_KEY")
BASE_URL = "https://api.polygon.io"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "../data")
DATE_FORMAT = "%Y-%m-%d"
START_DATE = datetime.now() - timedelta(days=7)  # For test, adjust later
END_DATE = datetime.now()
MIN_PRICE = 1
MAX_PRICE = 100
MIN_VOLUME = 1_000_000
MIN_PERCENT_CHANGE = 5

# === Ensure OUTPUT_DIR exists ===
if os.path.exists(OUTPUT_DIR):
    if not os.path.isdir(OUTPUT_DIR):
        os.remove(OUTPUT_DIR)
        os.makedirs(OUTPUT_DIR)
else:
    os.makedirs(OUTPUT_DIR)

# === Helper Functions ===

def fetch_grouped_daily(date_str):
    url = f"{BASE_URL}/v2/aggs/grouped/locale/us/market/stocks/{date_str}"
    params = {
        "adjusted": "true",
        "include_otc": "false",
        "apiKey": API_KEY
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    return data.get("results", [])

def fetch_news(ticker, date_str):
    url = f"{BASE_URL}/v2/reference/news"
    params = {
        "ticker": ticker,
        "published_utc.gte": f"{date_str}T00:00:00Z",
        "published_utc.lte": f"{date_str}T23:59:59Z",
        "apiKey": API_KEY
    }
    response = requests.get(url, params=params)
    if response.status_code == 429:
        time.sleep(2)
        response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    return len(data.get("results", [])) > 0

def percent_change(open_price, close_price):
    if open_price == 0:
        return 0
    return ((close_price - open_price) / open_price) * 100

# === Main Logic ===

def collect_monthly_data(start_date, end_date):
    current = start_date.replace(day=1)
    while current <= end_date:
        print(f"[+] Collecting {current.strftime('%Y-%m')}...")
        month_data = []

        month_end = (current + relativedelta(months=1)) - timedelta(days=1)
        date = current

        while date <= month_end and date <= end_date:
            date_str = date.strftime(DATE_FORMAT)
            try:
                results = fetch_grouped_daily(date_str)
                for stock in results:
                    try:
                        ticker = stock["T"]
                        open_price = stock["o"]
                        close_price = stock["c"]
                        volume = stock["v"]
                        high = stock["h"]
                        low = stock["l"]
                        change = percent_change(open_price, close_price)

                        if (
                            MIN_PRICE <= close_price <= MAX_PRICE
                            and volume > MIN_VOLUME
                            and change > MIN_PERCENT_CHANGE
                            and fetch_news(ticker, date_str)
                        ):
                            month_data.append({
                                "date": date_str,
                                "ticker": ticker,
                                "open": open_price,
                                "high": high,
                                "low": low,
                                "close": close_price,
                                "volume": volume,
                                "percent_change": round(change, 2)
                            })
                    except Exception as e:
                        print(f"[!] Error processing {stock.get('T')} on {date_str}: {e}")
                time.sleep(1)  # Avoid rate limits
            except Exception as e:
                print(f"[!] Error fetching {date_str}: {e}")
            date += timedelta(days=1)

        # Save to CSV
        if month_data:
            df = pd.DataFrame(month_data)
            filename = f"{current.strftime('%Y-%m')}-data.csv"
            filepath = os.path.join(OUTPUT_DIR, filename)
            df.to_csv(filepath, index=False)
            print(f"[+] Saved {len(df)} entries to {filepath}")
        else:
            print(f"[!] No qualifying data for {current.strftime('%Y-%m')}")

        current += relativedelta(months=1)

# === Entry Point ===

if __name__ == "__main__":
    collect_monthly_data(START_DATE, END_DATE)
