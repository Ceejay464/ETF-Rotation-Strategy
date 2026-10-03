import pandas as pd
import numpy as np


class SingleFactorAbsStpStrategy:

    def __init__(self, factor_df, dd_breach_days=3, cooldown_days=2, dd_window=252, abs_dd_threshold=0.1):

        self.factor_df = factor_df
        self.last_target = None

        # Risk control parameters
        self.abs_dd_threshold = abs_dd_threshold
        self.dd_window = dd_window
        self.dd_breach_days = dd_breach_days # Close only after consecutive closing signals
        self.cooldown_days_default = cooldown_days

        # State machine
        self.stop_flag = False
        self.cooldown_days = 0
        self.stop_trigger_date = None

        # Consecutive trigger counter
        self.dd_breach_count = 0

    # =========================================================
    # Main signal function
    # =========================================================
    def generate_signal(self, timestamp, data, portfolio):
        
        orders = []
        # =====================================================
        # 1. Update equity and drawdown series from the portfolio
        # =====================================================
        snapshot = data
        close_price_dict = {etf: snapshot[etf]["收盘价"] for etf in snapshot}
        equity = portfolio.get_equity(timestamp=timestamp, price_dict=close_price_dict)

        dd_series, current_dd = portfolio.drawdown_series(equity, window=self.dd_window)

        # Rolling check over the most recent window
        recent_dd = dd_series

        # =====================================================
        # 4. Cooldown period
        # =====================================================
        if self.stop_flag:

            self.cooldown_days -= 1

            print(f"Cooldown remaining {self.cooldown_days}  days")

            if self.cooldown_days > 0:
                return None

            # Cooldown ends
            print("Cooldown ended; resume trading")

            self.stop_flag = False

        # =====================================================
        # 2. Risk controls with consecutive triggers
        # =====================================================
        if len(recent_dd) >= self.dd_window:

            if current_dd > self.abs_dd_threshold:
                self.dd_breach_count += 1
            else:
                self.dd_breach_count = 0

        # =====================================================
        # 3. Trigger stop loss
        # =====================================================
        if self.dd_breach_count >= self.dd_breach_days:

            print(f"[RISK OFF] Consecutive {self.dd_breach_count}  days of excessive drawdown; close positions")

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
        # 5. Normal factor logic
        # =====================================================
        if timestamp not in self.factor_df.index:
            return None

        row = self.factor_df.loc[timestamp]

        if row.isna().all():
            return None

        target_etf = row.idxmax()

        print(f"ETF with the highest factor score today: {target_etf}, value={row[target_etf]}")

        if self.last_target == target_etf:
            return None

        self.last_target = target_etf

        return {"type": "rebalance", "target_etf": target_etf}