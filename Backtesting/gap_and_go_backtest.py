import os
import requests
import pandas as pd
from datetime import datetime, timedelta

API_KEY = os.getenv("POLYGON_API_KEY")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "../data")
START_DATE = datetime(2015, 5, 13)
END_DATE = datetime.today()

def fetch_grouped_data(date_str):
    url = (
        f"https://api.polygon.io/v2/aggs/grouped/locale/us/market/stocks/{date_str}"
        f"?adjusted=true&include_otc=false&apiKey={API_KEY}"
    )
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get("results", [])
    else:
        print(f"[!] Error fetching grouped data for {date_str}: {response.text}")
        return []

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    current = START_DATE
    yearly_data = {}

    while current <= END_DATE:
        date_str = current.strftime("%Y-%m-%d")
        print(f"[+] Processing {date_str}...")
        results = fetch_grouped_data(date_str)

        valid_rows = []
        for item in results:
            ticker = item.get("T")
            close = item.get("c", 0)
            open_ = item.get("o", 0)
            volume = item.get("v", 0)
            percent_change = ((close - open_) / open_ * 100) if open_ > 0 else 0

            if (
                1 <= close <= 100
                and volume > 1_000_000
                and percent_change > 5
            ):
                valid_rows.append({
                    "date": date_str,
                    "ticker": ticker,
                    "open": open_,
                    "high": item.get("h"),
                    "low": item.get("l"),
                    "close": close,
                    "volume": volume,
                    "percent_change": round(percent_change, 2)
                })

        if valid_rows:
            year = current.year
            if year not in yearly_data:
                yearly_data[year] = []
            yearly_data[year].extend(valid_rows)

        current += timedelta(days=1)

    for year, data in yearly_data.items():
        df = pd.DataFrame(data)
        path = os.path.join(OUTPUT_DIR, f"{year}-data.csv")
        df.to_csv(path, index=False)
        print(f"[+] Saved {len(df)} entries to {path}")

if __name__ == "__main__":
    main()
