# strategy_v4/io/TradeAnalyzer.py

import csv
from pathlib import Path
from typing import Dict, Any, List
from statistics import mean

class TradeAnalyzer:
    """
    交易分析器：
    - 讀取 trade_log.csv
    - 分群比較 v3/v4、不同 params_version 的績效
    - 計算勝率、平均盈虧、最大回撤
    """

    def __init__(self, log_path: str | Path = "trade_log.csv"):
        self.path = Path(log_path)
        self.trades: List[Dict[str, Any]] = []

    def load(self):
        """載入交易紀錄"""
        if not self.path.exists():
            print("[Analyzer] 無交易紀錄檔")
            return
        with self.path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            self.trades = [row for row in reader]

    def group_by_mode_version(self) -> Dict[str, List[Dict[str, Any]]]:
        """依 mode + params_version 分群"""
        groups: Dict[str, List[Dict[str, Any]]] = {}
        for trade in self.trades:
            key = f"{trade.get('mode','v3')}_{trade.get('params_version','unversioned')}"
            if key not in groups:
                groups[key] = []
            groups[key].append(trade)
        return groups

    def compute_stats(self, trades: List[Dict[str, Any]]) -> Dict[str, Any]:
        """計算統計數據"""
        profits = []
        max_drawdown = 0.0
        current_peak = 0.0

        for t in trades:
            try:
                pnl = float(t.get("unrealized_profit", 0.0))
            except ValueError:
                pnl = 0.0
            profits.append(pnl)

            # 計算回撤
            current_peak = max(current_peak, pnl)
            dd = current_peak - pnl
            max_drawdown = max(max_drawdown, dd)

        win_rate = sum(1 for p in profits if p > 0) / len(profits) if profits else 0.0
        avg_pnl = mean(profits) if profits else 0.0

        return {
            "count": len(profits),
            "win_rate": round(win_rate, 3),
            "avg_pnl": round(avg_pnl, 2),
            "max_drawdown": round(max_drawdown, 2),
        }

    def analyze(self):
        """分群分析並輸出結果"""
        self.load()
        groups = self.group_by_mode_version()
        results: Dict[str, Dict[str, Any]] = {}

        for key, trades in groups.items():
            stats = self.compute_stats(trades)
            results[key] = stats
            print(f"[Analyzer] {key} | 勝率={stats['win_rate']} | 平均盈虧={stats['avg_pnl']} | 最大回撤={stats['max_drawdown']} | 筆數={stats['count']}")

        return results
