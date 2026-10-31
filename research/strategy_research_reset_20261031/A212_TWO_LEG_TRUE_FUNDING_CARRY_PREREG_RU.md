# A212 — prereg ДО PnL: настоящий двухногий spot+perpetual carry на 2024, 2025, 2026

Дата: 2026-10-31. Independent research experiment, not a native Freqtrade strategy, **NO ORDERS/PAPER SCHEDULERS CHANGES**.

## Принципиально иная математическая гипотеза

Вместо предсказания направления цены проверить **дельта-нейтральное получение funding**. Одновременная позиция: LONG spot и SHORT USD-M perpetual **одинаковым количеством монет** на одной бирже; суммарный directional delta близок к нулю, но basis-risk, margin liquidation и execution risk остаются.

Исходная *идея и сканер*, не торговое исполнение: `Kureshi25/cryptobot:funding_scan.py` blob `606081f5e361d2b73fe52ee908be8c691d58498f`; `selectivity_test.py` blob `aa055677a2ae7cbc22d3c2ec1bb7027609dee248`. Авторский selectivity-test не имеет genuine hedged spot/perp trade ledger, поэтому здесь **НОВЫЙ НЕЗАВИСИМЫЙ 1h replay с заранее фиксированными правилами**, а не доказательство авторской доходности. Основной исследовательский контракт `A209_EDGE_FIRST_RESEARCH_CHARTER_RU.md`.

## Исходные и данные

BTC, ETH, SOL, LINK; каждый отделённый USDT wallet =1000; LONG spot qty=100USDT / действительная spot execution price на входе, SHORT perpetual **тот же qty**, perp initial margin условно 300 USDT earmarked (≈3× shorts initial notional), остаётся >500 USDT buffer/cash; 1x без плечевого усиления. История **2024-05-13–2024-09-30, 2025-05-13–2025-09-30, 2026-05-13–2026-09-30**, данные 1h с warmup с 2024/25/26 May1. Каждая выборка 141 day, фактически все годы уже исследовались в EMBER — НЕ pristine OOS.

**Genuine Binance Vision monthly**: spot `/data/spot/monthly/klines/{sym}/1h/`, perpetual `/data/futures/um/monthly/klines/{sym}/1h/`, mark `/data/futures/um/monthly/markPriceKlines/{sym}/1h/`, settled `/data/futures/um/monthly/fundingRate/{sym}/`, May–Sep2024/2025/2026 = **240 genuine ZIP** before source-backed daily gap repairs. Write every URL + ZIP SHA256 + extracted CSV SHA256. Do not substitute spot close for perp and vice versa. Missing genuine source or uncorrected Mark hour → BLOCKED. 1h price/mark continuity, no duplicates, funding accurate on settlement hour.

## Два заранее фиксированных policy варианта, не выбор после теста

- `ALWAYS`: open matched spot+short perp on **May13 00:00 UTC**, hold to **Sep30 23:00 close** (141 days, mark funding at each actual 8h settlement), then close both legs including four-leg fees. One entrance/exit per coin/year, no rebalance. This is a passive basis carry baseline and has very few independent trades, so even if positive => insufficient evidence pending longer forward.
- `SELECTIVE`: hour-level signal uses **9 last already settled funding rates**; select entry if their arithmetic mean > **0.0001** (1bp/funding payment); exit when mean <= 0.0001. Signal only after funding payment known; trading at **next 1h bar open**; no partial hindsight on current funding, no free instant switch within unsettled event. Fixed threshold from conventional previous 9 funding intervals; no grid search. On each new entry, simultaneously buy 100 USDT spot notional and SHORT exactly same qty perpetual. If signal remains on, do NOT re-enter. On turn-off exit, close both, account PnL after expenses, refuse to open if wallet insufficient to reserve 300 USDT perp margin plus spot purchase. Max one pair per independent wallet.
- All market orders (no fantasy maker queue); two costs:
  - BASE spot fee0.0010/side, perp fee0.0005/side, price slippage0.0001 **on each of four fills**.
  - STRESS spot fee0.0015/side, perp fee0.00125/side, price slippage0.0003 on each of four fills.
  - Perp short pays funding when rate negative and collects when positive, determined by exchange actual settlement; amount measured using **genuine mark price** × open qty, not constant $100 if price changed.
- On settlement timestamp t, if position exists BEFORE t, apply funding then allow policy to update at next hour. New positions never receive previously settled funding. Liquidation warning if *perp collateral mark-to-market* remaining < maintenance margin allowance 0.5% of perp notional, including fees; no automatic cross-collateral rescue. If potentially liquidated -> **risk gate FAIL** even when gross hedge PnL positive; simulated forced exit at next hour is NOT a perfect historical liquidation model.
- Validate two legs exactly matching qty, entry/exit timestamps and sign, each settlement inside open interval; 48 strategy×year×coin×cost cells (2 modes×3 years×4 coins×2 fee levels), underlying 4 wallet model, all SHA receipts. Portfolio equity at least 1h marked-to-market of spot+perp+funding and **entry fees** at minimum, not only realized losses. Initial $1000 wallet per symbol, initial $4000 total of four partitioned independent wallets. Compare cash 0% and spot-only matched $100 buying held over same period, **not funding-only return**.

## Decision logic

- Economy: overall 4 partitioned wallets, worst individual cell and years, net real basis+funding-fees-slippage, max 1h marked-to-market drawdown, number hedges and actual collateral minimum.
- No mandatory number trades/day. But one successful single full-period hold is **insufficient** proof of long-term stable edge. Requirement for further study: both years and other regimes, positive after STRESS for at least 2/4 coins each time, no collateral breaches; otherwise RESEARCH_NEGATIVE.
- Carry cannot be called riskless or market-neutral in a complete sense: basis divergence and liquidation of short leg can happen before hedge offsets spot. No actual live execution, still possible venue/default/withdrawal risk.
- Any missing source or ambiguity in actual Binance settlement = BLOCKED, do not invent funding.

## Future/OOS and permissions

These three historical windows are used in prior EMBER; no guarantee of genuine unseen OOS. Only after independent forward PAPER and execution quality checks can the system be considered for use. Existing SMOKE, live positions, Google Drive trade logs, and scheduled PAPER monitoring remain untouched.
