# Synthetic demonstration fixtures

`demo_prices.csv` contains artificial price paths generated with seed 42. Dates follow a business-day sequence without an exchange holiday calendar. These inputs verify runtime paths and state changes, not historical investment performance.

`demo_factors.csv` contains arbitrary sinusoidal scores, not reconstructed trend or momentum factors from the absent original indicator modules.

`*_template.csv` files contain headers only. Supply real market data separately and never mix synthetic rows into a historical dataset.
