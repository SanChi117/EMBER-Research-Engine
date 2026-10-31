# A212 + A213 — закрытие исследовательской проверки двухногого funding carry: доход есть, ГЕЙТ РИСКА FAIL

Дата: 2026-10-31. Исходная гипотеза была заморожена ДО PnL; неподвижные условия обоих тестов: spot LONG + USD-M perp SHORT matched exact coin quantity, 100 USDT spot per 1000 USDT segregated wallet, 3× short collateral reserve; BASE fee spot0.10%/perp0.05% per side +0.01% slippage, STRESS 0.15%/0.125% plus0.03% slippage; two modes ALWAYS and SELECTIVE trailing9 funding >0.0001; actual 1h spot/perp/mark/funding sources SHA from Binance Vision.

## 1. Первая проверка A212: May13-Sep30 2024/2025/2026

`research/a212-spot-perp-delta-neutral-funding-2024-2026-20261031`, GitHub Actions run **41206356977** SUCCESS: >=240 authentic monthly ZIP receipts incl mark daily repairs, 48 independently reopened real two-leg ledgers.

| Period | ALWAYS BASE, 4×1000 segregated wallets | ALWAYS STRESS | SELECTIVE BASE | SELECTIVE STRESS |
|---|---:|---:|---:|---:|
| 2024 May–Sep | +$9.207061 | +$7.909777 | −$0.138902 | −$2.425918 |
| 2025 May–Sep | +$8.410715 | +$6.885166 | −$0.482041 | −$1.126148 |
| 2026 May–Sep | +$4.326458 | +$2.863198 | $0, 0 сделок | $0, 0 сделок |

Итого в A212 получился реальный в модели положительный чистый денежный net с учётом changes basis/spot/perp/funding, но max one hedge/coin/season и **слишком малая абсолютная доходность** относительно $4000 полной segregated collateral модели. Даже A212 verdict `research_economy_gate:true` означает лишь положительные числа по базовому финансовому screening, не статистическую доказательность или execution readiness.

## 2. Незафиксированный ретюнинг запрещён: independent A213 Oct-Apr, правила НЕ менялись

`research/a213-two-leg-carry-offseason-heldout-20261031`, GitHub Actions run [41206676927](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41206676927) **SUCCESS**; 336 genuine monthly source ZIP and 48 additional ledgers, 2 fee cases, cross-year windows:

| Period | ALWAYS BASE | ALWAYS STRESS | SELECTIVE BASE | SELECTIVE STRESS |
|---|---:|---:|---:|---:|
| 2023 Oct – 2024 Apr | +$120.447199 | +$117.852532 | +$29.865890 | +$22.389281 |
| 2024 Oct – 2025 Apr | +$23.121653 | +$21.740053 | +$6.275283 | +$3.333374 |
| 2025 Oct – 2026 Apr | +$1.218781 | +$0.222570 | $0 / no trades | $0 / no trades |

**2023/24 SOL collateral risk breach** under original 3× collateral reserve. Spot profit mathematically offsets short quote price, но perpetual isolated margin can be exhausted **before** long spot is liquidated/transferred. In source replay lowest `perp short collateral / perpetual current notional` for SOL = **−0.544478**; conservative maintenance threshold +0.015. This means theoretical +$63.13683 modeled SOL net from ALWAYS seasonal replay **is NOT execution-feasible without a completely new collateral management mechanism**. Funding +$64.024753 on SOL is high, but not an executable free gain.

`2025-10–2026-04` 3/4 coins positive, SOL `−$1.533763` BASE/ `−$1.76403` STRESS, total ALWAYS BASE just **$1.22** over ~212 days on 4000 segregated USDT; STRESS **$0.22**. Not a substantial autonomous return for risks of two live legs and blocked collateral.

In both windows SELECTIVE had no stable positive behavior; positive 2023/24 due 2023-24 funding regime, 2024/25 small, 2025/26 none, no selection curve fitting permitted.

## 3. Сводный причинный вывод

1. Hypothesis **positive funding may generate positive carry after four-leg fees when spot-perp basis is hedged** is supported *in the modeled historical setting*, **not proven as robust autonomous executable edge**.
2. Higher funding periods coincide with explosive underlying price moves (2023 SOL), which can liquidate isolated short despite net hedge. Thus highest paper profits can be precisely the least execution-safe. Spot+perp requires automatic margin adjustment, cross-margin exposure, crash/failure recovery, exchange collateral limits; these have not been engineered or validated.
3. Fee and funding model is genuine Binance Vision, but fund payment mark 1h open approximates subsecond settlement and bid/ask/nonfill/counterparty risk are not captured. Both A212 and A213 mark-to-market **per individual 1h wallet**, NOT full multiwallet portfolio correlated DD.
4. At today's nominal model size $100 per coin, latest seven-month seasonal net is only ~0.03% of $4000 capital BASE (0.0056% STRESS), so even modest collateral opportunity costs could eclipse it; avoid claiming annualized risk-free yield or guaranteed return.
5. 2023/24 risk gate failed, A213 `research_economy_gate:false` both variants. **No forward PAPER approval**. Do not select 2023/24 positive $120 and exclude SOL after observing its historic loss of coverage; that would be post-hoc selection.
6. Keep code/data reusable for future carry ideas and margin-risk research, but move primary independent search to another hypothesis, ideally unlevered long-only spot allocation / systematic diversification, with verified buyhold cash controls.

## Verdict
A212 positive modeled economy in May-Sep but A213 FULL CHECK **FAIL due to 2023/24 SOL collateral risk and 2025/26 yield deterioration.** This is a *credible mechanism* but not a deployable system. Existing SMOKE/PAPER, user positions and schedulers unchanged.
