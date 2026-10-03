# Local reproduction

## 1. Environment

Extract the archive and work from the directory containing README.md. Base entry points require Python 3.10+. The verified environment used Python 3.13, NumPy 2.4.4, pandas 3.0.2, and openpyxl 3.1.5.

```bash
python -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

`requirements.txt` lists base dependency ranges. `requirements-tested.txt` records actual verified versions, without claiming coverage of all Python versions. Optional original-notebook dependencies are listed in `requirements-notebooks.txt`; base entry points need no SciPy, Matplotlib, Plotly, or Jupyter installation.

## 2. Input data

Price input is a CSV/Excel long table with `date,symbol,open,high,low,close`.
Factor input is a CSV/Excel wide table: `date` followed by columns exactly matching the price symbols, with one daily score per cell.

Each price date needs a factor row. All-NaN factor rows retain the original skip behavior; partial NaNs are preserved.
Ties follow the original factor-column order. Prices must cover all symbols on every date. Duplicates, infinite scores,
and invalid OHLC ranges are rejected without silently filling observations.

Real factor scores should use only information available at the time. The entry point does not infer publication timestamps or automatically remove future information.
Quantile-control settings are `--quantile 0.95 --dd-window 252 --breach-days 3 --cooldown-days 3`.
Use `--strategy absolute --abs-dd 0.10` for the original absolute-drawdown variant. These controls do not affect `plain`.

The original immediate full-allocation path is incompatible with the available strategy signal interface and is not exposed.
Running the old notebooks requires the missing indicator/loader modules and `etf_panel.pkl`. Synthetic scores are not a reconstruction of those factors.

## 3. Run

```bash
python -m local.run --demo --output runs/demo
python -m local.run --demo --strategy quantile --output runs/demo_quantile
python -m local.run --prices /path/to/prices.csv --factors /path/to/factors.csv --execution delayed --output runs/real
```

Use `python -m local.run --help` for all options.

## 4. Read outputs

Open your run's `report.html` directly in a browser. Reports use tables and do not generate additional unapproved images.

- `equity.csv`: daily engine equity plus presentation-only `normalized_equity` and `drawdown` fields.
- `trades.csv`: original-engine or adapter transaction records, labeled accordingly.
- `summary.json`: configuration, data kind, dependency versions, and input/source SHA-256 hashes.
- `run.log`: original strategy logs.

Terminal positions are retained, without an added forced liquidation. Select a fresh output directory for another run.

## 5. Verify retained sources and entry-point boundaries

```bash
python -m local.verify_originals
python -m unittest discover -s tests -v
```
