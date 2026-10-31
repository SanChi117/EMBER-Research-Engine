# A213 — заранее замороженный OFF-SEASON holdout двухногого funding carry

Дата 2026-10-31. Запись **до PnL**. Исходная гипотеза A212: spot LONG + perpetual SHORT одинаковым количеством монет, 4 segregated $1000 wallets (BTC/ETH/SOL/LINK), nominal spot $100/coin, reserve 3x underlying perp short collateral, original BASE/STRESS costs.

Результат A212 был положителен у ALWAYS на May13-Sep30 во всех 2024/25/26 годах, но это только 12 открытий-закрытий в 3 сезонах, с относительно небольшим доходом 0.07–0.23% за 141 день относительно 4000USDT и неполным учётом реального исполнения. Вариант selective на trailing9 funding threshold 0.0001 дал отрицательный результат или не торговал. **Запрещается использовать эти результаты для выбора нового threshold и fee; ставим независимый HOLDOUT без переоптимизации.**

## Новый неиспользованный A212 период: 3 «зимы», включающие другие режимы
- `2023-10-01 00:00 UTC – 2024-05-01 00:00 UTC` (end exclusive)
- `2024-10-01 00:00 UTC – 2025-05-01 00:00 UTC`
- `2025-10-01 00:00 UTC – 2026-05-01 00:00 UTC`

Все месяцы Oct–Apr, по 7 реальных календарных месяцев (разная продолжительность 212/213 дней). Эти интервалы **не проверялись в A212**, но другие старые исследования EMBER могли частично затрагивать даты; не обещать истинного never-seen OOS.

## Абсолютно неизменная стратегия

Идентичный исходный `research/strategy_research_reset_20261031/a212_real_spot_perp_funding_carry.py` из ветки A212, original source replayer; A213 создаёт **только копию с новыми календарными параметрами и labels**, не меняя активные торговые правила:
- `ALWAYS`: hold spot LONG / perp SHORT same asset q от первого UTC hourly open периода до последнего 1h close; полноценный spot/perp basis, funding short sign, four-leg taker fees, spread/slippage.
- `SELECTIVE`: previous 9 settled funding rates only, threshold0.0001; at hourly open после сигнала, start/stop both legs; никакого будущего funding.
- Spot nominal100 USDT per $1000 independent wallet, perp matched qty, separate margin reserve3×, approximate mark-based funding, 1h mark-to-market and approximate collateral risk, no DCA, same symbol universe.
- Fee & slippage exactly unchanged BASE and STRESS from A212; cost stress not absent just because buyhold appears positive. Cash benchmark and $100 unhedged spot HOLD same as A212; mark-price at settlement uses genuine 1h open approximation, risk of margin recall and leg fills remains unresolved.
- Binance spot/perp/mark/funding 1h **all genuine monthly ZIP** October through April of each cross-year period: `3 periods × 7 months × 4 symbols × 4 types = 336 ZIP`, plus authentic daily mark repair source if needed, each SHA256. All hour timestamps contiguous. If unavailable = BLOCKED.

## Важнейший порядок решений

A212 "research_economy_gate=True" for ALWAYS **НЕ означает пригодность к живой торговле**, потому что всего одна сделка в год на символ, реальный market order execution и margin risk ещё не валидированы. После A213:
- Честно показать независимо оба сезона по всем годам, оба тарифа, compare cash/spot and fees separately, no cherry-picking.
- Полный исследовательский результат ALWAYS может претендовать на **дальнейший дополнительный осмотр**, если во всех A213 сезонах оба fee-сценария после costs положительны на **как минимум 2/4 монет** без margin breach, и отсутствуют потенциальные отрицательные basis tail events, которые могут уничтожить funding.
- Даже A213 PASS не заменяет подробный margin/liquidation/exchange minimum notional / real spread / conservative multi-leg gap model / 30d live forward PAPER, отдельный пользовательский допуск.
- Если сезон отрицателен, сохранить FAIL и не подбирать threshold на выбранной истории.

Source provenance: сканер funding `Kureshi25/cryptobot:funding_scan.py`, авторская модель не является оригинальным execution engine. И A212, и A213 — явно помеченная independent replay; ни одно «нативное Freqtrade» утверждение здесь недопустимо.

Не изменять existing PAPER schedules, SMOKE, реальные позиции пользователя.
