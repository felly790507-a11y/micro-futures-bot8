# strategy_v4/backtest/WalkforwardTester.py

from typing import List, Dict
from strategy_v4.backtest.BacktestRunner import BacktestRunner
from strategy_v4.models.RegressionCalibrator import RegressionCalibrator
from strategy_v4.models.ParamsStore import ParamsStore
from strategy_v4.io.TradeAnalyzer import TradeAnalyzer


class WalkforwardTester:
    """
    分段回測器 (Walkforward Testing)：
    - 將資料分成多個區段
    - 每段先校正回歸權重，再進行回測
    - 自動更新 ParamsStore
    """

    def __init__(self, params_path: str = "calibrated_params.json", config_path: str = "strategy_config.json"):
        self.params_store = ParamsStore(params_path)
        self.params_store.load()
        self.config_path = config_path

    def split_data(self, ticks: List[Dict], segment_size: int) -> List[List[Dict]]:
        """將 tick 資料分段"""
        return [ticks[i:i+segment_size] for i in range(0, len(ticks), segment_size)]

    def run_segment(self, ticks: List[Dict], segment_id: int):
        """執行單一分段：校正 + 回測"""
        print(f"[Walkforward] Segment {segment_id} | ticks={len(ticks)}")

        # Step 1: 校正權重
        calibrator = RegressionCalibrator(self.params_store, version_prefix=f"v4-seg{segment_id}")
        new_weights = calibrator.calibrate(ticks, target_key="future_return", version_suffix="")

        # Step 2: 回測
        runner = BacktestRunner(
            mode="regression_based",
            params_path=self.params_store.path,
            config_path=self.config_path
        )
        results = runner.run(ticks)

        # Step 3: 分析
        analyzer = TradeAnalyzer("trade_log.csv")
        analyzer.analyze()

        return {"segment": segment_id, "weights": new_weights, "results": results}

    def run_walkforward(self, ticks: List[Dict], segment_size: int = 500):
        """執行完整 walkforward 測試"""
        segments = self.split_data(ticks, segment_size)
        all_results = []
        for i, seg in enumerate(segments, start=1):
            res = self.run_segment(seg, i)
            all_results.append(res)
        return all_results
