import pandas as pd

print("🚀 event_flag_matrix.py 開始執行")

# ====== 讀取事件表 ======
df = pd.read_csv("events.csv", parse_dates=["date"])
print("📂 讀到事件筆數：", len(df))

# ====== 建立事件矩陣（pivot 格式） ======
df["flag"] = 1
matrix = df.pivot_table(
    index="date",
    columns="event",
    values="flag",
    aggfunc="max",   # 同一天多事件 → 保留 1
    fill_value=0
)

# ====== 依日期排序 ======
matrix.sort_index(inplace=True)

# ====== 存成 CSV ======
matrix.to_csv("event_flag_matrix.csv", encoding="utf-8-sig")

print(f"✅ 已生成 event_flag_matrix.csv｜共 {len(matrix)} 天，{len(matrix.columns)} 類事件")
print("📌 事件欄位：", list(matrix.columns))
print(matrix.head())
