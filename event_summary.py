import pandas as pd

# ====== 讀取事件表 ======
df = pd.read_csv("events.csv", parse_dates=["date"])

# ====== 統計各類事件出現次數 ======
summary = df["event"].value_counts().reset_index()
summary.columns = ["event_type", "count"]

# ====== 加入日期範圍與首尾日期 ======
summary["start_date"] = df.groupby("event")["date"].min().values
summary["end_date"] = df.groupby("event")["date"].max().values

# ====== 存成 CSV ======
summary.to_csv("event_summary.csv", index=False, encoding="utf-8-sig")
print(f"✅ 已輸出 event_summary.csv｜共 {len(summary)} 類事件")
