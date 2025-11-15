# strategy_v4/backtest/ResultVisualizer.py

import pandas as pd
import matplotlib.pyplot as plt
from typing import Dict, Any

class ResultVisualizer:
    """
    回測結果視覺化：
    - 繪製盈虧曲線
    - 繪製勝率分布
    - 比較不同 mode/params_version 的績效
    """

    def __init__(self, trade_log_path: str = "trade_log.csv"):
        self.trade_log_path = trade_log_path
        self.df: pd.DataFrame | None = None

    def load(self):
        """載入交易紀錄"""
        self.df = pd.read_csv(self.trade_log_path, parse_dates=["timestamp"])
        return self.df

    def plot_pnl_curve(self):
        """繪製盈虧曲線"""
        if self.df is None:
            self.load()
        pnl_series = self.df["unrealized_profit"].fillna(0).cumsum()
        plt.figure(figsize=(10, 5))
        plt.plot(self.df["timestamp"], pnl_series, label="PnL Curve")
        plt.xlabel("Time")
        plt.ylabel("Cumulative PnL")
        plt.title("盈虧曲線")
        plt.legend()
        plt.grid(True)
        plt.show()

    def plot_winrate_distribution(self):
        """繪製勝率分布"""
        if self.df is None:
            self.load()
        wins = (self.df["unrealized_profit"].fillna(0) > 0).astype(int)
        plt.figure(figsize=(6, 4))
        plt.hist(wins, bins=2, rwidth=0.8)
        plt.xticks([0, 1], ["Loss", "Win"])
        plt.title("勝率分布")
        plt.show()

    def compare_versions(self):
        """比較不同 mode/params_version 的績效"""
        if self.df is None:
            self.load()
        grouped = self.df.groupby(["mode", "params_version"])["unrealized_profit"].sum()
        grouped.plot(kind="bar", figsize=(10, 5))
        plt.title("不同版本績效比較")
        plt.ylabel("總盈虧")
        plt.grid(True, axis="y")
        plt.show()
