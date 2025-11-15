# strategy_v4/io/TradeLogger.py

import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

class TradeLogger:
    """
    交易紀錄器：
    - 記錄進場、出場、停損、停利、加碼等事件
    - 支援 v3/v4 模式，增加 mode、params_version、entry_score_v2、exit_score_v2 欄位
    """

    def __init__(self, log_path: str | Path = "trade_log.csv"):
        self.path = Path(log_path)
        self._initialized = False

    def _init_file(self):
        """初始化 CSV 檔案，建立標題列"""
        if not self._initialized:
            with self.path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp", "event", "price", "direction", "position_size",
                    "mode", "params_version",
                    "bias", "bias_prob",
                    "entry_score", "entry_score_v2", "exit_score_v2",
                    "unrealized_profit", "max_profit", "max_loss", "tick_since_entry"
                ])
            self._initialized = True

    def log(self, event: str, state: Dict[str, Any], price: float, tick: Dict[str, Any]):
        """寫入交易紀錄"""
        if not self._initialized:
            self._init_file()

        row = [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            event,
            price,
            state.get("direction"),
            state.get("current_position_size"),
            state.get("mode", "v3"),
            state.get("params_version", "unversioned"),
            tick.get("bias"),
            tick.get("bias_prob", ""),
            tick.get("entry_score", ""),
            tick.get("entry_score_v2", ""),
            tick.get("exit_score_v2", ""),
            state.get("unrealized_profit", ""),
            state.get("max_profit", ""),
            state.get("max_loss", ""),
            state.get("tick_since_entry", "")
        ]

        with self.path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(row)

        print(f"[LOG] {event} @ {price} | mode={state.get('mode')} | ver={state.get('params_version')}")
