Micro Futures Bot v7
本專案是一套 微型台指期貨自動化回測與交易系統，同時支援：

v3 規則型引擎：基於邏輯規則的進出場判斷

v4 回歸型引擎：基於回歸模型的分數計算

事件整合模組：自動標記結算日、央行會議、交割日與休市日，並輸出事件矩陣

系統提供完整的 回測、視覺化、最佳化、走勢分段校正 工具鏈，並能將事件標記整合到 K 線資料，方便策略分析與回測。

📂 目錄結構
engines/
DecisionEngine.py → v3 規則型：bias、score_entry、score_exit、should_enter

DecisionEngine_v2.py → v4 回歸型：evaluate_tick → bias、bias_prob、entry_score_v2、exit_score_v2

StrategyState.py → 持倉管理與風控：stoploss/takeprofit/exit_score/tick/time

TickEngine.py → 主循環：整合 v3/v4 引擎、指標、記錄

io/
TradeLogger.py → 交易事件記錄

TickRecorder.py → tick 記錄

TradeAnalyzer.py → 回測分析彙總

models/
ParamsStore.py → 權重版本管理 JSON

RegressionCalibrator.py → 分段權重校正，寫入 ParamsStore

backtest/
BacktestDataLoader.py → K 線轉 tick

BacktestRunner.py → 回測執行

ResultVisualizer.py → 盈虧曲線、勝率分布、版本比較

PerformanceReporter.py → Sharpe、最大回撤、平均持倉時間

WalkforwardTester.py → 分段校正 + 回測

Optimizer.py → 多參數最佳化

ReportExporter.py → CSV/Markdown 匯出

config/
strategy_config.json → risk/decision 參數集合

ConfigManager.py → 載入配置

pipeline/
polars_indicator_utils.py → 以 Polars 產生指標

root
KlineInitializer.py → 資料準備

StrategyLoop.py → 線上策略迴圈；可參考 TickEngine 結構

main.py → 入口

📊 模組引用關係
TickEngine
inputs: tick dict（含 price、volume、timestamp 和指標）

uses: DecisionEngine_v2（v4）或 DecisionEngine（v3）、StrategyState、IndicatorEngine.extract_features、MultiTimeframeEngine、TradeLogger、TickRecorder、ParamsStore

outputs: 交易事件、tick 記錄、狀態更新

BacktestRunner
inputs: ticks（list[dict]）

orchestrates: TickEngine → TradeAnalyzer

outputs: 分析結果（dict）、trade_log.csv、tick_data.csv

WalkforwardTester
流程: split → calibrate → run → analyze → version manage

Optimizer
流程: param_grid → run combinations → find best metric

⚙️ Config 設定範例
json
{
  "risk": {
    "stoploss_atr_mult": 2.0,
    "takeprofit_atr_mult": 3.0,
    "max_ticks": 50,
    "max_minutes": 30
  },
  "decision": {
    "entry_threshold": 0.55,
    "exit_threshold": 0.45,
    "bias_prob_threshold": 0.6
  }
}
🚀 Quick Start
準備資料
使用 KlineInitializer.py 或 BacktestDataLoader.py 將 K 線轉成 ticks。

跑回測
python
BacktestRunner(mode="regression_based").run(ticks)
視覺化與報告
python
ResultVisualizer("trade_log.csv").plot_pnl_curve()
PerformanceReporter("trade_log.csv").report()
ReportExporter().export_csv([...])
走勢分段校正
python
WalkforwardTester(params_path, config_path).run_walkforward(ticks, segment_size=500)
參數最佳化
python
Optimizer(ticks).find_best(param_grid, mode="regression_based", metric="avg_pnl")
🛠 Roadmap
回歸權重校正（RegressionCalibrator）與版本化（ParamsStore.update）對齊

擴充 TradeAnalyzer 輸出指標，與 PerformanceReporter 接軌

加入單元測試（pytest），覆蓋 TickEngine 進出場、StrategyState 風控、DecisionEngine_v2 分數一致性

整合 VS Code tasks.json 一鍵回測與一鍵報告

📌 事件整合與回測流程
執行 generate_taifex_calendar.py

自動抓取 TAIFEX 官網休市日

生成 taifex_calendar.csv

執行 backtest_kbars.py

抓取近月微型台指期貨 K 線

自動計算結算日、央行利率會議日、合約交割日

整合休市日 → 生成 events.csv

輸出 kbars_6m.csv、kbars_5m.csv

執行 event_flag_matrix.py

生成 event_flag_matrix.csv

每天一列，事件類型一欄，方便統計分析

執行 merge_event_matrix.py

將事件矩陣合併到 K 線資料

讓每一根 K 線都帶有完整事件標記

📂 輸出檔案說明
events.csv：完整事件表（結算日、央行會議、交割日、休市日）

kbars_6m.csv：六個月 1 分 K，含事件標記

kbars_5m.csv：六個月 5 分 K，含事件標記

event_flag_matrix.csv：事件矩陣（pivot 格式）

🚦 快速導航流程
讀 read → 快速解析 README，定位專案架構與進度

事件 → 檢查事件模組（backtest_kbars.py、generate_taifex_calendar.py、event_flag_matrix.py、merge_event_matrix.py、event_summary.py）

回測 → 跑 BacktestRunner.py、TradeAnalyzer.py、ResultVisualizer.py

引擎 → 檢查 DecisionEngine.py、DecisionEngine_v2.py、StrategyState.py、TickEngine.py

最佳化 → 跑 Optimizer.py、RegressionCalibrator.py、WalkforwardTester.py

文件 → 補充 README 範例、API 使用說明

🔧 Git 快速操作
全部更新
bash
git add .
git commit -m "🔧 更新全部檔案"
git push origin main
文件更新
bash
git add README.md
git commit -m "📝 更新 README.md 文件"
git push origin main
程式更新
bash
git add backtest_kbars.py event_flag_matrix.py merge_event_matrix.py
git commit -m "✨ 更新回測程式與事件整合模組"
git push origin main
新增檔案
bash
git add event_summary.py
git commit -m "➕ 新增事件統計模組"
git push origin main
刪除檔案
bash
git rm README_architecture.md
git commit -m "🗑 移除舊版架構文件"
git push origin main

🎨 Git Commit Emoji 規範表
Emoji	類型	說明	範例
✨	新功能	新增功能或模組	git commit -m "✨ 新增事件矩陣模組"
🐛	修 bug	修正程式錯誤	git commit -m "🐛 修正回測日期範圍錯誤"
🔧	調整/重構	程式結構優化、重構	git commit -m "🔧 重構 TickEngine 邏輯"
📝	文件	更新 README 或文件	git commit -m "📝 更新 README.md，補充快速導航"
🎨	格式	程式碼排版、格式調整	git commit -m "🎨 統一程式縮排與命名"
➕	新增檔案	新增新模組或檔案	git commit -m "➕ 新增 event_summary.py"
🗑	刪除檔案	移除不需要的檔案	git commit -m "🗑 移除舊版 README_architecture.md"
🔒	安全	增加安全性或權限設定	git commit -m "🔒 加入 API key 加密處理"
🚀	部署/啟動	部署或啟動流程	git commit -m "🚀 初始版本上線"