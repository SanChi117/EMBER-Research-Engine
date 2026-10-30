# C111: самостоятельный 1D+4H фильтр режима — НЕ СРАБОТАЛ НА ДВУХ НОВЫХ ИСТОРИЧЕСКИХ ОКНАХ
Дата 2026-10-30. ONLY PAPER. **ENGINEERING PASS / ECONOMIC FAIL / DO NOT INTEGRATE GATE.** Пользователь согласился проверить gate после C110: C109 без фильтра давал +10.749521R на май–июль 2026, но на ноябрь 2025–январь 2026 −9.695331R при 25bps и реальном формате 4H SL/TP. Цель: устранить зависимость от режима БЕЗ усложнения входа и подгонки стопов.

## Что именно проверено, а не пообещано
Замороженный ДО получения котировок документ `cycles/B1_C111_PRECOMMIT_SINGLE_REGIME_GATE_TWO_UNSEEN_CRYPTO_WINDOWS_RU.md`:
- **C109 trading-code byte identical** SHA256 `39bf28a44cec0356b256853514c532b8f37be48f3da3477a365bd19c4add5557`. Оригинальный 4H FVG POI → first15m touch → full closed1H reclaim → closed15m genuine preconfirmed pivot BOS or 3bar IMB → next original3m OPEN. 4H-only SL far FVG edge±0.15 ATR4H, 4H-only TP nearest confirmed unswept pivot±0.15ATR4H, derived RR>=1.25, max hold48h, fees14/25/40bps; hard stop kept executable on 3m, no SL widening. **Ни один из этих элементов НЕ изменён.**
- Единственный C111 candidate trade-admission gate ДО 15m подтверждения, в момент полностью закрытой 1H реакции: 4H close six H4 steps directional sign matches intended side; fully closed 1D close three D1 steps same sign; 4H price path efficiency=abs(6-step net close move)/sum(abs(each of six consecutive closes differences))>=**1/3**. Missing or zero=fail closed. No external future bars; every source bar known no later than full H1 reaction close. One set of thresholds frozen before raw data; no side/time selection.
- Run unchanged C109 B1 as **control** and C111 B2 as **gated** through full original C109 state machine **SEPARATELY** on same original source; not post-hoc filtering exited losers. Each strategy has its own zone state, concurrent busy state, fills, stop/TP. No copied LuxAlgo indicators.

## ДВА НОВЫХ ИСТОРИЧЕСКИХ ОКНА, НЕ РАНЕЕ ИСПОЛЬЗОВАННЫЕ В C105–C110
- **WIN_A** 2025-03-01 to 2025-05-04 UTC exclusive, 64 full days.
- **WIN_B** 2025-07-01 to 2025-09-03 UTC exclusive, 64 full days.
- Same prereg 12 Binance USD-M coins BNB XLM HBAR INJ OP ALGO CHZ ICP SEI PENDLE LINK UNI /USDT: two×12×64 = **1536 original Binance Vision daily 3m ZIP**, each original provider .CHECKSUM, ZIP SHA & CSV SHA; **737280 original genuine 3m candles**. No third party substitute, no source continuity holes. 7day warmup,48h end embargo, fixed time-fold halfway each window. Historical (not future prospective OOS). No orders; PAPER trades are simulated.
- Genuine source original zip manifest per window SHA pinned:
  - `evidence/c111/C111_WIN_A_768_ORIGINAL_NATIVE3M_SOURCE_AND_TRADES.json`, **614380 bytes SHA256 `87e9eec8482a4749ecc1d73758968c1f3446d5a6917918d1595ebb3c53a60a73`**.
  - `evidence/c111/C111_WIN_B_768_ORIGINAL_NATIVE3M_SOURCE_AND_TRADES.json`, **600587 bytes SHA256 `47946bc53d23884a19bf3c6bb5734236c0c9d929f8fb4d2dfc1894fb28dd74c1`**.
  - `evidence/c111/C111_REGIME_GATE_TWO_WINDOW_PINNED_SUMMARY.json`, **7289 bytes SHA256 `3a42ddded2b65ecc47dd4b6e89405d4538745d81a547d9c571244c7e4a4cd9f0`** (two previous file SHA and costs, complete author-visible admission verdict).

