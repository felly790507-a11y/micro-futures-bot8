# strategy_v4/engines/DecisionEngine_v2.py

from typing import Dict, Tuple

class DecisionEngineV2:
    """
    多因子回歸分數判斷核心 (v4)：
    - detect_market_bias：輸出 bullish / bearish / neutral + 機率
    - score：計算 entry_score_v2 與 exit_score_v2
    - evaluate_tick：整合 bias、prob、score，方便 TickEngine 使用
    """

    def __init__(self, market_bias: str = "neutral",
                 indicators: dict | None = None,
                 weights: Dict[str, float] | None = None,
                 config: dict | None = None):
        self.market_bias = market_bias
        self.indicators = indicators or {}
        self.weights = weights or {}
        self.cfg = config or {}

        # 閾值設定
        self.entry_threshold = self.cfg.get("entry_threshold", 0.0)
        self.exit_threshold = self.cfg.get("exit_threshold", 0.0)
        self.bias_prob_threshold = self.cfg.get("bias_prob_threshold", 0.55)

        # 預設權重（若 ParamsStore 尚未提供）
        self.default_weights = {
            "rsi": 0.15, "macd": 0.20, "macd_signal": -0.10,
            "kd_k": 0.10, "kd_d": -0.05, "atr": -0.05,
            "adx": 0.10, "vwap": 0.10, "ema5": 0.10,
            "ema20": 0.10, "bband_pos": 0.05, "volume": 0.05,
        }

    def _get_weight(self, name: str) -> float:
        return float(self.weights.get(name, self.default_weights.get(name, 0.0)))

    def _linear_score(self, features: Dict[str, float]) -> float:
        score = 0.0
        for k, v in features.items():
            if v is None:
                continue
            score += self._get_weight(k) * float(v)
        return float(score)

    def detect_market_bias(self, tick: dict, features: Dict[str, float]) -> Tuple[str, float]:
        """
        偏向判斷：
        - 用 macd、ema slope、adx + 分數組合估算機率
        - 回傳 (bias_label, bias_prob)
        """
        macd = float(features.get("macd", 0.0))
        macd_signal = float(features.get("macd_signal", 0.0))
        ema5 = float(features.get("ema5", 0.0))
        ema20 = float(features.get("ema20", 0.0))
        adx = float(features.get("adx", 0.0))

        slope = ema5 - ema20
        base = self._linear_score(features)

        raw = 0.4 * base + 0.3 * (macd - macd_signal) + 0.2 * slope + 0.1 * (adx - 20)
        prob = max(0.0, min(1.0, 0.5 + raw / (abs(raw) + 10.0)))

        if prob >= self.bias_prob_threshold and (macd - macd_signal >= 0 or slope >= 0):
            return "bullish", prob
        if prob >= self.bias_prob_threshold and (macd - macd_signal < 0 or slope < 0):
            return "bearish", prob
        return "neutral", prob

    def score(self, tick: dict, features: Dict[str, float]) -> Tuple[float, float]:
        """
        回傳進場與出場分數：
        - entry_score_v2：偏向趨勢延續的分數
        - exit_score_v2：偏向轉弱或風險上升的分數（分數越高越傾向出場）
        """
        entry_score = self._linear_score(features)

        inv_features = {
            "rsi": 100 - float(features.get("rsi", 50.0)),
            "macd": -float(features.get("macd", 0.0)),
            "macd_signal": float(features.get("macd_signal", 0.0)),
            "kd_k": 100 - float(features.get("kd_k", 50.0)),
            "kd_d": float(features.get("kd_d", 50.0)),
            "atr": float(features.get("atr", 0.0)),
            "adx": 40 - float(features.get("adx", 20.0)),
            "vwap": -float(features.get("vwap", 0.0)),
            "ema5": -float(features.get("ema5", 0.0)),
            "ema20": -float(features.get("ema20", 0.0)),
            "bband_pos": 1.0 - float(features.get("bband_pos", 0.5)),
            "volume": -float(features.get("volume", 0.0)),
        }
        exit_score = self._linear_score(inv_features)

        return float(entry_score), float(exit_score)

    def should_enter(self, bias_prob: float, entry_score: float) -> bool:
        """判斷是否進場"""
        return bias_prob >= self.bias_prob_threshold and entry_score >= self.entry_threshold

    def should_exit(self, exit_score: float) -> bool:
        """判斷是否出場"""
        return exit_score >= self.exit_threshold

    def evaluate_tick(self, tick: dict, features: Dict[str, float]) -> Dict[str, float]:
        """
        整合評估：
        - bias, bias_prob
        - entry_score_v2, exit_score_v2
        - 是否進場/出場
        """
        bias, bias_prob = self.detect_market_bias(tick, features)
        entry_score, exit_score = self.score(tick, features)

        return {
            "bias": bias,
            "bias_prob": bias_prob,
            "entry_score_v2": entry_score,
            "exit_score_v2": exit_score,
            "should_enter": self.should_enter(bias_prob, entry_score),
            "should_exit": self.should_exit(exit_score),
        }
