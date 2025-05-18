import os
import requests
import pandas as pd
import json
from datetime import datetime, timedelta

API_KEY = os.getenv("POLYGON_API_KEY")
OUTPUT_DIR = "data"
DEBUG_ALL = "debug_all_tickers.csv"
DEBUG_FILTERED = "debug_filtered_tickers.csv"
RAW_JSON_DIR = "raw_json"
START_DATE = datetime(2023, 10, 10)
END_DATE = datetime(2023, 10, 11)

def fetch_grouped_data(date_str):
    url = (
        f"https://api.polygon.io/v2/aggs/grouped/locale/us/market/stocks/{date_str}"
        f"?adjusted=true&include_otc=false&apiKey={API_KEY}"
    )
    response = requests.get(url)
    if response.status_code == 200:
        results = response.json().get("results", [])
        os.makedirs(RAW_JSON_DIR, exist_ok=True)
        with open(os.path.join(RAW_JSON_DIR, f"{date_str}.json"), "w") as f:
            json.dump(results, f, indent=2)
        return results
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
    print(f"[INFO] Using API key: {API_KEY[:4]}...{API_KEY[-4:]}" if API_KEY else "[!] Missing API key!")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    all_tickers = []
    filtered_tickers = []
    yearly_data = {}

    current = START_DATE
    while current <= END_DATE:
        date_str = current.strftime("%Y-%m-%d")
        print(f"[+] Processing {date_str}...")
        results = fetch_grouped_data(date_str)
        print(f"  Retrieved {len(results)} results")

        for item in results:
            row = {
                "date": date_str,
                "ticker": item.get("T"),
                "open": item.get("o"),
                "high": item.get("h"),
                "low": item.get("l"),
                "close": item.get("c"),
                "volume": item.get("v"),
                "prev_close": item.get("pc"),
                "reason": "VALID"
            }

            # Start rejection diagnostics
            if not all([row["open"], row["close"], row["prev_close"], row["volume"]]):
                row["reason"] = "MISSING_KEY_DATA"
            elif not (1 <= row["close"] <= 100):
                row["reason"] = "CLOSE_OUT_OF_RANGE"
            elif row["volume"] <= 1_000_000:
                row["reason"] = "LOW_VOLUME"
            else:
                percent_change = ((row["close"] - row["open"]) / row["open"]) * 100 if row["open"] > 0 else 0
                if percent_change <= 5:
                    row["reason"] = "LOW_PERCENT_CHANGE"

            # Append to debug all
            all_tickers.append(row.copy())

            # Keep only those passing all filters
            if row["reason"] == "VALID":
                filtered_tickers.append(row.copy())
                year = current.year
                if year not in yearly_data:
                    yearly_data[year] = []
                yearly_data[year].append(row.copy())

        current += timedelta(days=1)

    # Save results
    if all_tickers:
        pd.DataFrame(all_tickers).to_csv(DEBUG_ALL, index=False)
        print(f"[+] Saved ALL tickers to {DEBUG_ALL}")

    if filtered_tickers:
        pd.DataFrame(filtered_tickers).to_csv(DEBUG_FILTERED, index=False)
        print(f"[+] Saved FILTERED tickers to {DEBUG_FILTERED}")

    for year, rows in yearly_data.items():
        df = compute_features_and_labels(rows)
        if not df.empty:
            out_path = os.path.join(OUTPUT_DIR, f"{year}-data.csv")
            df.to_csv(out_path, index=False)
            print(f"[+] Final ML dataset saved to {out_path}")

if __name__ == "__main__":
    main()
