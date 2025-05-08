import os
import pandas as pd
import requests
from datetime import datetime, timedelta

# --- Configuration ---
API_KEY = os.getenv("POLYGON_API_KEY")
BASE_URL = "https://api.polygon.io"
OUTPUT_DIR = os.path.abspath(os.path.join(".", "data"))
os.makedirs(OUTPUT_DIR, exist_ok=True)


def fetch_grouped_daily(date_str):
    url = f"{BASE_URL}/v2/aggs/grouped/locale/us/market/stocks/{date_str}"
    params = {
        "adjusted": "true",
        "include_otc": "false",
        "apiKey": API_KEY
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json().get("results", [])


def fetch_news_tickers(date_str):
    url = f"{BASE_URL}/v2/reference/news"
    params = {
        "published_utc.gte": f"{date_str}T00:00:00Z",
        "published_utc.lte": f"{date_str}T23:59:59Z",
        "apiKey": API_KEY
    }
    tickers_with_news = set()
    while url:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        for article in data.get("results", []):
            tickers_with_news.update([t['ticker'] for t in article.get("tickers", [])])
        url = data.get("next_url", None)
        params = {}  # already embedded in next_url
    return tickers_with_news


def percent_change(open_price, close_price):
    if open_price == 0:
        return 0
    return ((close_price - open_price) / open_price) * 100


def process_month(year, month):
    start_date = datetime(year, month, 1)
    next_month = (start_date.replace(day=28) + timedelta(days=4)).replace(day=1)
    end_date = next_month - timedelta(days=1)

    current_date = start_date
    all_data = []

    while current_date <= end_date and current_date < datetime.today():
        date_str = current_date.strftime("%Y-%m-%d")
        print(f"[+] Processing {date_str}")

        try:
            daily_data = fetch_grouped_daily(date_str)
            news_tickers = fetch_news_tickers(date_str)

            for stock in daily_data:
                ticker = stock.get("T")
                open_price = stock.get("o", 0)
                close_price = stock.get("c", 0)
                high = stock.get("h", 0)
                low = stock.get("l", 0)
                volume = stock.get("v", 0)

                if (
                    1 <= close_price <= 100
                    and volume > 1_000_000
                    and percent_change(open_price, close_price) > 5
                    and ticker in news_tickers
                ):
                    all_data.append({
                        "date": date_str,
                        "ticker": ticker,
                        "open": open_price,
                        "high": high,
                        "low": low,
                        "close": close_price,
                        "volume": volume,
                        "percent_change": round(percent_change(open_price, close_price), 2)
                    })

        except Exception as e:
            print(f"[!] Error on {date_str}: {e}")

        current_date += timedelta(days=1)

    if all_data:
        df = pd.DataFrame(all_data)
        output_file = os.path.join(OUTPUT_DIR, f"{year}-{month:02d}-data.csv")
        df.to_csv(output_file, index=False)
        print(f"[✓] Saved {len(df)} rows to {output_file}")
    else:
        print("[*] No qualifying data found this month.")


# Example: Last full month
today = datetime.today()
last_month = (today.replace(day=1) - timedelta(days=1))
process_month(last_month.year, last_month.month)
