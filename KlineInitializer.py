# strategy_v4/io/KlineInitializer.py

import requests
import pandas as pd
from datetime import datetime
from typing import List, Dict

class KlineInitializer:
    """
    K 線初始化器：
    - 從外部網站抓取 K 線資料
    - 支援多來源 (yahoo, twse, fugle)
    - 統一輸出格式
    """

    def __init__(self, source: str = "yahoo", cache: bool = True):
        self.source = source
        self.cache = cache
        self._cache_data: Dict[str, List[dict]] = {}

    def fetch(self, symbol: str, start: str, end: str, interval: str = "1d") -> List[dict]:
        """
        抓取 K 線資料
        :param symbol: 股票/期貨代號
        :param start: 起始日期 (YYYY-MM-DD)
        :param end: 結束日期 (YYYY-MM-DD)
        :param interval: 時間間隔 (1d, 1h, 5m)
        :return: List[dict] 格式的 K 線資料
        """
        cache_key = f"{symbol}_{start}_{end}_{interval}"
        if self.cache and cache_key in self._cache_data:
            return self._cache_data[cache_key]

        if self.source == "yahoo":
            url = f"https://query1.finance.yahoo.com/v7/finance/download/{symbol}?period1={int(datetime.strptime(start,'%Y-%m-%d').timestamp())}&period2={int(datetime.strptime(end,'%Y-%m-%d').timestamp())}&interval={interval}&events=history"
            resp = requests.get(url)
            df = pd.read_csv(pd.compat.StringIO(resp.text))
        elif self.source == "twse":
            # 台灣證交所 API 範例
            url = f"https://www.twse.com.tw/exchangeReport/STOCK_DAY?response=json&date={start.replace('-','')}&stockNo={symbol}"
            resp = requests.get(url).json()
            df = pd.DataFrame(resp.get("data", []))
        else:
            raise ValueError(f"Unsupported source: {self.source}")

        # 統一格式
        kline_data = []
        for _, row in df.iterrows():
            try:
                kline_data.append({
                    "timestamp": pd.to_datetime(row.get("Date") or row.get("date")),
                    "open": float(row.get("Open") or row[1]),
                    "high": float(row.get("High") or row[2]),
                    "low": float(row.get("Low") or row[3]),
                    "close": float(row.get("Close") or row[4]),
                    "volume": float(row.get("Volume") or row[5]),
                })
            except Exception:
                continue

        if self.cache:
            self._cache_data[cache_key] = kline_data

        return kline_data

    def to_dataframe(self, kline_data: List[dict]) -> pd.DataFrame:
        """轉換成 DataFrame"""
        return pd.DataFrame(kline_data)

    def with_indicators(self, kline_data: List[dict]) -> pd.DataFrame:
        """附加 RSI、EMA 等指標"""
        df = self.to_dataframe(kline_data)
        df["rsi"] = self._compute_rsi(df["close"].tolist())
        df["ema20"] = df["close"].ewm(span=20).mean()
        return df

    def _compute_rsi(self, closes: List[float], period: int = 14) -> List[float]:
        if len(closes) < period + 1:
            return [50.0] * len(closes)
        deltas = pd.Series(closes).diff()
        gains = deltas.where(deltas > 0, 0.0)
        losses = -deltas.where(deltas < 0, 0.0)
        avg_gain = gains.rolling(period).mean()
        avg_loss = losses.rolling(period).mean()
        rs = avg_gain / avg_loss.replace(0, 1e-9)
        rsi = 100 - (100 / (1 + rs))
        return rsi.fillna(50.0).tolist()