## Результат двух честных контролируемых окон
| Окно | Арм | N | 25bps NetR | PF25 | PF40 | DD25 при1% риска | timefold early/late R25 |
|---|---|---:|---:|---:|---:|---:|---|
| Март–май2025 | B1 original core no gate |55|**−20.008366R**|0.55804|0.48018|24.88168%|−14.377216R / −5.631150R|
| Март–май2025 | B2 with 1D+4H gate |17|**−6.642906R**|0.52556|0.42670|10.08710%|−4.236619R / −2.406287R|
| Июль–сентябрь2025 | B1 no gate |49|**−7.617704R**|0.81358|0.70267|15.11299%|+6.565196R / −14.182900R|
| Июль–сентябрь2025 | B2 with 1D+4H gate |19|**−13.995634R**|0.27572|0.23231|13.37617%|−5.168964R / −8.826670R|

**Strict prereg gate FAIL in BOTH**. B2 WIN_A n17<30, early fold n5<10, negative netR25, PF25<1.2, PF40<1.1, DD25>10%. B2 WIN_B n19<30, early fold n8<10, negative R25, PF25<1.2, PF40<1.1, DD25>10%. No cherry-pick which window. Summed exploratory B2 n36 netR25 **−20.63854R PF25 0.38069**, netR40 **−25.425075R**; B1 n104 netR25 −27.62607R but lower trade count means no direct capital-performance equality; these are NOT true portfolio returns and omit concurrent gross exposure across different pairs.

Gate selection facts: 4H/H1 true price reclaims deemed admissible **57** in WIN_A, **45** in WIN_B; downstream completed 15m VC events 55/45 and eventual eligible paper entries only 17/19. Rejections at H1 initial gate WIN_A: conflicting D1 22, conflicting H4 32, choppy H4 49; WIN_B conflicting D1 49, conflicting H4 30, choppy H4 27. Strict align signal reduction alone **did NOT improve win quality**. In WIN_B, PF fell from 0.81358 to 0.27572, so this is an economic failure, not merely an insufficient sample.

## Технические гарантии, ограничения и вердикт
- New `d05/c111_frozen_c109_1d4h_regime_gate.py`, scoped C109 original immutable source and native3m historical H4/D1 closes as-of at confirmed 1H reaction. For each symbol BOTH complete event-machine PAPER replays run independently; no post-exit filtering of winning/losing observed trades.
- `d05/test_c111_one_regime_gate_source_asof.py`: 20 new adversarial tests; 769 previous tests ×3 interpreters Python3.10/3.11/3.12 = **2367 PASS**. [CI run 41031495139](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41031495139) **SUCCESS 4/4**, all 1536 original checksum ZIP and 737280 native3m. First red CI 41031395939 due ONLY to Python test method identifier with spaces; corrected BEFORE source-price downloads; no changes to C109 or gate parameters based on market outcomes.
- **No algorithm or market parameter changes after precommit**. Only fixes before raw source were syntactic test identifier, synthetic fixture timing, JS JSON newline serialization and source-freshness guard strictly enforcing historical as-of availability.
- `owner course and C109` still do not guarantee alpha. Technical correctness of a causal system does not imply profitable edge. Extra 1D and 4H momentum classifier failed on both prior-unseen calendar windows. Do not integrate B2 into any trading terminal, automation or real futures executor. Retain as failed immutable PAPER research. All open prior engines preserved for audit; **LIVE BLOCKED**.
- Recommended next actual decision: **stop shipping variations of the C105/C109 FVG parent** as "potentially working" with more guessed gates. Need a new independent, falsifiable trade hypothesis that demonstrates profit in multiple blind regimes, or NO_TRADE. No increased leverage, moving SL, fee ignoring or reclassifying this result. If changing core setup later, prereg on fresh data and compare held-out market segments; never reuse these 2025 regimes to tune threshold 1/3.
