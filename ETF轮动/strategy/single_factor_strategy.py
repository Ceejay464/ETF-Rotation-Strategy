import pandas as pd


class SingleFactorStrategy:

    def __init__(self, factor_df, target_qty=100_0000):
        """
        pct_change_df:
            index = date
            columns = ETF
            values = pct change

        target_qty:
            每次目标持仓数量
        """
        self.factor_df = factor_df
        self.target_qty = target_qty

        self.last_target = None

    # =========================================================
    # signal generation
    # =========================================================
    def generate_signal(self, timestamp, data, portfolio):

        # 当前日期的所有ETF涨跌幅
        if timestamp not in self.factor_df.index:
            return []

        row = self.factor_df.loc[timestamp]

        # 如果全是 NaN
        if row.isna().all():
            print("今天因子数据缺失")
            return []

        # =====================================================
        # 1️⃣ 选涨幅最大的ETF
        # =====================================================
        target_etf = row.idxmax()
        print(f"今日因子最大etf为：{target_etf}，其因子为：{row[target_etf]}")

        # 如果没有变化，不交易（降低换手）
        if self.last_target == target_etf:
            print("因子相对大小没有变化，不交易")
            return []

        self.last_target = target_etf

        # =====================================================
        # 2️⃣ 当前持仓
        # =====================================================
        current_positions = portfolio.get_positions()

        orders = []

        # =====================================================
        # 3️⃣ 先平掉所有非目标ETF
        # =====================================================
        for etf, qty in current_positions.items():

            if etf != "underlying" and qty != 0:

                orders.append({
                    "etf": etf,
                    "quantity": -qty
                })

        # =====================================================
        # 4️⃣ 开仓目标ETF（使用参数）
        # =====================================================
        orders.append({
            "etf": target_etf,
            "quantity": self.target_qty
        })

        return orders