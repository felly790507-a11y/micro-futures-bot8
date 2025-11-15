# strategy_v4/backtest/BacktestRunner.py

from strategy_v4.engines.TickEngine import TickEngine
from strategy_v4.engines.StrategyState import StrategyState
from strategy_v4.io.TradeLogger import TradeLogger
from strategy_v4.io.TickRecorder import TickRecorder
from strategy_v4.io.TradeAnalyzer import TradeAnalyzer
from strategy_v4.models.ParamsStore import ParamsStore
from strategy_v4.config.ConfigManager import ConfigManager




class BacktestRunner:
    """
    回測執行器：
    - 支援 v3/v4 策略
    - 可指定 params_version
    - 自動紀錄交易與 tick
    - 回測結束後執行分析
    """

    def __init__(
        self,
        mode: str = "regression_based",
        params_path: str = "calibrated_params.json",
        config_path: str = "strategy_config.json"
    ):
        self.mode = mode
        self.params_store = ParamsStore(params_path)
        self.params_store.load()
        self.config = ConfigManager(config_path)
        self.config.load()

        # 初始化模組
        self.state = StrategyState(
            config={
                "risk": self.config.get_risk_params(),
                "decision": self.config.get_decision_params()
            },
            params_version=self.params_store.get_version(),
            mode=mode
        )
        self.logger = TradeLogger("trade_log.csv")
        self.recorder = TickRecorder("tick_data.csv")

        self.engine = TickEngine(
            state=self.state,
            trade_logger=self.logger,
            tick_recorder=self.recorder,
            mode=self.mode,
            params_store=self.params_store,
            config={
                "risk": self.config.get_risk_params(),
                "decision": self.config.get_decision_params()
            }
        )

    def run(self, ticks: list[dict]):
        """
        執行回測
        :param ticks: tick 資料列表，每筆包含 price, volume, timestamp, indicators
        """
        for tick in ticks:
            self.engine.on_tick(tick)

        # 強制 flush tick recorder
        self.recorder.force_flush()

        # 分析結果
        analyzer = TradeAnalyzer("trade_log.csv")
        results = analyzer.analyze()
        return results
