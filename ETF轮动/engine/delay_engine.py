import pandas as pd


class DelayEngine:

    def __init__(self, data, strategy, portfolio, start=None, end=None):
        self.data = data
        self.strategy = strategy
        self.portfolio = portfolio

        self.start = pd.Timestamp(start) if start else None
        self.end = pd.Timestamp(end) if end else None

        self.timeline = self._build_timeline()

        self.pending_orders = []
        self.results = []

    # =========================================================
    # build timeline with filter
    # =========================================================
    def _build_timeline(self):

        timeline = sorted(list(next(iter(self.data.values())).index))
        timeline = [pd.Timestamp(t) for t in timeline]

        if self.start is not None:
            timeline = [t for t in timeline if t >= self.start]

        if self.end is not None:
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

            price_dict = {etf: snapshot[etf]["开盘价"] for etf in snapshot}

            # =====================================================
            # 1️⃣ 执行上一天信号（open price）
            # =====================================================
            for order in self.pending_orders:

                etf = order["etf"]

                if etf not in snapshot:
                    continue

                self.portfolio.update_position(
                    timestamp=date,
                    etf_name=etf,
                    quantity=order["quantity"],
                    price=price_dict[etf]
                )

            self.pending_orders = []

            # =====================================================
            # 2️⃣ 当前生成信号（不执行）
            # =====================================================
            self.pending_orders = self.strategy.generate_signal(
                timestamp=date,
                data=snapshot,
                portfolio=self.portfolio
            )

            # =====================================================
            # 3️⃣ 估值（close price）
            # =====================================================
            close_price_dict = {etf: snapshot[etf]["收盘价"] for etf in snapshot}

            equity = self.portfolio.get_equity(timestamp=date, price_dict=close_price_dict)

            self.results.append({
                "timestamp": date,
                "equity": equity
            })

        return pd.DataFrame(self.results)