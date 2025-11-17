import pandas as pd

# ====== 讀取 K 線資料 ======
df_1m = pd.read_csv("kbars_6m.csv", parse_dates=["datetime"])
df_5m = pd.read_csv("kbars_5m.csv", parse_dates=["datetime"])

# ====== 讀取事件矩陣 ======
matrix = pd.read_csv("event_flag_matrix.csv", parse_dates=["date"])

# ====== 合併到 1 分 K ======
df_1m["date"] = df_1m["datetime"].dt.normalize()
df_1m = df_1m.merge(matrix, left_on="date", right_on="date", how="left")
df_1m.fillna(0, inplace=True)

# ====== 合併到 5 分 K ======
df_5m["date"] = df_5m["datetime"].dt.normalize()
df_5m = df_5m.merge(matrix, left_on="date", right_on="date", how="left")
df_5m.fillna(0, inplace=True)

# ====== 存檔 ======
df_1m.to_csv("kbars_6m.csv", index=False, encoding="utf-8-sig")
df_5m.to_csv("kbars_5m.csv", index=False, encoding="utf-8-sig")

print(f"✅ 已將 event_flag_matrix 整合進 kbars_6m.csv（{len(df_1m)} 筆）")
print(f"✅ 已將 event_flag_matrix 整合進 kbars_5m.csv（{len(df_5m)} 筆）")
