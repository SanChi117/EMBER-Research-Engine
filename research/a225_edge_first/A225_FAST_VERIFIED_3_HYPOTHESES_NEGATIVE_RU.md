# A225 — завершён: независимый экономический фальсификационный тест 3 Price Action гипотез

Дата: 2026-10-31. PREREG: [PREREG_EVIDENCE_FIRST_4H_LEVELS.md](PREREG_EVIDENCE_FIRST_4H_LEVELS.md), commit `73a6e84643f6bd028cda4959bf04e5dd49a5400b` **до** появления результатов. [CI run 41230801427](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41230801427) SUCCESS, [artifact](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41230801427) `a225-authenticated-futures-4h-event-economics`, id `13053647110`, sha256 `8c22ac1c8ee7fc8b1770cf66bc80293b1ee302451ad61d093bda56f1e165d4b8`. ZIP/CSV originals 204/204 SHA совпали с A217. Рынок **реальные BTC/ETH/SOL Binance USDT-M futures OHLCV и fundingRate** 2023-11…2026-09. Никаких Spot, случайно придуманных сделок, настоящих ордеров или старого PAPER. Это первичная исследовательская гипотеза, **не готовая оригинальная стратегия**.

Ни один из трёх заранее зафиксированных механизмов не прошёл исследовательский stress-gate `>=2 отдельных года >0 после STRESS`:

| Гипотеза | 2024 BASE / STRESS | 2025 BASE / STRESS | 2026 янв–сен BASE / STRESS | Записанных завершённых сделок по годам |
|---|---:|---:|---:|---:|
| E1: 4h reaction → opposite 4h level | −17.42 / **−28.21%** | −10.34 / **−22.16%** | −6.10 / **−14.74%** | 547 / 530 / 315 |
| E2: 4h breakout → 1h retest | +0.64 / **−1.28%** | −2.06 / **−3.97%** | −2.04 / **−3.83%** | 185 / 187 / 145 |
| E3: 4h compression → 1h expansion | +1.46 / **−2.01%** | −3.36 / **−7.05%** | −0.69 / **−3.98%** | 203 / 199 / 139 |

BASE roundtrip costs = 21bps, STRESS = 45bps **per roundtrip**, excluding real signed funding (which was additionally charged). One virtual model $1000 per BTC/ETH/SOL sleeve, risk 0.5% per trade and 1x maximum notional. Tested 2024 / 2025 / Jan–Sep 2026 independently, no parameter sweep or tuning. Values are return on sum of sleeve equities and do **not** include operational Binance margin/liquidation ledger. Full [raw CI artifact](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41230801427) contains JSON result, per-coin metrics, trade journal, receipt evidence.

**Вердикт: `RESEARCH_NEGATIVE_FAST_ECONOMIC_SCREEN` for specific preset E1/E2/E3 only.** Не перебирать ATR/окна и не выдавать эти варианты за успешно работающий edge. Это не опровержение Price Action в целом и не тест готового существующего исходного кода. Но рационально: не искать источник, реализующий конкретно **эти три конструкции**, и не тратить время на глубокое восстановление. Продолжать поиск других эмпирически обоснованных независимо различных механизмов.

Ограничения даже для отрицательного результата: нет официального mark, liquidation tiers; в OHLCV модельные stop fills с optimistic assumption, пока нет funding/survivorship point-in-time portfolio across changing symbols (фиксировано 3 majors). Поскольку даже при оптимистичном условии нет плюса в STRESS, дальнейшее изучение этих точных вариантов нецелесообразно. Никаких сделок и изменения существующих сценариев.
