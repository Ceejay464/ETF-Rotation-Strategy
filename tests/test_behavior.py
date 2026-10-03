"""Execution ordering and scoring ties on controlled daily data."""
from pathlib import Path
import sys
import unittest
import pandas as pd
from contextlib import redirect_stdout
from io import StringIO

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ETF轮动"))
from strategy.single_factor_full_strategy import SingleFactorFullStrategy
from engine.delay_full_engine import DelayFullEngine
from portfolio.portfolio import Portfolio


class RotationBehaviorTests(unittest.TestCase):
    def test_signal_uses_next_open_not_signal_day_close(self):
        dates = pd.date_range("2023-01-02", periods=3)
        data = {"A": pd.DataFrame({"开盘价": [10, 20, 30], "收盘价": [12, 22, 32]}, index=dates),
                "B": pd.DataFrame({"开盘价": [5, 6, 7], "收盘价": [5.5, 6.5, 7.5]}, index=dates)}
        factors = pd.DataFrame({"A": [2, 0, 0], "B": [1, 2, 2]}, index=dates)
        portfolio = Portfolio(100_000, etf_cost_rate=0, etf_slippage=0)
        engine = DelayFullEngine(data, SingleFactorFullStrategy(factors), portfolio)
        with redirect_stdout(StringIO()):
            result = engine.run()
        self.assertEqual(len(result), 3)
        first = portfolio.trade_history[0]
        self.assertEqual(first["timestamp"], dates[1])
        self.assertEqual(first["etf"], "A")
        self.assertEqual(first["price"], 20)
        self.assertEqual(portfolio.trade_history[-1]["etf"], "B")
        self.assertEqual(portfolio.trade_history[-1]["timestamp"], dates[2])

    def test_ties_use_input_column_order(self):
        date = pd.Timestamp("2023-01-02")
        factors = pd.DataFrame([[1, 1]], index=[date], columns=["B", "A"])
        strategy = SingleFactorFullStrategy(factors)
        with redirect_stdout(StringIO()):
            signal = strategy.generate_signal(date, {}, Portfolio(1000))
        self.assertEqual(signal["target_etf"], "B")

    def test_incompatible_instant_path_not_exposed(self):
        import subprocess
        result = subprocess.run([sys.executable, "-m", "local.run", "--demo", "--execution", "instant"],
                                cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("invalid choice", result.stderr)


if __name__ == "__main__":
    unittest.main()
