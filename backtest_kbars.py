import json
import shioaji as sj
from shioaji.constant import QuoteType, QuoteVersion
import pandas as pd

from strategy_v4.engines.StrategyState import StrategyState
from strategy_v4.engines.TickEngine import TickEngine
from strategy_v4.io.TradeLogger import TradeLogger
from strategy_v4.io.TickRecorder import TickRecorder

# ====== 讀取設定與登入 ======
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

simulation_mode = config.get("simulation", True)
api_key = config["api_key"]
secret_key = config["secret_key"]

api = sj.Shioaji(simulation=simulation_mode)
api.login(api_key=api_key, secret_key=secret_key)
print(f"✅ 登入成功｜模式：{'模擬' if simulation_mode else '真實'}")

# ====== 合約選擇（取最早交割月） ======
contracts = [c for c in api.Contracts.Futures.TMF if c.code[-2:] not in ["R1", "R2"]]
contract = min(contracts, key=lambda c: c.delivery_date)
print(f"✅ 使用合約：{contract.code}")

# ====== 抓取歷史 K 線 ======
kbars = api.kbars(
    contract=contract,
    start=config["start"],   # 例如 "2025-10-01 09:00:00"
    end=config["end"],       # 例如 "2025-10-01 13:30:00"
    quote_type=QuoteType.Futures,
    quote_version=QuoteVersion.v1
)

df = pd.DataFrame({**kbars})
df["ts"] = pd.to_datetime(df["ts"])
df.to_csv("kbars.csv", index=False)
print("✅ K 線資料已存成 kbars.csv")

# ====== 初始化策略模組 ======
state = StrategyState()
tick_recorder = TickRecorder(filename="tick_record.csv")
trade_logger = TradeLogger(tick_recorder=tick_recorder)
tick_engine = TickEngine(state, bias="auto", indicators={}, trade_logger=trade_logger, tick_recorder=tick_recorder)

# ====== 用 K 線資料跑回測 ======
for _, row in df.iterrows():
    tick_dict = {
        "price": row["Close"],
        "volume": row["Volume"],
        "timestamp": row["ts"],
    }
    tick_engine.on_tick(tick_dict)

# ====== 強制 flush，確保紀錄寫入 ======
tick_recorder.force_flush()
print("✅ 回測完成，交易紀錄已輸出 trade_log.csv")
print("Final state:", state.get_status())
