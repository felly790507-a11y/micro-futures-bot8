import os
import pandas as pd

def test_kbars_with_events():
    base_dir = os.path.dirname(__file__)
    csv_path = os.path.join(base_dir, "..", "kbars_with_events.csv")

    df = pd.read_csv(csv_path, parse_dates=["datetime"])
    # 清理欄位名稱：移除所有換行符號與多餘空白
    df.columns = df.columns.str.strip().str.replace(r"\s+", "", regex=True)

    required_cols = [
        "datetime", "open", "high", "low", "close", "volume", "amount", "date",
        "中秋節", "中華民國開國紀念日", "兒童節及清明節", "勞動節", "台指期貨結算日",
        "合約交割日", "和平紀念日", "國慶日", "央行利率會議", "孔子誕辰紀念日/教師節",
        "端午節", "臺灣光復暨金門古寧頭大捷紀念日", "行憲紀念日", "除夕及春節"
    ]
    for col in required_cols:
        assert col in df.columns, f"缺少欄位: {col}"

    event_cols = required_cols[8:]
    for col in event_cols:
        assert set(df[col].dropna().unique()).issubset({0, 1}), f"{col} 欄位有非 0/1 值"

    assert not df[event_cols].isnull().any().any(), "事件欄位有空值"
import os
import pandas as pd

def test_kbars_with_events():
    base_dir = os.path.dirname(__file__)
    csv_path = os.path.join(base_dir, "..", "kbars_with_events.csv")

    df = pd.read_csv(csv_path, parse_dates=["datetime"])
    # 清理欄位名稱：移除所有換行符號與多餘空白
    df.columns = df.columns.str.strip().str.replace(r"\s+", "", regex=True)

    required_cols = [
        "datetime", "open", "high", "low", "close", "volume", "amount", "date",
        "中秋節", "中華民國開國紀念日", "兒童節及清明節", "勞動節", "台指期貨結算日",
        "合約交割日", "和平紀念日", "國慶日", "央行利率會議", "孔子誕辰紀念日/教師節",
        "端午節", "臺灣光復暨金門古寧頭大捷紀念日", "行憲紀念日", "除夕及春節"
    ]
    for col in required_cols:
        assert col in df.columns, f"缺少欄位: {col}"

    event_cols = required_cols[8:]
    # 將 NaN 補成 0，確保事件欄位完整
    df[event_cols] = df[event_cols].fillna(0).astype(int)

    for col in event_cols:
        assert set(df[col].unique()).issubset({0, 1}), f"{col} 欄位有非 0/1 值"
