import pandas as pd


class InstantFullEngine:

    def __init__(self, data, strategy, portfolio, start=None, end=None):

        self.data = data
        self.strategy = strategy
        self.portfolio = portfolio

        self.start = pd.Timestamp(start) if start else None
        self.end = pd.Timestamp(end) if end else None

        self.timeline = self._build_timeline()

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

        for date in self.timeline:

            snapshot = self.get_snapshot(date)

            if not snapshot:
                continue

            # =========================
            # price dict
            # =========================
            price_dict = {
                etf: snapshot[etf]["收盘价"]
                for etf in snapshot
            }

            # =========================
            # strategy signal
            # =========================
            signal = self.strategy.generate_signal(
                timestamp=date,
                data=snapshot,
                portfolio=self.portfolio
            )

            # =========================
            # handle empty signal
            # =========================
            if not signal:
                continue

            target_etf = signal[0]["etf"]

            # =========================
            # FULL REBALANCE (instant)
            # =========================
            self.portfolio.close_all(date, price_dict)

            # buy target fully
            price = price_dict[target_etf]

            trade_price = price * (1 + self.portfolio.etf_slippage)
            cost_per_unit = trade_price * (1 + self.portfolio.etf_cost_rate)

            qty = int(self.portfolio.cash / cost_per_unit)

            if qty > 0:
                self.portfolio.update_position(
                    timestamp=date,
                    etf_name=target_etf,
                    quantity=qty,
                    price=price
                )

            # =========================
            # equity
            # =========================
            equity = self.portfolio.get_equity(
                timestamp=date,
                price_dict=price_dict
            )

            self.results.append({
                "timestamp": date,
                "equity": equity
            })

        return pd.DataFrame(self.results)