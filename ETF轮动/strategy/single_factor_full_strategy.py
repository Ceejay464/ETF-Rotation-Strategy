import pandas as pd


class SingleFactorFullStrategy:

    def __init__(self, factor_df):

        self.factor_df = factor_df
        self.last_target = None

    # =========================================================
    # signal generation
    # =========================================================
    def generate_signal(self, timestamp, data, portfolio):

        # 1️⃣ 时间检查
        if timestamp not in self.factor_df.index:
            return None

        row = self.factor_df.loc[timestamp]

        # 2️⃣ 缺失检查
        if row.isna().all():
            print("今天因子数据缺失")
            return None

        # 3️⃣ 选最大因子ETF
        target_etf = row.idxmax()
        print(f"今日因子最大ETF: {target_etf}, value={row[target_etf]}")

        # 4️⃣ 降低换手
        if self.last_target == target_etf:
            print("无变化，不调仓")
            return None

        self.last_target = target_etf

        # 5️⃣ 只返回 ETF（关键修改）
        return {"type": "rebalance", "target_etf": target_etf}