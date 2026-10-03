import pandas as pd


class Portfolio:

    def __init__(self, cash: float, etf_cost_rate=0.0001, etf_slippage=0.0, etf_min_cost=0.0):

        # Cash
        self.cash = cash

        # ETF positions
        # { "ETF_name": quantity }
        self.positions = {}

        # Costs
        self.etf_cost_rate = etf_cost_rate
        self.etf_slippage = etf_slippage
        self.etf_min_cost = etf_min_cost

        # Tracking
        self.trade_history = []
        self.equity_history = []

    # =========================================================
    # ETF trade
    # =========================================================
    def update_position(self, timestamp, etf_name, quantity, price):

        if price is None or pd.isna(price):
            print("未查询到ETF价格，交易失败！")
            return

        print(f"仓位变化：{etf_name}仓位变化：{quantity}")
        # Slippage
        if quantity > 0:
            trade_price = price * (1 + self.etf_slippage)
        else:
            trade_price = price * (1 - self.etf_slippage)

        # Update position
        self.positions[etf_name] = self.positions.get(etf_name, 0) + quantity

        if self.positions[etf_name] == 0:
            del self.positions[etf_name]

        # Cash update
        self.cash -= quantity * trade_price

        # Transaction cost
        cost = max(abs(quantity * trade_price) * self.etf_cost_rate, self.etf_min_cost) if quantity != 0 else 0

        self.cash -= cost

        # Record trade
        self.trade_history.append({
            "timestamp": timestamp,
            "etf": etf_name,
            "quantity": quantity,
            "price": price,
            "trade_price": trade_price,
            "cost": cost
        })

    # =========================================================
    # Close all positions
    # =========================================================
    def close_all(self, timestamp, price_dict):

        for etf in list(self.positions.keys()):

            qty = self.positions[etf]
            price = price_dict.get(etf, None)

            if price is None or pd.isna(price):
                continue

            self.update_position(
                timestamp=timestamp,
                etf_name=etf,
                quantity=-qty,
                price=price
            )

    # Equity
    def get_equity(self, timestamp, price_dict):

        equity = self.cash

        for etf, qty in self.positions.items():

            price = price_dict.get(etf, None)

            if price is None or pd.isna(price):
                continue

            equity += qty * price

        self.equity_history.append({
            "timestamp": timestamp,
            "equity": equity
        })

        return equity
    
    def full_rebalance(self, timestamp, target_etf, price_dict):

        # 1️⃣ 清仓所有持仓
        for etf in list(self.positions.keys()):

            qty = self.positions[etf]
            price = price_dict.get(etf, None)

            if price is None or pd.isna(price):
                continue

            if qty != 0:
                self.update_position(timestamp=timestamp, etf_name=etf, quantity=-qty, price=price)

        # 2️⃣ 用全部现金买目标ETF
        price = price_dict[target_etf]
        if price is None or pd.isna(price):
            print("今天无价格传入")
            return

        trade_price = price * (1 + self.etf_slippage)
        cost_per_unit = trade_price * (1 + self.etf_cost_rate)
        qty = int(self.cash / cost_per_unit // 100 * 100)

        if qty <= 0:
            return

        self.update_position(timestamp=timestamp, etf_name=target_etf, quantity=qty, price=price)

    def drawdown_series(self, equity, window=25):

        # 1. 初始化存储容器
        if not hasattr(self, "historical_highest"):
            self.historical_highest = equity

        if not hasattr(self, "dd_series"):
            self.dd_series = []

        # 2. 更新历史最高净值
        if equity > self.historical_highest:
            self.historical_highest = equity

        # 3. 计算当前回撤
        dd = (self.historical_highest - equity) / self.historical_highest

        # 4. 记录序列
        if dd > 0:
            self.dd_series.append(dd)

        # 5. rolling max drawdown
        window_dd = self.dd_series[-window:]

        rolling_mdd = max(window_dd) if window_dd else dd

        return self.dd_series.copy(), dd


    # Utility
    def get_positions(self):
        return self.positions

    def get_cash(self):
        return self.cash