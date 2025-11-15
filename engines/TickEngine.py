# strategy_v4/engines/TickEngine.py

from datetime import datetime
from strategy_v4.engines.StrategyState import StrategyState
from strategy_v4.engines.DecisionEngine import DecisionEngine          # v3 規則型
from strategy_v4.engines.DecisionEngine_v2 import DecisionEngineV2     # v4 回歸型
from strategy_v4.engines.TickPatternTracker import TickPatternTracker
from strategy_v4.io.TradeLogger import TradeLogger
from strategy_v4.io.TickRecorder import TickRecorder
from strategy_v4.engines.IndicatorEngine import extract_features
from strategy_v4.engines.MultiTimeframeEngine import MultiTimeframeEngine
from strategy_v4.models.ParamsStore import ParamsStore



class TickEngine:
    def __init__(
        self,
        state: StrategyState,
        market_bias: str = "neutral",
        trade_logger: TradeLogger | None = None,
        tick_recorder: TickRecorder | None = None,
        mode: str = "rule_based",  # rule_based | regression_based
        params_store: ParamsStore | None = None,
        config: dict | None = None,
    ):
        self.state = state
        self.market_bias = market_bias
        self.tick_tracker = TickPatternTracker()
        self.logger = trade_logger if trade_logger else TradeLogger()
        self.tick_recorder = tick_recorder
        self.mode = mode
        self.params_store = params_store
        self.config = config or {}

        # v4 權重版本與決策引擎初始化
        self.params_version = "unversioned"
        if self.mode == "regression_based":
            weights = None
            if self.params_store:
                weights = self.params_store.get_weights()
                self.params_version = self.params_store.get_version()
            self.decision_engine = DecisionEngineV2(
                market_bias=self.market_bias,
                weights=weights,
                config=self.config.get("decision", {}),
            )
        else:
            # v3 規則型需傳 indicators/tick_tracker（若無則用空/預設）
            self.decision_engine = DecisionEngine(
                market_bias=self.market_bias,
                indicators=self.config.get("indicators", {}),
                tick_tracker=self.tick_tracker
            )

        # 本地緩存序列（僅供指標計算）
        self.close_prices: list[float] = []
        self.high_prices: list[float] = []
        self.low_prices: list[float] = []
        self.volumes: list[float] = []

        # 多時間框架引擎
        self.multi_tf_engine = MultiTimeframeEngine()

        # 閾值配置（本地快取，用於 v3/v4 進場檢查）
        dcfg = self.config.get("decision", {})
        self.entry_threshold = float(dcfg.get("entry_threshold", 0.0))
        self.exit_threshold = float(dcfg.get("exit_threshold", 0.0))
        self.bias_prob_threshold = float(dcfg.get("bias_prob_threshold", 0.55))

    def _choose_direction_v3(self, tick: dict) -> str:
        dir_score = tick.get("direction_score", 0)
        bias = tick.get("bias", "neutral")
        if dir_score > 0 and bias == "bullish":
            return "long"
        if dir_score < 0 and bias == "bearish":
            return "short"
        return "long" if tick.get("momentum", 0) > 0 else "short"

    def _choose_direction_v4(self, tick: dict) -> str:
        bias = tick.get("bias", "neutral")
        bias_prob = float(tick.get("bias_prob", 0.5))
        entry_score = float(tick.get("entry_score_v2", 0.0))
        if bias == "bullish" and bias_prob >= self.bias_prob_threshold and entry_score >= self.entry_threshold:
            return "long"
        if bias == "bearish" and bias_prob >= self.bias_prob_threshold and entry_score >= self.entry_threshold:
            return "short"
        # 若條件不足，回退 v3 規則方向
        return self._choose_direction_v3(tick)

    def on_tick(self, tick: dict):
        price = float(tick.get("price", 0))
        volume = float(tick.get("volume", 0))
        timestamp = tick.get("timestamp", datetime.now())

        # 更新本地緩存
        self.close_prices.append(price)
        self.high_prices.append(price)
        self.low_prices.append(price)
        self.volumes.append(volume)

        # 更新多時間框架引擎
        self.multi_tf_engine.update(price, volume)

        # 統一特徵輸出 (IndicatorEngine + MultiTimeframeEngine)
        features = extract_features(tick, self.close_prices, self.high_prices, self.low_prices, self.volumes)
        tf_features = self.multi_tf_engine.extract_features()
        features.update(tf_features)

        # 判斷 Bias 與分數
        if self.mode == "regression_based":
            eval_res = self.decision_engine.evaluate_tick(tick, features)
            tick.update({
                "bias": eval_res["bias"],
                "bias_prob": eval_res["bias_prob"],
                "entry_score_v2": eval_res["entry_score_v2"],
                "exit_score_v2": eval_res["exit_score_v2"],
                "params_version": self.params_version,
                "mode": "v4"
            })
            entry_score = float(eval_res["entry_score_v2"])
            exit_score = float(eval_res["exit_score_v2"])
        else:
            # v3 規則型
            bias = self.decision_engine.detect_market_bias(tick)
            entry_score = float(self.decision_engine.score_entry(tick))
            exit_score = float(self.decision_engine.score_exit(tick)) if hasattr(self.decision_engine, "score_exit") else 0.0
            tick.update({
                "bias": bias,
                "entry_score": entry_score,
                "exit_score": exit_score,
                "mode": "v3"
            })

        # 更新狀態（獲利與追蹤器）
        self.tick_tracker.update(price, volume)
        self.state.update_profit_loss(price)

        # 紀錄輸出
        print(
            f"[TICK] {timestamp}｜Price={price:.2f}｜Bias={tick.get('bias')}｜Score={entry_score:.3f}"
            + (f"｜pBias={tick.get('bias_prob', 0.0):.3f}｜ver={tick.get('params_version', 'n/a')}" if self.mode == "regression_based" else "")
        )

        # Tick 記錄
        if self.tick_recorder:
            self.tick_recorder.record_tick(tick)

        # 進場判斷
        if not self.state.in_position:
            if self.mode == "rule_based":
                should_enter = bool(self.decision_engine.should_enter(tick))
            else:
                should_enter = bool(
                    tick.get("entry_score_v2", 0.0) >= self.entry_threshold and
                    tick.get("bias_prob", 0.0) >= self.bias_prob_threshold
                )

            if should_enter:
                direction = self._choose_direction_v4(tick) if self.mode == "regression_based" else self._choose_direction_v3(tick)
                self.state.enter(direction, price)
                self.logger.log("ENTER", self.state.get_status(), price, tick)
                return  # 進場後本 tick 不做出場判斷

        # 出場判斷（依序：停損 → 停利 → exit_score → tick/time → 其他）
        atr_val = float(tick.get("atr", 0))
        if self.state.should_stoploss(price, atr_val):
            self.logger.log("STOPLOSS", self.state.get_status(), price, tick)
            self.state.exit(price, reason="stoploss")
        elif self.state.should_takeprofit(price, atr_val):
            self.logger.log("TAKEPROFIT", self.state.get_status(), price, tick)
            self.state.exit(price, reason="takeprofit")
        elif self.mode == "regression_based" and self.state.should_exit_by_score(float(tick.get("exit_score_v2", 0.0))):
            self.logger.log("EXIT_SCORE", self.state.get_status(), price, tick)
            self.state.exit(price, reason="exit_score")
        elif self.state.should_exit_by_tick() or self.state.should_exit_by_time():
            self.logger.log("TIME_EXIT", self.state.get_status(), price, tick)
            self.state.exit(price, reason="time_or_tick")
        elif not self.state.should_hold():
            self.logger.log("EXIT", self.state.get_status(), price, tick)
            self.state.exit(price, reason="hold_false")
        else:
            # 加碼判斷（可選）
            if self.state.should_add(price, tick):
                self.state.current_position_size += 1
                self.logger.log("ADD", self.state.get_status(), price, tick)
