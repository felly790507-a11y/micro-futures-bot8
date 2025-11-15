# strategy_v4/engines/DecisionEngine.py

from typing import Optional

class DecisionEngine:
    def __init__(self, market_bias: str = "neutral", indicators: dict | None = None, tick_tracker: Optional[object] = None):
        """
        規則型決策引擎 (v3)：
        - 與 TickEngine 對齊：提供 detect_market_bias, score_entry, score_exit, should_enter
        - 相容 v4 的 TickPatternTracker（若沒有特殊方法則退化為 momentum/方向分數）
        """
        self.market_bias = market_bias
        self.indicators = indicators or {}
        self.tick_tracker = tick_tracker

        # 進場門檻配置
        self.cfg = {
            "adx_consolidation": 20,
            "momentum_abs_min": 3,
            "bull_score_min": 3,
            "bear_score_max": -2,
            "neutral_score_abs": 3,
            "rsi_overbought": 70,
            "rsi_bullish_min": 55,
            "rsi_bearish_max": 45,
            "atr_high": 20,   # ATR 高波動門檻
            "atr_low": 5      # ATR 低波動門檻
        }

    # ===== 偏向判斷 =====
    def detect_market_bias(self, tick: dict) -> str:
        adx = float(tick.get("adx", 0) or 0)
        if adx < self.cfg["adx_consolidation"]:
            return "neutral"

        ema5 = float(tick.get("ema5", 0) or 0)
        ema20 = float(tick.get("ema20", 0) or 0)
        macd = float(tick.get("macd", 0) or 0)
        signal = float(tick.get("macd_signal", 0) or 0)
        hist = float(tick.get("macd_hist", 0) or (macd - signal))
        rsi = float(tick.get("rsi", 50) or 50)

        score = 0
        score += 1 if ema5 > ema20 else -1
        score += 1 if macd > signal else -1
        score += 1 if hist > 0.3 else (-1 if hist < -0.3 else 0)
        score += 1 if rsi > 65 else (-1 if rsi < 35 else 0)

        if score > 0:
            return "bullish"
        if score < 0:
            return "bearish"
        return "neutral"

    # ===== 輔助：從 TickPatternTracker 取 momentum/方向分數 =====
    def _extract_tracker_signals(self, tick: dict) -> tuple[float, int]:
        """
        回傳 (momentum, direction_score)
        - 若 tracker 提供 get_status()：用 status["momentum"]
        - 若有 is_three_up/is_sharp_drop_rebound：加分（相容舊版本）
        - 若都沒有：從 tick["momentum"] 推估，並用 momentum 正負當方向分數
        """
        momentum = 0.0
        dir_score = 0

        # v4 TickPatternTracker: get_status()
        if self.tick_tracker and hasattr(self.tick_tracker, "get_status"):
            try:
                st = self.tick_tracker.get_status()
                momentum = float(st.get("momentum", 0.0))
                # 方向分數：基於 momentum 正負與幅度
                if momentum > 0:
                    dir_score += 1
                elif momentum < 0:
                    dir_score -= 1
                # 若有偏向機率也可輔助
                bias_prob = st.get("bias_prob", None)
                if isinstance(bias_prob, (int, float)):
                    if bias_prob >= 0.65:
                        dir_score += 1
                    elif bias_prob <= 0.35:
                        dir_score -= 1
            except Exception:
                pass

        # 舊版 TickPatternTracker: is_three_up / is_sharp_drop_rebound / get_momentum / get_direction_score
        if self.tick_tracker:
            if hasattr(self.tick_tracker, "is_three_up"):
                try:
                    if self.tick_tracker.is_three_up():
                        dir_score += 1
                except Exception:
                    pass
            if hasattr(self.tick_tracker, "is_sharp_drop_rebound"):
                try:
                    if self.tick_tracker.is_sharp_drop_rebound():
                        dir_score += 1
                except Exception:
                    pass
            if hasattr(self.tick_tracker, "get_momentum"):
                try:
                    momentum = float(self.tick_tracker.get_momentum())
                except Exception:
                    pass
            if hasattr(self.tick_tracker, "get_direction_score"):
                try:
                    dir_score += int(self.tick_tracker.get_direction_score())
                except Exception:
                    pass

        # 退化為 tick 欄位
        if momentum == 0.0:
            try:
                momentum = float(tick.get("momentum", 0.0))
            except Exception:
                momentum = 0.0

        if dir_score == 0:
            # 用 momentum 推估方向分數
            if abs(momentum) >= self.cfg["momentum_abs_min"]:
                dir_score = 1 if momentum > 0 else -1
            else:
                dir_score = 0

        # 回寫到 tick（讓 TickEngine 可用）
        tick["momentum"] = momentum
        tick["direction_score"] = dir_score

        return momentum, dir_score

    # ===== 進場強度分數 =====
    def entry_strength_score(self, tick: dict) -> int:
        score = 0
        macd = float(tick.get("macd", 0) or 0)
        signal = float(tick.get("macd_signal", 0) or 0)
        hist = float(tick.get("macd_hist", macd - signal) or (macd - signal))
        rsi = float(tick.get("rsi", 50) or 50)
        ema5 = float(tick.get("ema5", 0) or 0)
        ema20 = float(tick.get("ema20", 0) or 0)
        vwap = float(tick.get("vwap", 0) or 0)
        close = float(tick.get("close", tick.get("price", 0)) or tick.get("price", 0))
        adx = float(tick.get("adx", 0) or 0)
        atr = float(tick.get("atr", 0) or 0)
        volume = float(tick.get("volume", 0) or 0)

        # 盤整過濾
        if adx < self.cfg["adx_consolidation"] and abs(macd - signal) < 0.3:
            return -99

        # 趨勢加分
        if macd > signal and hist > 0.8:
            score += 1
        if close > vwap and ema5 > ema20 and rsi > self.cfg["rsi_bullish_min"]:
            score += 1

        # 多週期確認
        if tick.get("is_ready_5m") and tick.get("is_ready_15m"):
            if float(tick.get("rsi_5m", 50) or 50) > 55 and float(tick.get("ema_15m", 0) or 0) > float(tick.get("ema_5m", 0) or 0):
                score += 1

        # VWAP + 成交量
        if close > vwap and volume >= 5:
            score += 1

        # ATR + ADX 結合
        if adx > 20 and atr >= self.cfg["atr_high"]:
            score += 1
        elif atr <= self.cfg["atr_low"]:
            score -= 1

        # TickPatternTracker 形態/動能
        momentum, direction_score = self._extract_tracker_signals(tick)
        if abs(momentum) >= self.cfg["momentum_abs_min"]:
            score += 1
        score += direction_score

        return int(score)

    def score_entry(self, tick: dict) -> int:
        return int(self.entry_strength_score(tick))

    # ===== 出場分數（分數越高越傾向出場） =====
    def score_exit(self, tick: dict) -> float:
        """
        v3 規則型的出場分數：
        - 高波動、趨勢轉弱、RSI 過熱、逆向 MACD 交叉、VWAP 下穿、動能反轉 → 加分（更傾向出場）
        - 分數越高越傾向出場，與 StrategyState.exit_threshold 一致
        """
        score = 0.0
        macd = float(tick.get("macd", 0) or 0)
        signal = float(tick.get("macd_signal", 0) or 0)
        hist = float(tick.get("macd_hist", macd - signal) or (macd - signal))
        rsi = float(tick.get("rsi", 50) or 50)
        ema5 = float(tick.get("ema5", 0) or 0)
        ema20 = float(tick.get("ema20", 0) or 0)
        vwap = float(tick.get("vwap", 0) or 0)
        price = float(tick.get("price", tick.get("close", 0)) or tick.get("close", 0))
        adx = float(tick.get("adx", 0) or 0)
        atr = float(tick.get("atr", 0) or 0)

        # 動能與方向
        momentum, direction_score = self._extract_tracker_signals(tick)

        # 高波動（ATR 高）
        if atr >= self.cfg["atr_high"]:
            score += 1.0

        # ADX 走弱（小於門檻）
        if adx < self.cfg["adx_consolidation"]:
            score += 0.5

        # 趨勢轉弱：ema5 < ema20
        if ema5 < ema20:
            score += 1.0

        # RSI 過熱或過冷（根據方向分數）
        if rsi >= self.cfg["rsi_overbought"]:
            score += 1.0
        if rsi <= self.cfg["rsi_bearish_max"]:
            score += 0.5

        # MACD 逆向交叉或柱體轉負
        if macd < signal or hist < 0:
            score += 1.0

        # VWAP 下穿（價格 < VWAP）
        if price < vwap:
            score += 0.5

        # 動能反轉或疲弱
        if abs(momentum) < self.cfg["momentum_abs_min"]:
            score += 0.5
        if direction_score < 0:
            score += 0.5

        return float(score)

    # ===== 進場判斷 =====
    def should_enter(self, tick: dict) -> bool:
        score = self.entry_strength_score(tick)
        if score == -99:
            return False

        bias = self.market_bias if self.market_bias != "auto" else self.detect_market_bias(tick)
        tick["bias"] = bias

        # 構面檢查
        if abs(tick.get("momentum", 0)) < self.cfg["momentum_abs_min"]:
            return False
        if tick.get("direction_score", 0) == 0:
            return False
        if not tick.get("is_ready", False):
            return False

        if bias == "bullish":
            return (
                score >= self.cfg["bull_score_min"] and
                float(tick.get("close", tick.get("price", 0)) or 0) > float(tick.get("vwap", 0) or 0) and
                float(tick.get("ema5", 0) or 0) > float(tick.get("ema20", 0) or 0) and
                float(tick.get("rsi", 50) or 50) < self.cfg["rsi_overbought"]
            )
        elif bias == "bearish":
            return (
                score <= self.cfg["bear_score_max"] and
                float(tick.get("ema5", 0) or 0) < float(tick.get("ema20", 0) or 0)
            )
        else:
            return abs(score) >= self.cfg["neutral_score_abs"]
