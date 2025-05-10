import os
import time
import pandas as pd
from polygon import RESTClient
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load API key
load_dotenv()
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")

client = RESTClient(POLYGON_API_KEY)
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "../data")

START_DATE = datetime(2015, 1, 1)
END_DATE = datetime.now()

def fetch_grouped_data(date_str):
    try:
        return client.get_grouped_daily_aggs(date_str, adjusted=True)
    except Exception as e:
        print(f"[!] Error fetching grouped data for {date_str}: {e}")
        return []

def fetch_news(ticker, date_str):
    try:
        news = client.list_ticker_news(ticker=ticker, published_utc=date_str, order="desc", limit=1)
        return len(news.results) > 0
    except Exception:
        return False

def process_day(day):
    results = []
    day_str = day.strftime("%Y-%m-%d")
    aggs = fetch_grouped_data(day_str)
    for agg in aggs:
        if agg.volume < 1_000_000:
            continue
        if agg.close < 1 or agg.close > 100:
            continue
        if agg.open == 0:
            continue
        percent_change = ((agg.close - agg.open) / agg.open) * 100
        if percent_change < 5:
            continue
        if not fetch_news(agg.ticker, day_str):
            continue

        results.append({
            "date": day_str,
            "ticker": agg.ticker,
            "open": agg.open,
            "high": agg.high,
            "low": agg.low,
            "close": agg.close,
            "volume": agg.volume,
            "percent_change": round(percent_change, 2)
        })
        time.sleep(0.25)  # throttle to avoid hitting news rate limits
    return results

def save_yearly_data(year, data):
    if not data:
        print(f"[!] No qualifying entries for {year}")
        return
    df = pd.DataFrame(data, columns=[
        "date", "ticker", "open", "high", "low", "close", "volume", "percent_change"
    ])
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    file_path = os.path.join(OUTPUT_DIR, f"{year}-data.csv")
    df.to_csv(file_path, index=False)
    print(f"[+] Saved {len(df)} entries to {file_path}")

def main():
    current = START_DATE
    year_data = []
    last_year = current.year

    while current <= END_DATE:
        print(f"[+] Processing {current.strftime('%Y-%m-%d')}...")
        if current.year != last_year:
            save_yearly_data(last_year, year_data)
            year_data = []
            last_year = current.year

        day_data = process_day(current)
        year_data.extend(day_data)

        current += timedelta(days=1)

    save_yearly_data(last_year, year_data)

if __name__ == "__main__":
    main()
