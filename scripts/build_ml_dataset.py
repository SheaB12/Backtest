import os
import pandas as pd
from datetime import datetime

DATA_DIR = "./Data"
OUTPUT_CSV = "./Backtesting/results/gap_and_go_ml_dataset.csv"

def load_data_files():
    return sorted([
        os.path.join(DATA_DIR, f)
        for f in os.listdir(DATA_DIR)
        if f.endswith(".csv") and f[:4].isdigit()
    ])

def extract_features_and_label(row):
    open_price = row["open"]
    high_price = row["high"]
    close_price = row["close"]
    volume = row["volume"]
    percent_change = row["percent_change"]
    prev_close = row.get("prev_close", open_price / (1 + percent_change / 100))

    # Features
    gap_pct = (open_price - prev_close) / prev_close * 100
    intraday_range_pct = (high_price - open_price) / open_price * 100
    close_to_open_pct = (close_price - open_price) / open_price * 100
    day_of_week = datetime.strptime(row["date"], "%Y-%m-%d").weekday()  # 0=Mon, 4=Fri
    volume = row["volume"]

    # Label (did high reach 2% above open)
    target_gain = 0.02
    actual_gain = (high_price - open_price) / open_price
    label = 1 if actual_gain >= target_gain else 0

    return {
        "date": row["date"],
        "ticker": row["ticker"],
        "open": open_price,
        "high": high_price,
        "close": close_price,
        "volume": volume,
        "percent_change": percent_change,
        "gap_pct": gap_pct,
        "intraday_range_pct": intraday_range_pct,
        "close_to_open_pct": close_to_open_pct,
        "day_of_week": day_of_week,
        "gain_pct": actual_gain * 100,
        "label": label
    }

def build_ml_dataset():
    files = load_data_files()
    all_rows = []

    for file in files:
        print(f"[+] Processing {file}")
        df = pd.read_csv(file)

        if "percent_change" not in df.columns:
            print(f"[!] Skipping {file}: missing 'percent_change'")
            continue

        filtered = df[df["percent_change"] > 5]

        trades = [extract_features_and_label(row) for _, row in filtered.iterrows()]
        all_rows.extend(trades)

    if all_rows:
        df_out = pd.DataFrame(all_rows)
        os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
        df_out.to_csv(OUTPUT_CSV, index=False)
        print(f"[+] Saved ML dataset with {len(df_out)} rows to {OUTPUT_CSV}")
    else:
        print("[!] No data matched criteria across all files.")

if __name__ == "__main__":
    build_ml_dataset()
