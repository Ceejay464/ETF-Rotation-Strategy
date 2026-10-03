import pandas as pd


class InstantEngine:

    def __init__(self, data, strategy, portfolio, start=None, end=None):
        self.data = data
        self.strategy = strategy
        self.portfolio = portfolio

        self.start = pd.Timestamp(start) if start else None
        self.end = pd.Timestamp(end) if end else None

        self.timeline = self._build_timeline()

        self.results = []

    # =========================================================
    # build timeline with filter
    # =========================================================
    def _build_timeline(self):

        timeline = sorted(list(next(iter(self.data.values())).index))

        # 转成 Timestamp（防止字符串）
        timeline = [pd.Timestamp(t) for t in timeline]

        if self.start is not None:
            timeline = [t for t in timeline if t >= self.start]

        if self.end is not None:
            timeline = [t for t in timeline if t <= self.end]

        return timeline

    # =========================================================
    # get snapshot
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

        for date in self.timeline:
            print(date)
            snapshot = self.get_snapshot(date)

            if not snapshot:
                continue

            price_dict = {etf: snapshot[etf]["收盘价"] for etf in snapshot}

            # ===== strategy =====
            orders = self.strategy.generate_signal(timestamp=date, data=snapshot, portfolio=self.portfolio)

            # ===== execute at CLOSE =====
            for order in orders:

                self.portfolio.update_position(
                    timestamp=date,
                    etf_name=order["etf"],
                    quantity=order["quantity"],
                    price=price_dict[order["etf"]]
                )

            # ===== equity =====
            equity = self.portfolio.get_equity(timestamp=date, price_dict=price_dict)

            self.results.append({
                "timestamp": date,
                "equity": equity
            })

        return pd.DataFrame(self.results)