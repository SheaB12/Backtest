import os
import pandas as pd
from datetime import datetime, timedelta
from polygon import RESTClient
import time

POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "../data")
START_YEAR = 2015
END_YEAR = datetime.now().year

client = RESTClient(POLYGON_API_KEY)


def fetch_grouped_daily(date_str):
    try:
        response = client.get_grouped_daily_aggs(
            locale="us",
            market="stocks",
            date=date_str,
            adjusted=True
        )
        return response.results if response.results else []
    except Exception as e:
        print(f"[!] Error fetching grouped data for {date_str}: {e}")
        return []


def fetch_news(ticker, date):
    try:
        news = client.list_ticker_news(ticker=ticker, published_utc=date, limit=1)
        return len(news.results) > 0 if news.results else False
    except:
        return False


def percent_change(open_price, close_price):
    if open_price == 0:
        return 0
    return ((close_price - open_price) / open_price) * 100


def meets_criteria(stock, date_str):
    try:
        ticker = stock["T"]
        open_price = stock["o"]
        close_price = stock["c"]
        volume = stock["v"]
        is_otc = ticker.startswith("OTC")

        if is_otc or open_price < 1 or close_price > 100 or volume < 1_000_000:
            return False

        change = percent_change(open_price, close_price)
        if change < 5:
            return False

        return fetch_news(ticker, date_str)
    except Exception as e:
        print(f"[!] Error filtering stock {stock}: {e}")
        return False


def run_backtest():
    for year in range(START_YEAR, END_YEAR + 1):
        print(f"[+] Backtesting {year}...")
        yearly_data = []

        start_date = datetime(year, 1, 1)
        end_date = datetime(year, 12, 31)
        current_date = start_date

        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            stocks = fetch_grouped_daily(date_str)

            for stock in stocks:
                if meets_criteria(stock, date_str):
                    yearly_data.append({
                        "date": date_str,
                        "ticker": stock["T"],
                        "open": stock["o"],
                        "high": stock["h"],
                        "low": stock["l"],
                        "close": stock["c"],
                        "volume": stock["v"],
                        "percent_change": round(percent_change(stock["o"], stock["c"]), 2)
                    })

            current_date += timedelta(days=1)
            time.sleep(1)  # basic rate-limit control

        if yearly_data:
            df = pd.DataFrame(yearly_data, columns=[
                "date", "ticker", "open", "high", "low", "close", "volume", "percent_change"
            ])
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            file_path = os.path.join(OUTPUT_DIR, f"{year}-data.csv")
            df.to_csv(file_path, index=False)
            print(f"[+] Saved {len(df)} entries to {file_path}")
        else:
            print(f"[!] No qualifying entries for {year}")


if __name__ == "__main__":
    run_backtest()
