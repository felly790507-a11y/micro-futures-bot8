import json
import shioaji as sj
import pandas as pd
from datetime import datetime, timedelta

# ====== 讀取設定與登入 ======
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

simulation_mode = config.get("simulation", False)
api_key = config["api_key"]
secret_key = config["secret_key"]

api = sj.Shioaji(simulation=simulation_mode)
api.login(api_key=api_key, secret_key=secret_key, contracts_timeout=10000)
print(f"✅ 登入成功｜模式：{'模擬' if simulation_mode else '真實'}")

# ====== 確保商品檔完整載入 ======
api.fetch_contracts(contract_download=True)

# ====== 使用近月連續合約 R1（微型台指期貨） ======
contract = api.Contracts.Futures.TMF.TMFR1

# ====== 設定過去六個月的日期範圍 ======
today = datetime.today()
six_months_ago = today - timedelta(days=31 * 6)

start_date = six_months_ago.strftime("%Y-%m-%d")
end_date = today.strftime("%Y-%m-%d")

print(f"🔎 抓取 {contract.code}｜期間：{start_date} ~ {end_date}")

# ====== 抓取 K 線 ======
kbars = api.kbars(
    contract=contract,
    start=start_date,
    end=end_date
)

df = pd.DataFrame({**kbars})
if df.empty:
    print("⚠️ 沒有抓到 K 線資料，請確認日期區間或合約是否正確")
else:
    df["ts"] = pd.to_datetime(df["ts"])
    df.to_csv("kbars_6m.csv", index=False)
    print(f"✅ 已存成 kbars_6m.csv｜筆數：{len(df)}")
