import os
import requests
import pandas as pd
from datetime import datetime, timedelta

API_KEY = os.getenv("POLYGON_API_KEY")
OUTPUT_DIR = "data"
START_DATE = datetime(2015, 5, 13)
END_DATE = datetime(2025, 5, 12)

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

def compute_features_and_labels(data):
    df = pd.DataFrame(data)
    if df.empty:
        return pd.DataFrame()

    df["gap_percent"] = ((df["open"] - df["prev_close"]) / df["prev_close"]) * 100
    df["volatility"] = ((df["high"] - df["low"]) / df["open"]) * 100
    df["target_10pct_spike"] = ((df["high"] - df["open"]) / df["open"]) >= 0.10
    df["target_10pct_spike"] = df["target_10pct_spike"].astype(int)

    return df[[ 
        "date", "ticker", "open", "high", "low", "close", "volume",
        "gap_percent", "volatility", "target_10pct_spike"
    ]]

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
            try:
                close = item["c"]
                if 1 <= close <= 50:
                    valid_rows.append({
                        "date": date_str,
                        "ticker": item["T"],
                        "open": item["o"],
                        "high": item["h"],
                        "low": item["l"],
                        "close": close,
                        "volume": item["v"],
                        "prev_close": item["pc"]
                    })
            except KeyError:
                continue

        if valid_rows:
            year = current.year
            if year not in yearly_data:
                yearly_data[year] = []
            yearly_data[year].extend(valid_rows)

        current += timedelta(days=1)

    for year, data in yearly_data.items():
        df = compute_features_and_labels(data)
        if not df.empty:
            path = os.path.join(OUTPUT_DIR, f"{year}-data.csv")
            df.to_csv(path, index=False)
            print(f"[+] Saved {len(df)} entries to {path}")

if __name__ == "__main__":
    main()
