import os
import requests
import pandas as pd
from datetime import datetime, timedelta

API_KEY = os.getenv("POLYGON_API_KEY")
OUTPUT_DIR = "data"
DEBUG_FILTERED = "debug_filtered_tickers.csv"
DEBUG_ALL = "debug_all_tickers.csv"
START_DATE = datetime(2023, 1, 1)
END_DATE = datetime(2023, 1, 7)

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
    debug_filtered = []
    debug_all = []
    yearly_data = {}

    current = START_DATE
    while current <= END_DATE:
        date_str = current.strftime("%Y-%m-%d")
        print(f"[+] Processing {date_str}...")
        results = fetch_grouped_data(date_str)
        print(f"  Retrieved {len(results)} results")

        valid_rows = []
        for item in results:
            try:
                close = item.get("c")
                open_ = item.get("o")
                prev_close = item.get("pc")
                volume = item.get("v")
                high = item.get("h")
                low = item.get("l")
                ticker = item.get("T")

                # Log everything regardless of filtering
                debug_all.append({
                    "date": date_str,
                    "ticker": ticker,
                    "open": open_,
                    "high": high,
                    "low": low,
                    "close": close,
                    "volume": volume,
                    "prev_close": prev_close
                })

                if not all([open_, close, prev_close, volume]):
                    continue

                percent_change = ((close - open_) / open_ * 100) if open_ > 0 else 0

                if (
                    1 <= close <= 100
                    and volume > 1_000_000
                    and percent_change > 5
                ):
                    row = {
                        "date": date_str,
                        "ticker": ticker,
                        "open": open_,
                        "high": high,
                        "low": low,
                        "close": close,
                        "volume": volume,
                        "prev_close": prev_close
                    }
                    valid_rows.append(row)
                    debug_filtered.append(row)

            except Exception as e:
                print(f"[!] Exception while parsing row: {e}")
                continue

        print(f"  Filtered {len(valid_rows)} valid rows")

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
        else:
            print(f"[!] No trades met criteria for year {year}")

    if debug_filtered:
        pd.DataFrame(debug_filtered).to_csv(DEBUG_FILTERED, index=False)
        print(f"[+] Debug filtered log saved to {DEBUG_FILTERED}")

    if debug_all:
        pd.DataFrame(debug_all).to_csv(DEBUG_ALL, index=False)
        print(f"[+] Debug ALL tickers log saved to {DEBUG_ALL}")

if __name__ == "__main__":
    main()
