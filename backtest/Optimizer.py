# strategy_v4/backtest/Optimizer.py

from typing import List, Dict, Any
from strategy_v4.backtest.BacktestRunner import BacktestRunner
from strategy_v4.io.TradeAnalyzer import TradeAnalyzer



class Optimizer:
    """
    策略參數最佳化器：
    - 測試多組參數組合
    - 執行回測並比較績效
    - 找出最佳設定
    """

    def __init__(self, ticks: List[Dict]):
        self.ticks = ticks

    def run_combinations(self, param_grid: Dict[str, List[Any]], mode: str = "regression_based") -> List[Dict[str, Any]]:
        """
        執行多組參數組合回測
        :param param_grid: 參數網格，例如 {"entry_threshold":[0.1,0.2], "exit_threshold":[-0.05,-0.1]}
        :param mode: 策略模式 (rule_based / regression_based)
        :return: 每組參數的績效結果
        """
        results = []
        keys = list(param_grid.keys())

        def recurse(idx: int, current: Dict[str, Any]):
            if idx == len(keys):
                # 執行回測
                runner = BacktestRunner(mode=mode)
                # 更新配置
                runner.engine.entry_threshold = current.get("entry_threshold", runner.engine.entry_threshold)
                runner.engine.exit_threshold = current.get("exit_threshold", runner.engine.exit_threshold)
                runner.engine.bias_prob_threshold = current.get("bias_prob_threshold", runner.engine.bias_prob_threshold)

                res = runner.run(self.ticks)
                results.append({"params": current.copy(), "results": res})
                return

            key = keys[idx]
            for val in param_grid[key]:
                current[key] = val
                recurse(idx + 1, current)

        recurse(0, {})
        return results

    def find_best(self, param_grid: Dict[str, List[Any]], mode: str = "regression_based", metric: str = "avg_pnl") -> Dict[str, Any]:
        """
        找出最佳參數組合
        :param param_grid: 參數網格
        :param mode: 策略模式
        :param metric: 評估指標 (avg_pnl / win_rate / max_drawdown)
        :return: 最佳參數與績效
        """
        results = self.run_combinations(param_grid, mode)
        best = None
        best_val = None

        for r in results:
            stats = list(r["results"].values())[0]  # 取第一組分群結果
            val = stats.get(metric, 0)
            if best is None or (metric == "max_drawdown" and val > best_val) or (metric != "max_drawdown" and val > best_val):
                best = r
                best_val = val

        print(f"[Optimizer] Best params={best['params']} | {metric}={best_val}")
        return best
