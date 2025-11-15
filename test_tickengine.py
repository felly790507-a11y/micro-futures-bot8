# test_tickengine.py

import os
from strategy_v4.engines.StrategyState import StrategyState
from strategy_v4.engines.TickEngine import TickEngine
from strategy_v4.io.TradeLogger import TradeLogger
from strategy_v4.io.TickRecorder import TickRecorder

# 取得當前檔案所在目錄，確保 CSV 存在 strategy_v4 資料夾內
base_dir = os.path.dirname(__file__)

# 建立狀態與引擎
state = StrategyState(config={
    "risk": {
        "stoploss_atr_mult": 2.0,
        "takeprofit_atr_mult": 3.0,
        "max_ticks": 10,
        "max_minutes": 5
    },
    "decision": {
        "entry_threshold": 0.5,
        "exit_threshold": 0.5,
        "bias_prob_threshold": 0.55
    }
}, mode="v4")

# 指定 CSV 檔案路徑在 strategy_v4 資料夾
logger = TradeLogger(os.path.join(base_dir, "trade_log.csv"))
recorder = TickRecorder(os.path.join(base_dir, "tick_data.csv"))

# 建立 TickEngine
engine = TickEngine(
    state=state,
    trade_logger=logger,
    tick_recorder=recorder,
    mode="regression_based"
)

# 模擬一段 ticks
ticks = [
    {"price": 100, "volume": 10, "timestamp": "2025-11-15 10:00:00"},
    {"price": 102, "volume": 12, "timestamp": "2025-11-15 10:01:00"},
    {"price": 105, "volume": 15, "timestamp": "2025-11-15 10:02:00"},
    {"price": 103, "volume": 8,  "timestamp": "2025-11-15 10:03:00"},
    {"price": 101, "volume": 9,  "timestamp": "2025-11-15 10:04:00"},
]

# 逐筆送入引擎
for tick in ticks:
    engine.on_tick(tick)

# 強制 flush，確保寫入檔案
recorder.force_flush()

# 查看狀態
print("Final state:", state.get_status())
