import pandas as pd
import numpy as np


class SingleFactorFullStpLossStrategy:

    def __init__(self, factor_df, max_drawdown_threshold=0.90, dd_window=252, dd_breach_days=3, cooldown_days=2):

        self.factor_df = factor_df
        self.last_target = None

        # 风控参数
        self.max_drawdown_threshold = max_drawdown_threshold
        self.dd_window = dd_window
        self.dd_breach_days = dd_breach_days # 连续发出平仓信号才进行平仓
        self.cooldown_days_default = cooldown_days

        # 状态机
        self.stop_flag = False
        self.cooldown_days = 0
        self.stop_trigger_date = None

        # 连续触发计数
        self.dd_breach_count = 0

    # =========================================================
    # 主信号函数
    # =========================================================
    def generate_signal(self, timestamp, data, portfolio):
        
        orders = []
        # =====================================================
        # 1. 更新 equity + drawdown series（从 portfolio）
        # =====================================================
        snapshot = data
        close_price_dict = {etf: snapshot[etf]["收盘价"] for etf in snapshot}
        equity = portfolio.get_equity(timestamp=timestamp, price_dict=close_price_dict)

        dd_series, current_dd = portfolio.drawdown_series(equity, window=self.dd_window)

        # rolling 判断（最近 window）
        recent_dd = dd_series

        # =====================================================
        # 4. 冷却期
        # =====================================================
        if self.stop_flag:

            self.cooldown_days -= 1

            print(f"冷却期剩余 {self.cooldown_days} 天")

            if self.cooldown_days > 0:
                return None

            # 冷却结束
            print("冷却结束，恢复交易")

            self.stop_flag = False

        # =====================================================
        # 2. 风控逻辑（连续触发）
        # =====================================================
        if len(recent_dd) >= self.dd_window:
            threshold = np.quantile(dd_series, self.max_drawdown_threshold)

            if current_dd > threshold:
                self.dd_breach_count += 1
            else:
                self.dd_breach_count = 0

        # =====================================================
        # 3. 触发止损
        # =====================================================
        if self.dd_breach_count >= self.dd_breach_days:

            print(f"[RISK OFF] 连续 {self.dd_breach_count} 天回撤过大，平仓")

            self.stop_flag = True
            self.cooldown_days = self.cooldown_days_default

            self.stop_trigger_date = timestamp

            self.last_target = None
            self.dd_breach_count = 0

            current_positions = portfolio.get_positions()
            for etf, qty in current_positions.items():
                orders.append({"etf": etf, "quantity": -qty})

            return {"type": "risk_off", "orders": orders}

        # =====================================================
        # 5. 正常因子逻辑
        # =====================================================
        if timestamp not in self.factor_df.index:
            return None

        row = self.factor_df.loc[timestamp]

        if row.isna().all():
            return None

        target_etf = row.idxmax()

        print(f"今日因子最大ETF: {target_etf}, value={row[target_etf]}")

        if self.last_target == target_etf:
            return None

        self.last_target = target_etf

        return {"type": "rebalance", "target_etf": target_etf}