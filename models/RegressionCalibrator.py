# strategy_v4/models/RegressionCalibrator.py

import numpy as np
import pandas as pd
from typing import List, Dict
from sklearn.linear_model import LinearRegression
from pathlib import Path
from strategy_v4.models.ParamsStore import ParamsStore


class RegressionCalibrator:
    """
    回歸校正器：
    - 從 tick 資料計算特徵與目標
    - 使用線性回歸校正權重
    - 更新 ParamsStore
    """

    def __init__(self, params_store: ParamsStore, version_prefix: str = "v4-calib"):
        self.params_store = params_store
        self.version_prefix = version_prefix

    def fit(self, ticks: List[Dict], target_key: str = "future_return") -> Dict[str, float]:
        """
        訓練回歸模型，輸出權重
        :param ticks: tick 資料，每筆包含 features 與 target
        :param target_key: 目標欄位 (例如 future_return)
        :return: 權重 dict
        """
        if not ticks:
            return {}

        # 建立 DataFrame
        df = pd.DataFrame(ticks)

        # 特徵欄位
        feature_cols = [
            "rsi", "macd", "macd_signal", "kd_k", "kd_d",
            "atr", "adx", "vwap", "ema5", "ema20",
            "bband_pos", "bband_width", "volume", "vol_roc",
            "rsi_1m", "ema_1m", "rsi_5m", "ema_5m", "rsi_15m", "ema_15m"
        ]

        # 避免缺失欄位造成 KeyError
        for col in feature_cols:
            if col not in df.columns:
                df[col] = 0.0

        if target_key not in df.columns:
            df[target_key] = 0.0

        features = df[feature_cols].fillna(0.0).values
        target = df[target_key].fillna(0.0).values

        # 線性回歸
        model = LinearRegression()
        model.fit(features, target)

        weights = {col: float(w) for col, w in zip(feature_cols, model.coef_)}
        return weights

    def calibrate(self, ticks: List[Dict], target_key: str = "future_return", version_suffix: str = "") -> Dict[str, float]:
        """
        執行校正並更新 ParamsStore
        """
        weights = self.fit(ticks, target_key)
        version = f"{self.version_prefix}{version_suffix}"
        self.params_store.update(version, weights)
        print(f"[Calibrator] 更新權重版本 {version}")
        return weights
