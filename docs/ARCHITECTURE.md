# EMBER Architecture

## Data layer

`DataEngine` exposes the exact specification interface:

```python
load_csv(path) -> pl.LazyFrame
fetch_binance(symbols, interval, limit) -> pl.DataFrame
validate(lf) -> pl.LazyFrame
resample(lf, from_tf, to_tf) -> pl.LazyFrame
```

Validation enforces:

- `high >= max(open, close)`;
- `low <= min(open, close)`;
- `high >= low`;
- `volume >= 0`;
- chronological ordering per symbol;
- deterministic deduplication by `(symbol, time)`.

## Feature layer

Features are built with Polars expressions. Confirmed swing events are emitted two bars after the pivot so the feature stream never needs future prices at the decision row.

Implemented columns include ATR, swing events and prices, BOS/CHoCH, FVG and age, simplified mitigation, order blocks, volume ratio, volatility regime, PDA position and UTC session.

## Context layer

At every entry timestamp the context builder filters all HTF bars to `time <= entry_time`. It derives:

- 4H-preferred / 1D-fallback EMA20 bias;
- HTF swing structure;
- recent liquidity sweep;
- approximate active HTF FVG/OB;
- entry-time PDA, session, volume ratio and ATR.

## Strategy layer

HYBRID v2 enables only:

- `pullback`;
- `ignition`.

The remaining named setup types stay blocked by configuration and are not fabricated.

## Risk and exits

Risk is sized from equity and stop distance. Stop distance is ATR-based and clamped to 0.5%-5%. The target is at least 1.8R. Fees and slippage must leave positive net edge.

Exit simulation starts on the first bar strictly after entry. Bull bars use OLHC; bear and neutral bars use OHLC. A stop receives adverse slippage. A trade without enough future bars returns `None`.

## Learning and validation

Quality scoring is outcome-blind. Structure scoring uses only closed trades where `exit_time < entry_time`. WFO inserts an embargo between train and test windows.

## Paper mode

The FastAPI paper server writes only virtual trades to SQLite and exposes health, status, trade history, CSV export and a virtual webhook.
