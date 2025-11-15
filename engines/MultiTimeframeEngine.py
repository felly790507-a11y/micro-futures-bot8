# strategy_v4/engines/MultiTimeframeEngine.py

import numpy as np
from typing import Dict, List

# ===== 基本指標計算 =====
def compute_rsi(prices: List[float], period: int = 14) -> float:
    if len(prices) < period + 1:
        return 50.0
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    avg_gain = np.mean(gains[-period:]) if np.any(gains) else 0.0
    avg_loss = np.mean(losses[-period:]) if np.any(losses) else 0.0
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)

def compute_ema(prices: List[float], period: int = 20) -> float:
    if not prices:
        return 0.0
    if len(prices) < period:
        return prices[-1]
    k = 2 / (period + 1)
    ema_val = prices[0]
    for price in prices[1:]:
        ema_val = price * k + ema_val * (1 - k)
    return round(ema_val, 2)

def compute_bbands(prices: List[float], period: int = 20, mult: float = 2.0) -> Dict[str, float]:
    if len(prices) < period:
        return {"bband_pos": 0.5, "bband_width": 0.0}
    arr = np.array(prices[-period:])
    mean = np.mean(arr)
    std = np.std(arr)
    upper = mean + mult * std
    lower = mean - mult * std
    pos = (arr[-1] - lower) / (upper - lower) if upper != lower else 0.5
    width = (upper - lower) / mean if mean != 0 else 0.0
    return {"bband_pos": round(pos, 3), "bband_width": round(width, 3)}

def compute_volume_roc(volumes: List[float], period: int = 10) -> float:
    if len(volumes) < period * 2:
        return 0.0
    prev = np.mean(volumes[-2*period:-period])
    curr = np.mean(volumes[-period:])
    if prev == 0:
        return 0.0
    return round((curr - prev) / prev, 3)

# ===== 多時間框架引擎 =====
class MultiTimeframeEngine:
    def __init__(self):
        self.close_1m: List[float] = []
        self.close_5m: List[float] = []
        self.close_15m: List[float] = []
        self.volumes: List[float] = []
        self.tick_count = 0

    def update(self, price: float, volume: float):
        """更新多時間框架資料"""
        self.tick_count += 1
        self.close_1m.append(price)
        self.volumes.append(volume)

        # 5m close
        if self.tick_count % 5 == 0:
            self.close_5m.append(price)
            if len(self.close_5m) > 500:
                self.close_5m.pop(0)

        # 15m close
        if self.tick_count % 15 == 0:
            self.close_15m.append(price)
            if len(self.close_15m) > 500:
                self.close_15m.pop(0)

    def extract_features(self) -> Dict[str, float]:
        """輸出多時間框架特徵"""
        features = {}

        # 1m RSI/EMA
        features["rsi_1m"] = compute_rsi(self.close_1m)
        features["ema_1m"] = compute_ema(self.close_1m, 20)
        features["is_ready_1m"] = len(self.close_1m) >= 30

        # 5m RSI/EMA
        features["rsi_5m"] = compute_rsi(self.close_5m)
        features["ema_5m"] = compute_ema(self.close_5m, 20)
        features["is_ready_5m"] = len(self.close_5m) >= 20

        # 15m RSI/EMA
        features["rsi_15m"] = compute_rsi(self.close_15m)
        features["ema_15m"] = compute_ema(self.close_15m, 20)
        features["is_ready_15m"] = len(self.close_15m) >= 20

        # 布林帶寬度（用 1m close）
        bb = compute_bbands(self.close_1m)
        features.update(bb)

        # 成交量變化率
        features["vol_roc"] = compute_volume_roc(self.volumes)

        return features
