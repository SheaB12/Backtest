import os
import pandas as pd
from pathlib import Path

DATA_DIR = Path("backtesting/data")
RESULTS_DIR = Path("backtesting/results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

TRADE_LOG_PATH = RESULTS_DIR / "trade_log.csv"
SUMMARY_PATH = RESULTS_DIR / "summary.csv"

# Define strategy parameters
GAP_THRESHOLD = 0.04  # 4% gap up
BREAKOUT_BUFFER = 0.01  # 1% above open to enter
TARGET_PERCENT = 0.05  # take profit at 5%
STOP_PERCENT = 0.03    # stop loss at 3%

all_trades = []

def run_backtest_for_year(year):
    file_path = DATA_DIR / f"{year}-data.csv"
    if not file_path.exists():
        print(f"[!] Missing data for {year}")
        return

    df = pd.read_csv(file_path, parse_dates=["date"])
    df.sort_values(["date", "ticker"], inplace=True)

    grouped = df.groupby("date")

    for date, day_df in grouped:
        for _, row in day_df.iterrows():
            # Gap & Go strategy
            prev_close = row.get("prev_close")
            open_price = row["open"]
            if not prev_close or pd.isna(prev_close) or prev_close == 0:
                continue

            gap_percent = (open_price - prev_close) / prev_close
            if gap_percent < GAP_THRESHOLD:
                continue  # not a gap up

            breakout_entry = open_price * (1 + BREAKOUT_BUFFER)
            target_price = breakout_entry * (1 + TARGET_PERCENT)
            stop_price = breakout_entry * (1 - STOP_PERCENT)

            high = row["high"]
            low = row["low"]
            exit_price = None
            outcome = None

            if high >= target_price:
                exit_price = target_price
                outcome = "win"
            elif low <= stop_price:
                exit_price = stop_price
                outcome = "loss"
            else:
                exit_price = row["close"]
                outcome = "neutral"

            percent_gain = (exit_price - breakout_entry) / breakout_entry * 100

            all_trades.append({
                "date": date.strftime("%Y-%m-%d"),
                "ticker": row["ticker"],
                "entry": breakout_entry,
                "exit": exit_price,
                "outcome": outcome,
                "percent_gain": round(percent_gain, 2),
                "volume": row["volume"],
            })

def summarize_results():
    df = pd.DataFrame(all_trades)
    df.to_csv(TRADE_LOG_PATH, index=False)

    total_trades = len(df)
    wins = df[df["outcome"] == "win"]
    losses = df[df["outcome"] == "loss"]
    neutrals = df[df["outcome"] == "neutral"]

    summary = {
        "Total Trades": total_trades,
        "Wins": len(wins),
        "Losses": len(losses),
        "Neutrals": len(neutrals),
        "Win Rate (%)": round(len(wins) / total_trades * 100, 2) if total_trades else 0,
        "Avg Gain (%)": round(df["percent_gain"].mean(), 2) if total_trades else 0,
        "Total Return (%)": round(df["percent_gain"].sum(), 2) if total_trades else 0,
    }

    pd.DataFrame([summary]).to_csv(SUMMARY_PATH, index=False)
    print("[+] Backtest complete. Summary written to summary.csv")

if __name__ == "__main__":
    for year in range(2021, 2026):  # Change range as needed
        print(f"[+] Backtesting {year}...")
        run_backtest_for_year(year)

    summarize_results()
