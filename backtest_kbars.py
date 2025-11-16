import json
import shioaji as sj
import pandas as pd
from datetime import datetime, timedelta
import calendar

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
try:
    kbars = api.kbars(contract=contract, start=start_date, end=end_date)
    df = pd.DataFrame({**kbars})
except Exception as e:
    print("❌ 抓取 K 線失敗:", e)
    df = pd.DataFrame()

# ====== 定義事件計算函式 ======
def get_settlement_days(year):
    days = []
    for month in range(1, 13):
        max_day = calendar.monthrange(year, month)[1]
        wednesdays = [day for day in range(1, max_day+1)
                      if calendar.weekday(year, month, day) == 2]
        if len(wednesdays) >= 3:
            days.append(datetime(year, month, wednesdays[2]).date())
    return days

def get_central_bank_meetings(year):
    meetings = []
    for month in [3, 6, 9, 12]:
        max_day = calendar.monthrange(year, month)[1]
        thursdays = [day for day in range(1, max_day+1)
                     if calendar.weekday(year, month, day) == 3]
        if len(thursdays) >= 3:
            meetings.append(datetime(year, month, thursdays[2]).date())
    return meetings

# ====== 資料整理與存檔 ======
if df.empty:
    print("⚠️ 沒有抓到 K 線資料，請確認日期區間或合約是否正確")
else:
    # 欄位改名
    df.rename(columns={
        "ts": "datetime",
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Volume": "volume",
        "Amount": "amount"
    }, inplace=True)

    # 時間轉換與索引
    df["datetime"] = pd.to_datetime(df["datetime"])
    df.set_index("datetime", inplace=True)

    # ====== 自動產生事件表 ======
    settlement_days = get_settlement_days(today.year)
    cb_meetings = get_central_bank_meetings(today.year)

    df_events = pd.DataFrame(
        {"date": settlement_days + cb_meetings,
         "event": ["台指期貨結算日"] * len(settlement_days) + ["央行利率會議"] * len(cb_meetings)}
    )
    df_events["date"] = pd.to_datetime(df_events["date"])  # 確保型別一致
    df_events.to_csv("events.csv", index=False)

    # ====== 事件標記 ======
    df["event_flag"] = df.index.normalize().isin(df_events["date"])
    df = df.merge(df_events, left_on=df.index.normalize(), right_on="date", how="left")

    # 修正索引：重新設回 DatetimeIndex
    df["datetime"] = pd.to_datetime(df["datetime"])
    df.set_index("datetime", inplace=True)

    print("✅ 已標記事件日")

    # 存檔：1 分 K
    df.to_csv("kbars_6m.csv", mode="w")
    print(f"✅ 已存成 kbars_6m.csv｜筆數：{len(df)}")

    # ====== 週期轉換：5 分 K ======
    df_5m = df.resample("5min").agg({
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "volume": "sum",
        "amount": "sum"
    }).dropna()

    df_5m.to_csv("kbars_5m.csv", mode="w")
    print(f"✅ 已存成 kbars_5m.csv｜筆數：{len(df_5m)}")
