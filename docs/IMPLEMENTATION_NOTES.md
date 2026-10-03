# Implementation notes and reproduction boundaries

These notes compare the supplied code with its original documentation. Important behavior is retained; discrepancies are documented rather than silently repaired.

- Factor-calculation and data-loader modules are missing. All original factor formulas cannot be established from the archive; the new entry point accepts precomputed scores only.
- The original `idxmax()` selects the first column when scores tie. Input factor-column order is retained.
- Normal signals are generated only when the target changes, rather than requiring a trade every day.
- Immediate/delayed and fixed-quantity/full-allocation engines are different paths. All original files remain; the new entry point focuses on the verified delayed full-allocation path.
- The drawdown series appends only positive drawdowns. `dd_window` controls how many recorded drawdowns are needed before checks, while `drawdown_series` returns the entire recorded series. The quantile rule therefore does not use a conventional rolling window of the latest 252 trading days. This behavior remains unchanged.
- Risk-control strategies and engines both call valuation, potentially creating duplicate dates in internal `equity_history`. Reports use one daily record from `engine.results`.
- Numerical notebook costs are commission 0.00005 and relative slippage 0.0005, unlike the original README's percentage wording.
- Existing notebook charts and outputs are retained; no unapproved performance images were added.
- `InstantFullEngine` reads `signal[0]["etf"]`, whereas the current full-allocation strategies return a dictionary. Combining them raises `KeyError: 0`. That engine also skips valuation when no signal is produced. It is retained unchanged and is not exposed by the new runner.
