import os
import pandas as pd

DATA_DIR = "data"
RESULTS_CSV = "gap_and_go_results.csv"
SUMMARY_CSV = "gap_and_go_summary.csv"

def load_data_files():
    return sorted([f for f in os.listdir(DATA_DIR) if f.endswith(".csv")])

def simulate_trade(row):
    open_price = row["open"]
    high_price = row["high"]
    close_price = row["close"]

    target_gain = 0.02  # 2%
    actual_gain = (high_price - open_price) / open_price

    result = {
        "date": row["date"],
        "ticker": row["ticker"],
        "open": open_price,
        "high": high_price,
        "low": row["low"],
        "close": close_price,
        "volume": row["volume"],
        "gap_percent": row.get("gap_percent", row.get("percent_change", 0)),
        "volatility": row.get("volatility", None),
        "gain_pct": round(actual_gain * 100, 2),
        "outcome": "win" if actual_gain >= target_gain else "loss",
    }
    return result

def summarize_results():
    df = pd.read_csv(RESULTS_CSV)

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
        path = os.path.join(DATA_DIR, file)
        print(f"[+] Backtesting {file}...")
        df = pd.read_csv(path)

        if "gap_percent" not in df.columns:
            print(f"[!] Skipping {file} (missing gap_percent)")
            continue

        # Strategy: Gap and Go (gap up > 5%)
        filtered = df[df["gap_percent"] > 5]

        trades = [simulate_trade(row) for _, row in filtered.iterrows()]
        all_trades.extend(trades)

    if all_trades:
        pd.DataFrame(all_trades).to_csv(RESULTS_CSV, index=False)
        print(f"[+] Saved {len(all_trades)} trades to {RESULTS_CSV}")
        summarize_results()
    else:
        print("[!] No trades matched the strategy.")
