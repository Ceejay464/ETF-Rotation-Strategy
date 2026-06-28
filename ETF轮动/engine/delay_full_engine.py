import pandas as pd


class DelayFullEngine:

    def __init__(self, data, strategy, portfolio, start=None, end=None):

        self.data = data
        self.strategy = strategy
        self.portfolio = portfolio

        self.start = pd.Timestamp(start) if start else None
        self.end = pd.Timestamp(end) if end else None

        self.timeline = self._build_timeline()

        # =========================
        # 延迟信号缓存
        # =========================
        self.pending_target = None

        self.results = []

    # =========================================================
    # timeline
    # =========================================================
    def _build_timeline(self):

        timeline = sorted(list(next(iter(self.data.values())).index))
        timeline = [pd.Timestamp(t) for t in timeline]

        if self.start:
            timeline = [t for t in timeline if t >= self.start]

        if self.end:
            timeline = [t for t in timeline if t <= self.end]

        return timeline

    # =========================================================
    # snapshot
    # =========================================================
    def get_snapshot(self, date):

        snapshot = {}

        for name, df in self.data.items():
            if date in df.index:
                snapshot[name] = df.loc[date]

        return snapshot

    # =========================================================
    # run
    # =========================================================
    def run(self):

        for i in range(len(self.timeline)):

            date = self.timeline[i]
            print(date)

            snapshot = self.get_snapshot(date)

            if not snapshot:
                continue

            # =====================================================
            # 1️⃣ OPEN PRICE DICT
            # =====================================================
            open_price_dict = {etf: snapshot[etf]["开盘价"] for etf in snapshot}

            # =====================================================
            # 2️⃣ 执行上一天信号（全仓）
            # =====================================================
            if self.pending_target is not None:
                if self.pending_target["type"] == "rebalance":
                    print("重新开仓")
                    etf = self.pending_target["target_etf"]
                    self.portfolio.full_rebalance(timestamp=date, target_etf=etf, price_dict=open_price_dict)
                    self.pending_target = None

                else:
                    print("回撤太大强制平仓")
                    orders = self.pending_target["orders"]
                    for order in orders:
                        etf = order["etf"]
                        qty = order["quantity"]  
                        price = open_price_dict.get(etf, None)                      
                        self.portfolio.update_position(timestamp=date, etf_name=etf, quantity=qty, price=price)
                        self.pending_target = None

            # =====================================================
            # 3️⃣ 当前生成信号（保存，下一天执行）
            # =====================================================
            signal = self.strategy.generate_signal( timestamp=date, data=snapshot, portfolio=self.portfolio)

            if signal:
                self.pending_target = signal

            # =====================================================
            # 4️⃣ CLOSE PRICE VALUATION
            # =====================================================
            close_price_dict = {etf: snapshot[etf]["收盘价"] for etf in snapshot}

            equity = self.portfolio.get_equity(timestamp=date, price_dict=close_price_dict)

            self.results.append({
                "timestamp": date,
                "equity": equity
            })

        return pd.DataFrame(self.results)