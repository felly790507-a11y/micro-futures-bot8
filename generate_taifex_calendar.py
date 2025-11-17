import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime

# ====== 來源網址（TAIFEX 店頭集中結算市場休假日期表） ======
URL = "https://www.taifex.com.tw/cht/5/ccpCalendar"

# ====== 抓取網頁 ======
resp = requests.get(URL)
resp.encoding = "utf-8"
soup = BeautifulSoup(resp.text, "html.parser")

# ====== 找出行事曆表格 ======
table = soup.find("table")
rows = table.find_all("tr")

holidays = []
for row in rows[1:]:  # 跳過表頭
    cols = [col.get_text(strip=True) for col in row.find_all("td")]
    if len(cols) >= 3:
        name, date_str, weekday = cols[0], cols[1], cols[2]

        # 拆解多個日期（如 "2月15日2月16日"）
        parts = date_str.replace("日", "日,").split(",")
        for part in parts:
            part = part.strip()
            if not part:
                continue
            try:
                # 將 "2月15日" → "2-15" → datetime
                date_obj = datetime.strptime(
                    part.replace("月", "-").replace("日", ""), "%m-%d"
                )
                date_obj = date_obj.replace(year=2025)
                holidays.append({
                    "date": date_obj.strftime("%Y-%m-%d"),
                    "is_holiday": 1,
                    "holiday_name": name
                })
            except Exception as e:
                print(f"⚠️ 日期解析失敗：{part} → {e}")

# ====== 存成 CSV ======
df = pd.DataFrame(holidays)
df.to_csv("taifex_calendar.csv", index=False, encoding="utf-8-sig")

print(f"✅ 已生成 taifex_calendar.csv，共 {len(df)} 筆休市日")
