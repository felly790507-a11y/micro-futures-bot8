# strategy_v4/backtest/PerformanceReporter.py

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any

class PerformanceReporter:
    """
    回測績效報告：
    - 計算 Sharpe ratio
    - 平均持倉時間
    - 最大回撤
    - 輸出統計摘要
    """

    def __init__(self, trade_log_path: str = "trade_log.csv"):
        self.path = Path(trade_log_path)
        self.df: pd.DataFrame | None = None

    def load(self):
        """載入交易紀錄"""
        if not self.path.exists():
            print("[Reporter] 無交易紀錄檔")
            return None
        self.df = pd.read_csv(self.path, parse_dates=["timestamp"])
        return self.df

    def compute_sharpe(self, returns: pd.Series, risk_free_rate: float = 0.0) -> float:
        """計算 Sharpe ratio"""
        excess_returns = returns - risk_free_rate
        mean_excess = excess_returns.mean()
        std_excess = excess_returns.std()
        if std_excess == 0:
            return 0.0
        return round(mean_excess / std_excess * np.sqrt(len(returns)), 3)

    def compute_max_drawdown(self, pnl_series: pd.Series) -> float:
        """計算最大回撤"""
        cum_pnl = pnl_series.cumsum()
        peak = cum_pnl.expanding(min_periods=1).max()
        drawdown = (cum_pnl - peak)
        return round(drawdown.min(), 2)

    def compute_avg_holding_time(self) -> float:
        """計算平均持倉時間（tick 數）"""
        if self.df is None:
            self.load()
        return round(self.df["tick_since_entry"].fillna(0).mean(), 2)

    def report(self) -> Dict[str, Any]:
        """輸出統計摘要"""
        if self.df is None:
            self.load()
        if self.df is None or self.df.empty:
            return {}

        returns = self.df["unrealized_profit"].fillna(0)
        sharpe = self.compute_sharpe(returns)
        max_dd = self.compute_max_drawdown(returns)
        avg_hold = self.compute_avg_holding_time()

        summary = {
            "Sharpe_ratio": sharpe,
            "Max_drawdown": max_dd,
            "Avg_holding_ticks": avg_hold,
            "Total_trades": len(self.df)
        }

        print("[Performance Report]")
        for k, v in summary.items():
            print(f"{k}: {v}")

        return summary
