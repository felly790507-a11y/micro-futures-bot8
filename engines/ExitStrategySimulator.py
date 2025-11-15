# strategy_v4/engines/ExitStrategySimulator.py

from typing import Dict, List
from strategy_v4.engines.StrategyState import StrategyState

class ExitStrategySimulator:
    """
    出場策略模擬器：
    - 模擬不同出場條件 (停損、停利、exit_score、時間退出)
    - 支援 v3/v4 模式比較
    """

    def __init__(self, config: dict | None = None):
        cfg = config or {}
        risk_cfg = cfg.get("risk", {})
        self.k_sl = risk_cfg.get("stoploss_atr_mult", 2.0)
        self.k_tp = risk_cfg.get("takeprofit_atr_mult", 3.0)
        self.max_ticks = risk_cfg.get("max_ticks", 50)
        self.exit_threshold = cfg.get("decision", {}).get("exit_threshold", 0.0)

    def simulate_exit(self, state: StrategyState, tick: dict) -> Dict[str, bool]:
        """
        模擬各種出場條件，回傳 dict 標記哪些條件觸發
        """
        price = float(tick.get("price", 0))
        atr_val = tick.get("atr", 0.0)
        exit_score = tick.get("exit_score_v2", None)

        results = {
            "stoploss": False,
            "takeprofit": False,
            "exit_score": False,
            "time_exit": False,
            "tick_exit": False,
        }

        # 停損
        if state.should_stoploss(price, atr_val):
            results["stoploss"] = True

        # 停利
        if state.should_takeprofit(price, atr_val):
            results["takeprofit"] = True

        # exit_score (v4)
        if exit_score is not None and state.should_exit_by_score(exit_score, self.exit_threshold):
            results["exit_score"] = True

        # tick-based exit
        if state.should_exit_by_tick():
            results["tick_exit"] = True

        # time-based exit
        if state.should_exit_by_time():
            results["time_exit"] = True

        return results

    def run_simulation(self, state: StrategyState, ticks: List[dict]) -> List[Dict[str, bool]]:
        """
        對一系列 ticks 進行出場模擬
        """
        results = []
        for tick in ticks:
            res = self.simulate_exit(state, tick)
            results.append(res)
        return results
