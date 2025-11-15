# strategy_v4/engines/IndicatorEngine.py

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
    if len(prices) < period:
        return prices[-1] if prices else 0.0
    k = 2 / (period + 1)
    ema_val = prices[0]
    for price in prices[1:]:
        ema_val = price * k + ema_val * (1 - k)
    return round(ema_val, 2)

def compute_macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, float]:
    if len(prices) < slow + signal:
        return {"macd": 0.0, "macd_signal": 0.0}
    ema_fast = compute_ema(prices, fast)
    ema_slow = compute_ema(prices, slow)
    macd_val = ema_fast - ema_slow
    # signal 線：用 MACD 值序列的 EMA
    macd_series = [compute_ema(prices[i:], fast) - compute_ema(prices[i:], slow) for i in range(len(prices) - slow)]
    macd_signal = compute_ema(macd_series, signal) if macd_series else 0.0
    return {"macd": round(macd_val, 3), "macd_signal": round(macd_signal, 3)}

def compute_atr(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> float:
    if len(closes) < period + 1:
        return 0.0
    trs = []
    for i in range(1, len(closes)):
        tr = max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
        trs.append(tr)
    return round(np.mean(trs[-period:]), 2)

def compute_adx(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> float:
    if len(closes) < period + 1:
        return 20.0
    # 簡化版 ADX：取 TR 平均比例
    trs = [highs[i] - lows[i] for i in range(1, len(closes))]
    avg_tr = np.mean(trs[-period:]) if trs else 0.0
    return round(25.0 + avg_tr * 0.1, 2)

def compute_vwap(prices: List[float], volumes: List[float]) -> float:
    if not prices or not volumes or sum(volumes) == 0:
        return 0.0
    cum_pv = np.cumsum(np.array(prices) * np.array(volumes))
    cum_vol = np.cumsum(volumes)
    return round(cum_pv[-1] / cum_vol[-1], 2)

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

# ===== 統一特徵輸出 =====
def compute_all_indicators(closes: List[float], highs: List[float], lows: List[float], volumes: List[float]) -> Dict[str, float]:
    return {
        "rsi": compute_rsi(closes),
        "ema5": compute_ema(closes, 5),
        "ema20": compute_ema(closes, 20),
        **compute_macd(closes),
        "atr": compute_atr(highs, lows, closes),
        "adx": compute_adx(highs, lows, closes),
        "vwap": compute_vwap(closes, volumes),
        **compute_bbands(closes),
        "vol_roc": compute_volume_roc(volumes),
    }

def extract_features(tick: dict, closes: List[float], highs: List[float], lows: List[float], volumes: List[float]) -> Dict[str, float]:
    """
    統一輸出回歸模型需要的特徵矩陣
    """
    indicators = compute_all_indicators(closes, highs, lows, volumes)
    features = {
        "rsi": indicators.get("rsi", 50.0),
        "macd": indicators.get("macd", 0.0),
        "macd_signal": indicators.get("macd_signal", 0.0),
        "kd_k": tick.get("kd_k", 50.0),
        "kd_d": tick.get("kd_d", 50.0),
        "atr": indicators.get("atr", 0.0),
        "adx": indicators.get("adx", 20.0),
        "vwap": indicators.get("vwap", 0.0),
        "ema5": indicators.get("ema5", 0.0),
        "ema20": indicators.get("ema20", 0.0),
        "bband_pos": indicators.get("bband_pos", 0.5),
        "bband_width": indicators.get("bband_width", 0.0),
        "volume": tick.get("volume", 0.0),
        "vol_roc": indicators.get("vol_roc", 0.0),
    }
    return features
