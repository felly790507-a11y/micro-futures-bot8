# strategy_v4/engines/StrategyState.py

from datetime import datetime, timedelta

class StrategyState:
    """
    管理持倉狀態與風控判斷：
    - 外部化風控參數 (ATR 倍數、最大 tick/minute)
    - 支援 exit_score 出場判斷
    - 紀錄 mode 與 params_version，方便分析
    """

    def __init__(self, config: dict | None = None, params_version: str = "unversioned", mode: str = "v3"):
        self.in_position = False
        self.direction = None
        self.entry_price = None
        self.entry_time = None
        self.current_position_size = 0
        self.max_profit = 0.0
        self.max_loss = 0.0
        self.tick_since_entry = 0
        self.last_rsi = 50
        self.last_macd = 0
        self.last_kd_k = 50
        self.last_kd_d = 50
        self.mode = mode
        self.params_version = params_version

        # 外部化風控參數
        cfg = config or {}
        risk_cfg = cfg.get("risk", {})
        self.k_sl = risk_cfg.get("stoploss_atr_mult", 2.0)   # 停損 ATR 倍數
        self.k_tp = risk_cfg.get("takeprofit_atr_mult", 3.0) # 停利 ATR 倍數
        self.max_ticks = risk_cfg.get("max_ticks", 50)       # 最大持倉 tick
        self.max_minutes = risk_cfg.get("max_minutes", 30)   # 最大持倉分鐘
        self.exit_threshold = cfg.get("decision", {}).get("exit_threshold", 0.0) # exit_score 閾值

    # ===== 狀態操作 =====
    def enter(self, direction: str, price: float):
        self.in_position = True
        self.direction = direction
        self.entry_price = price
        self.entry_time = datetime.now()
        self.current_position_size = 1
        self.max_profit = 0.0
        self.max_loss = 0.0
        self.tick_since_entry = 0
        print(f"[State] 進場 | direction={direction} | price={price}")

    def exit(self, price: float, reason: str = "manual"):
        if not self.in_position:
            return
        pnl = (price - self.entry_price) if self.direction == "long" else (self.entry_price - price)
        print(f"[State] 出場 | direction={self.direction} | price={price} | pnl={pnl:.2f} | reason={reason}")
        self.in_position = False
        self.direction = None
        self.entry_price = None
        self.entry_time = None
        self.current_position_size = 0
        self.tick_since_entry = 0

    def update_profit_loss(self, price: float):
        if not self.in_position:
            return
        pnl = (price - self.entry_price) if self.direction == "long" else (self.entry_price - price)
        self.max_profit = max(self.max_profit, pnl)
        self.max_loss = min(self.max_loss, pnl)
        self.tick_since_entry += 1

    def get_unrealized_profit(self, price: float) -> float:
        if not self.in_position:
            return 0.0
        return (price - self.entry_price) if self.direction == "long" else (self.entry_price - price)

    # ===== 出場判斷 =====
    def should_stoploss(self, price: float, atr: float) -> bool:
        if not self.in_position:
            return False
        threshold = self.k_sl * atr
        pnl = self.get_unrealized_profit(price)
        return pnl <= -threshold

    def should_takeprofit(self, price: float, atr: float) -> bool:
        if not self.in_position:
            return False
        threshold = self.k_tp * atr
        pnl = self.get_unrealized_profit(price)
        return pnl >= threshold

    def should_exit_by_tick(self) -> bool:
        return self.in_position and self.tick_since_entry >= self.max_ticks

    def should_exit_by_time(self) -> bool:
        if not self.in_position or not self.entry_time:
            return False
        return datetime.now() - self.entry_time >= timedelta(minutes=self.max_minutes)

    def should_exit_by_score(self, exit_score: float) -> bool:
        """
        exit_score 越高越傾向出場
        """
        if not self.in_position:
            return False
        return exit_score >= self.exit_threshold

    def should_hold(self) -> bool:
        # 可加上更多條件，例如 bias_prob 或 momentum
        return True

    def should_add(self, price: float, tick: dict) -> bool:
        # 簡單加碼邏輯：若獲利超過一定值且 bias 強烈
        if not self.in_position:
            return False
        if self.get_unrealized_profit(price) > 2 * tick.get("atr", 1.0) and tick.get("bias_prob", 0.0) > 0.7:
            return True
        return False

    # ===== 狀態輸出 =====
    def get_status(self) -> dict:
        return {
            "in_position": self.in_position,
            "direction": self.direction,
            "entry_price": self.entry_price,
            "entry_time": self.entry_time,
            "current_position_size": self.current_position_size,
            "max_profit": self.max_profit,
            "max_loss": self.max_loss,
            "tick_since_entry": self.tick_since_entry,
            "mode": self.mode,
            "params_version": self.params_version,
        }

    def just_entered(self, seconds: int = 3) -> bool:
        if not self.entry_time:
            return False
        return (datetime.now() - self.entry_time).total_seconds() <= seconds
