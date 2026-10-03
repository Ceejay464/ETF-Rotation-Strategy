import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def plot_strategy_vs_buyhold(df_etf, result, initial_cash=1_000_000):

    # =========================================================
    # 1️⃣ strategy equity
    # =========================================================
    plt.figure(figsize=(12, 6))
    plt.plot(result["timestamp"], result["equity"], label="Strategy", linewidth=2)

    # =========================================================
    # 2️⃣ buy & hold for each ETF
    # =========================================================
    for etf_name, df in df_etf.items():

        close = df["收盘价"].copy()

        # normalize to 1
        bh = close / close.iloc[0] * initial_cash

        plt.plot(bh.index, bh.values, alpha=0.6, linestyle="--", label=f"B&H {etf_name}")

    # =========================================================
    # 3️⃣ style
    # =========================================================
    plt.title("Strategy vs Buy & Hold (All ETFs)")
    plt.xlabel("Date")
    plt.ylabel("Portfolio Value")
    plt.legend()
    plt.grid(True)

    plt.show()


def performance_metrics(equity):
    df = equity.copy()

    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')
    df = df.set_index('timestamp')

    equity = df['equity']
    equity = equity.dropna()

    # returns
    ret = equity.pct_change().dropna()

    # drawdown
    cummax = equity.cummax()
    dd = equity / cummax - 1

    # time
    days = (equity.index[-1] - equity.index[0]).days

    # metrics
    cagr = (equity.iloc[-1] / equity.iloc[0]) ** (365 / days) - 1
    vol = ret.std() * np.sqrt(252)
    sharpe = ret.mean() / ret.std() * np.sqrt(252)
    mdd = dd.min()
    calmar = cagr / abs(mdd)

    return {
        "CAGR": cagr,
        "Volatility": vol,
        "Sharpe": sharpe,
        "Max Drawdown": mdd,
        "Calmar": calmar
    }

def build_trade_pairs(df):

    df = df.copy()

    # =========================
    # 1. 基础处理
    # =========================
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values(["etf", "timestamp"])

    trades = []

    # =========================
    # 2. 按 ETF 处理
    # =========================
    for etf, g in df.groupby("etf"):

        pos = 0
        entry_price = None
        entry_time = None
        entry_cost = 0

        for row in g.itertuples():

            qty = row.quantity
            price = row.trade_price
            t = row.timestamp

            prev_pos = pos
            pos += qty

            # =========================
            # 开仓（从0到非0）
            # =========================
            if prev_pos == 0 and pos != 0:
                entry_time = t
                entry_price = price
                entry_cost = row.cost

            # =========================
            # 平仓（从非0到0）
            # =========================
            elif prev_pos != 0 and pos == 0:

                exit_price = price
                exit_time = t

                pnl = (exit_price - entry_price) * prev_pos

                trades.append({
                    "etf": etf,
                    "entry_time": entry_time,
                    "exit_time": exit_time,
                    "direction": "LONG" if prev_pos > 0 else "SHORT",
                    "quantity": prev_pos,
                    "entry_price": entry_price,
                    "exit_price": exit_price,
                    "holding_days": (exit_time - entry_time).days,
                    "pnl": pnl,
                    "return": pnl / (abs(entry_price * prev_pos) + 1e-12)
                })

                entry_time = None
                entry_price = None
                entry_cost = 0

    return pd.DataFrame(trades)