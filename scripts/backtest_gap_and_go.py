import backtrader as bt
import os
import pandas as pd
from datetime import datetime

# --- Strategy Class ---
class GapAndGoWithPullback(bt.Strategy):
    params = dict(
        gap_threshold=0.05,     # 5%+ gap
        max_float=50_000_000,   # hypothetical float filter
        entry_buffer=0.01,      # enter a bit above premarket high
        risk_pct=0.01,          # 1% stop
        reward_multiplier=2     # 2R target
    )

    def __init__(self):
        self.order = None
        self.entry_price = None
        self.stop_price = None
        self.target_price = None
        self.prev_close = None
        self.premarket_high = None
        self.pullback_low = None
        self.breakout_confirmed = False

    def next(self):
        if len(self) < 2:
            return

        current_open = self.data.open[0]
        current_close = self.data.close[0]
        previous_close = self.data.close[-1]
        current_time = self.data.datetime.time(0)

        # GAP CHECK (only at 9:30 open)
        if self.data.datetime.datetime(0).time() == datetime.strptime("09:30", "%H:%M").time():
            gap_pct = (current_open - previous_close) / previous_close
            if gap_pct > self.params.gap_threshold:
                self.premarket_high = max([self.data.high[-i] for i in range(1, 16)])  # simulate premarket high
                self.prev_close = previous_close
                self.breakout_confirmed = True
            else:
                self.breakout_confirmed = False

        # GAP AND GO BREAKOUT
        if self.breakout_confirmed and not self.position and not self.order:
            if current_close > self.premarket_high * (1 + self.params.entry_buffer):
                self.entry_price = current_close
                self.stop_price = self.entry_price * (1 - self.params.risk_pct)
                self.target_price = self.entry_price * (1 + self.params.risk_pct * self.params.reward_multiplier)
                print(f"[BUY] {self.datetime.datetime(0)} - Entry: {self.entry_price:.2f}")
                self.order = self.buy()

        # MICRO PULLBACK ENTRY (only after breakout)
        if self.position and not self.order:
            if self.pullback_low is None and current_close < self.data.close[-1] < self.data.close[-2]:
                self.pullback_low = self.data.low[0]
            elif self.pullback_low and current_close > self.data.close[-1]:
                print(f"[ADD] Micro pullback confirmed at {self.datetime.datetime(0)}")
                self.buy()
                self.pullback_low = None  # Reset

        # EXIT
        if self.position:
            if current_close >= self.target_price:
                print(f"[SELL - TP] {self.datetime.datetime(0)} @ {current_close:.2f}")
                self.close()
            elif current_close <= self.stop_price:
                print(f"[SELL - SL] {self.datetime.datetime(0)} @ {current_close:.2f}")
                self.close()

    def notify_order(self, order):
        if order.status in [order.Completed, order.Canceled, order.Margin]:
            self.order = None


# --- Data Loader ---
def load_csv_as_feed(filepath):
    return bt.feeds.GenericCSVData(
        dataname=filepath,
        timeframe=bt.TimeFrame.Minutes,
        compression=1,
        dtformat='%Y-%m-%d %H:%M:%S',
        datetime=0,
        open=1,
        high=2,
        low=3,
        close=4,
        volume=5,
        openinterest=-1,
        headers=True
    )


# --- Backtest Runner ---
def run_backtest(csv_file):
    cerebro = bt.Cerebro()
    cerebro.addstrategy(GapAndGoWithPullback)

    data = load_csv_as_feed(csv_file)
    cerebro.adddata(data)

    cerebro.broker.set_cash(10_000)
    cerebro.broker.setcommission(commission=0.0025)
    cerebro.addsizer(bt.sizers.FixedSize, stake=100)

    print(f"\nStarting Portfolio Value: ${cerebro.broker.getvalue():.2f}")
    cerebro.run()
    print(f"Final Portfolio Value: ${cerebro.broker.getvalue():.2f}")
    cerebro.plot()


# --- Entry Point ---
if __name__ == '__main__':
    ticker = "AAPL"
    csv_path = os.path.join(os.path.dirname(__file__), '..', 'data', f'{ticker}_1min.csv')
    run_backtest(csv_path)
