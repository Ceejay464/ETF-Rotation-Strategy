"""Replay precomputed factors through the unchanged ETF rotation strategies."""
from pathlib import Path
import argparse
import sys
import numpy as np
import pandas as pd
from .common import (load_panel, load_table, daily_dates, select_dates, prepare_output,
                     run_log, export_run, require_columns)

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "ETF轮动"


def run(args):
    sys.path.insert(0, str(SOURCE))
    from portfolio.portfolio import Portfolio
    from strategy.single_factor_full_strategy import SingleFactorFullStrategy
    from strategy.single_factor_full_stploss_strategy import SingleFactorFullStpLossStrategy
    from strategy.single_factor_abs_stp_strategy import SingleFactorAbsStpStrategy
    from engine.delay_full_engine import DelayFullEngine
    price_path = ROOT / "examples/demo_prices.csv" if args.demo else args.prices
    factor_path = ROOT / "examples/demo_factors.csv" if args.demo else args.factors
    panel, price_path = load_panel(price_path)
    panel = select_dates(panel, args.start, args.end)
    factors, factor_path = load_table(factor_path)
    require_columns(factors, ["date"], "factors")
    factors["date"] = daily_dates(factors["date"])
    if factors["date"].duplicated().any():
        raise ValueError("Duplicate factor dates")
    factors = factors.set_index("date").sort_index()
    symbols = sorted(panel["symbol"].unique())
    if list(factors.columns) != symbols:
        # Do not reorder columns: idxmax tie-breaks depend on column order.
        if set(factors.columns) != set(symbols):
            raise ValueError("Factor columns must exactly match price symbols")
    for col in factors.columns:
        factors[col] = pd.to_numeric(factors[col], errors="raise")
    if np.isinf(factors.to_numpy(dtype=float)).any():
        raise ValueError("Factors cannot contain infinite scores; NaN is allowed")
    if not set(panel["date"].unique()) <= set(factors.index):
        raise ValueError("Every price date needs a factor row; use all-NaN scores to skip a date")
    data = {}
    for symbol, frame in panel.groupby("symbol", sort=True):
        data[symbol] = frame.set_index("date").rename(
            columns={"open": "开盘价", "close": "收盘价"})
    portfolio = Portfolio(args.cash, etf_cost_rate=0.00005, etf_slippage=0.0005,
                          etf_min_cost=0)
    if args.strategy == "plain":
        strategy = SingleFactorFullStrategy(factors)
    elif args.strategy == "quantile":
        strategy = SingleFactorFullStpLossStrategy(factors,
            max_drawdown_threshold=args.quantile, dd_window=args.dd_window,
            dd_breach_days=args.breach_days, cooldown_days=args.cooldown_days)
    else:
        strategy = SingleFactorAbsStpStrategy(factors, abs_dd_threshold=args.abs_dd,
            dd_window=args.dd_window, dd_breach_days=args.breach_days,
            cooldown_days=args.cooldown_days)
    # Original InstantFullEngine expects a list while these strategies emit a
    # dictionary; do not silently repair/change that original execution path.
    engine_cls = DelayFullEngine
    engine = engine_cls(data=data, strategy=strategy, portfolio=portfolio,
                        start=args.start, end=args.end)
    output = prepare_output(args.output)
    with run_log(output):
        results = engine.run()
    export_run(ROOT, output, results, portfolio.trade_history, args.cash, {
        "project": "ETF Rotation / Precomputed Factors", "accent": "#008f9b",
        "demo": args.demo,
        "data_kind": "SYNTHETIC DEMO DATA — arbitrary factor scores" if args.demo else "User-supplied prices and precomputed factors",
        "engine": f"Original {engine_cls.__name__}", "parameters": vars(args),
        "factor_column_order": list(factors.columns),
        "terminal_positions": portfolio.get_positions(),
        "costs": {"etf_rate": 0.00005, "etf_slippage_fraction": 0.0005},
        "execution_note": "Delayed: previous signal at next open. "
                          "Original risk-control ordering, factor tie-breaks and cooling preserved.",
    }, [price_path, factor_path])


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--demo", action="store_true", help="Use explicitly synthetic bundled fixtures")
    p.add_argument("--prices")
    p.add_argument("--factors")
    p.add_argument("--strategy", choices=["plain", "quantile", "absolute"], default="plain")
    p.add_argument("--execution", choices=["delayed"], default="delayed",
                   help="Only the verified delayed full-allocation path is exposed")
    p.add_argument("--cash", type=float, default=1_000_000)
    p.add_argument("--start")
    p.add_argument("--end")
    p.add_argument("--quantile", type=float, default=0.95)
    p.add_argument("--abs-dd", type=float, default=0.10)
    p.add_argument("--dd-window", type=int, default=252)
    p.add_argument("--breach-days", type=int, default=3)
    p.add_argument("--cooldown-days", type=int, default=3)
    p.add_argument("--output", default="runs/rotation")
    args = p.parse_args()
    if args.demo and (args.prices or args.factors):
        p.error("--demo cannot be combined with real input paths")
    if not args.demo and not (args.prices and args.factors):
        p.error("Provide --prices and --factors, or explicitly select --demo")
    try:
        if not np.isfinite(args.cash) or args.cash <= 0:
            raise ValueError("cash must be positive")
        if not 0 < args.quantile < 1 or not 0 < args.abs_dd < 1:
            raise ValueError("quantile and abs-dd must lie between 0 and 1")
        if min(args.dd_window, args.breach_days, args.cooldown_days) < 1:
            raise ValueError("Risk-control window/counters must be at least 1")
        run(args)
    except (ValueError, FileNotFoundError) as e:
        p.error(str(e))


if __name__ == "__main__":
    main()
