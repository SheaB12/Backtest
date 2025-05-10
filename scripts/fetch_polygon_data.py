import os
import pandas as pd
from datetime import datetime, timedelta
from polygon import RESTClient

POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "../data")
os.makedirs(OUTPUT_DIR, exist_ok=True)

client = RESTClient(api_key=POLYGON_API_KEY)

def get_grouped_data(date_str):
    try:
        return client.get_grouped_daily_aggs(date_str)
    except Exception as e:
        print(f"[!] Error fetching {date_str}: {e}")
        return None

def get_news_tickers(date_str):
    try:
        news = client.list_ticker_news(published_utc=date_str)
        return {item.ticker for item in news}
    except:
        return set()

def calculate_features(row):
    try:
        percent_gap = ((row['open'] - row['prev_close']) / row['prev_close']) * 100
    except ZeroDivisionError:
        percent_gap = 0.0

    range_percent = ((row['high'] - row['low']) / row['low']) * 100 if row['low'] > 0 else 0.0
    body_percent = ((row['close'] - row['open']) / row['open']) * 100 if row['open'] > 0 else 0.0
    volatility = row['high'] - row['low']
    label = 1 if row['close'] > row['open'] else 0

    return pd.Series({
        'percent_gap': round(percent_gap, 2),
        'range_percent': round(range_percent, 2),
        'body_percent': round(body_percent, 2),
        'volatility': round(volatility, 2),
        'label': label
    })

def collect_year_data(year):
    start = datetime(year, 1, 1)
    end = datetime(year, 12, 31)
    all_data = []

    current = start
    while current <= end:
        date_str = current.strftime("%Y-%m-%d")
        print(f"[+] Processing {date_str}...")
        grouped = get_grouped_data(date_str)
        if not grouped:
            current += timedelta(days=1)
            continue

        news_tickers = get_news_tickers(date_str)

        for ag in grouped.results:
            ticker = ag.get('T')
            close = ag.get('c')
            open_ = ag.get('o')
            high = ag.get('h')
            low = ag.get('l')
            volume = ag.get('v')
            prev_close = ag.get('pc', None)

            if not all([ticker, close, open_, high, low, volume]):
                continue

            if prev_close is None:
                continue

            percent_change = ((close - prev_close) / prev_close) * 100
            if (
                1 <= close <= 100 and
                volume >= 1_000_000 and
                percent_change >= 5 and
                ticker in news_tickers
            ):
                row = {
                    "date": date_str,
                    "ticker": ticker,
                    "open": open_,
                    "high": high,
                    "low": low,
                    "close": close,
                    "volume": volume,
                    "percent_change": round(percent_change, 2),
                    "prev_close": prev_close
                }
                all_data.append(row)

        current += timedelta(days=1)

    if all_data:
        df = pd.DataFrame(all_data)
        features = df.apply(calculate_features, axis=1)
        final_df = pd.concat([df.drop(columns=['prev_close']), features], axis=1)
        path = os.path.join(OUTPUT_DIR, f"{year}-data.csv")
        final_df.to_csv(path, index=False)
        print(f"[+] Saved {len(final_df)} entries to {path}")
    else:
        print(f"[!] No qualifying entries for {year}")

# Example: Loop for backfill
for year in range(2015, datetime.now().year + 1):
    collect_year_data(year)
