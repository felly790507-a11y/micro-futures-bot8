# strategy_v4/engines/TickPatternTracker.py

from collections import deque
from typing import Dict, Any

class TickPatternTracker:
    """
    短線型態追蹤器：
    - 追蹤最近 N 筆 tick 的價格變化
    - 計算 momentum、bias_prob 輔助值
    - 提供 exit_score 輔助判斷
    """

    def __init__(self, window: int = 20):
        self.window = window
        self.prices = deque(maxlen=window)
        self.volumes = deque(maxlen=window)

    def update(self, price: float, volume: float = 0.0):
        """更新 tick 資料"""
        self.prices.append(price)
        self.volumes.append(volume)

    def momentum(self) -> float:
        """
        計算相對動能：
        - (最後價 / 第一價 - 1)，代表漲跌幅
        """
        if len(self.prices) < 2 or self.prices[0] == 0:
            return 0.0
        return round((self.prices[-1] / self.prices[0]) - 1.0, 3)

    def bias_prob(self) -> float:
        """
        計算 bias 機率輔助值：
        - 價格上漲比例作為 bullish 機率
        """
        if len(self.prices) < 2:
            return 0.5
        up_moves = sum(1 for i in range(1, len(self.prices)) if self.prices[i] > self.prices[i-1])
        prob = up_moves / (len(self.prices) - 1)
        return round(prob, 3)

    def exit_score(self) -> float:
        """
        計算 exit_score 輔助值：
        - 價格波動越大，exit_score 越高（越傾向出場）
        """
        if len(self.prices) < 2:
            return 0.0
        diffs = [abs(self.prices[i] - self.prices[i-1]) for i in range(1, len(self.prices))]
        avg_volatility = sum(diffs) / len(diffs)
        base_price = self.prices[-1] if self.prices[-1] != 0 else 1.0
        score = avg_volatility / base_price
        return round(score, 3)

    def avg_volume(self) -> float:
        """計算平均成交量"""
        if not self.volumes:
            return 0.0
        return round(sum(self.volumes) / len(self.volumes), 2)

    def get_status(self) -> Dict[str, Any]:
        """輸出追蹤狀態"""
        return {
            "momentum": self.momentum(),
            "bias_prob": self.bias_prob(),
            "exit_score": self.exit_score(),
            "last_price": self.prices[-1] if self.prices else None,
            "count": len(self.prices),
            "avg_volume": self.avg_volume(),
        }
