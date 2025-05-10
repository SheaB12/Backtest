import os
import pandas as pd

DATA_DIR = "data"
RESULTS_CSV = "gap_and_go_results.csv"
ML_DATASET_CSV = "gap_and_go_ml_dataset.csv"
SUMMARY_CSV = "gap_and_go_summary.csv"

def load_data_files():
    return sorted([f for f in os.listdir(DATA_DIR) if f.endswith("-data.csv")])

def simulate_trade_and_label(row):
    open_price = row["open"]
    high_price = row["high"]
    close_price = row["close"]
    volume = row["volume"]
    prev_close = row.get("prev_close", open_price / (1 + row["percent_change"] / 100))

    # Features
    gap_pct = (open_price - prev_close) / prev_close * 100
    intraday_range_pct = (high_price - open_price) / open_price * 100
    close_to_open_pct = (close_price - open_price) / open_price * 100
    day_of_week = pd.to_datetime(row["date"]).dayofweek  # 0=Mon, 4=Fri

    # Label
    target_gain = 0.02  # 2%
    actual_gain = (high_price - open_price) / open_price
    outcome = "win" if actual_gain >= target_gain else "loss"
    label = 1 if outcome == "win" else 0

    result = {
        "date": row["date"],
        "ticker": row["ticker"],
        "open": open_price,
        "high": high_price,
        "close": close_price,
        "volume": volume,
        "percent_change": row["percent_change"],
        "gap_pct": gap_pct,
        "intraday_range_pct": intraday_range_pct,
        "close_to_open_pct": close_to_open_pct,
        "day_of_week": day_of_week,
        "gain_pct": actual_gain * 100,
        "outcome": outcome,
        "label": label
    }

    return result

def summarize_results(df):
    wins = df[df["outcome"] == "win"]
    losses = df[df["outcome"] == "loss"]
    total = len(df)

    summary = {
        "Total Trades": total,
        "Wins": len(wins),
        "Losses": len(losses),
        "Win Rate (%)": round(len(wins) / total * 100, 2) if total else 0,
        "Average Gain (%)": round(df["gain_pct"].mean(), 2) if total else 0,
        "Total Return (%)": round(df["gain_pct"].sum(), 2) if total else 0,
    }

    pd.DataFrame([summary]).to_csv(SUMMARY_CSV, index=False)
    print(f"[+] Saved summary to {SUMMARY_CSV}")
    print(summary)

if __name__ == "__main__":
    all_files = load_data_files()
    all_trades = []

    for file in all_files:
        print(f"[+] Processing {file}...")
        df = pd.read_csv(os.path.join(DATA_DIR, file))

        # Strategy criteria: Gap and Go (gap up > 5%)
        filtered = df[df["percent_change"] > 5]

        trades = [simulate_trade_and_label(row) for _, row in filtered.iterrows()]
        all_trades.extend(trades)

    if all_trades:
        df_all = pd.DataFrame(all_trades)
        df_all.to_csv(RESULTS_CSV, index=False)
        df_all.to_csv(ML_DATASET_CSV, index=False)
        print(f"[+] Saved {len(df_all)} trades to {RESULTS_CSV} and {ML_DATASET_CSV}")
        summarize_results(df_all)
    else:
        print("[!] No qualifying trades found. No data saved.")
