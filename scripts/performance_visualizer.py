import pandas as pd
import matplotlib.pyplot as plt
import os

DATA_DIR = "backtesting/results"
CHART_DIR = "charts"
os.makedirs(CHART_DIR, exist_ok=True)

# Load and combine all yearly result CSVs
all_dfs = []
for file in sorted(os.listdir(DATA_DIR)):
    if file.endswith(".csv"):
        df = pd.read_csv(os.path.join(DATA_DIR, file))
        all_dfs.append(df)

if not all_dfs:
    raise ValueError("No backtest result files found in results directory.")

df = pd.concat(all_dfs, ignore_index=True)
df["date"] = pd.to_datetime(df["date"])

# Sort by date
df = df.sort_values("date")

# Calculate cumulative return over time
df["cumulative_return"] = (1 + df["pct_change"] / 100).cumprod()

# Outcome metrics
total_trades = len(df)
wins = df[df["outcome"] == "win"]
losses = df[df["outcome"] == "loss"]
win_rate = len(wins) / total_trades * 100
avg_gain = wins["pct_change"].mean()
avg_loss = losses["pct_change"].mean()
final_return = df["cumulative_return"].iloc[-1] - 1

# Print summary
print("Backtest Summary:")
print(f"Total Trades: {total_trades}")
print(f"Win Rate: {win_rate:.2f}%")
print(f"Average Gain: {avg_gain:.2f}%")
print(f"Average Loss: {avg_loss:.2f}%")
print(f"Cumulative Return: {final_return * 100:.2f}%")

# Equity curve plot
plt.figure(figsize=(10, 5))
plt.plot(df["date"], df["cumulative_return"])
plt.title("Equity Curve")
plt.xlabel("Date")
plt.ylabel("Cumulative Return")
plt.grid(True)
plt.tight_layout()
plt.savefig(os.path.join(CHART_DIR, "equity_curve.png"))
plt.close()

# Outcome distribution plot
plt.figure(figsize=(6, 4))
df["outcome"].value_counts().plot(kind="bar", color=["green", "red"])
plt.title("Trade Outcomes")
plt.ylabel("Count")
plt.tight_layout()
plt.savefig(os.path.join(CHART_DIR, "outcome_distribution.png"))
plt.close()

# Top tickers by count
top_tickers = df["ticker"].value_counts().head(10)
plt.figure(figsize=(8, 4))
top_tickers.plot(kind="bar", color="blue")
plt.title("Top 10 Traded Tickers")
plt.ylabel("Trades")
plt.tight_layout()
plt.savefig(os.path.join(CHART_DIR, "top_traded_tickers.png"))
plt.close()

# Top tickers by total return
ticker_returns = df.groupby("ticker")["pct_change"].sum().sort_values(ascending=False).head(10)
plt.figure(figsize=(8, 4))
ticker_returns.plot(kind="bar", color="purple")
plt.title("Top 10 Performing Tickers (Total % Gain)")
plt.ylabel("Total % Gain")
plt.tight_layout()
plt.savefig(os.path.join(CHART_DIR, "top_performing_tickers.png"))
plt.close()
