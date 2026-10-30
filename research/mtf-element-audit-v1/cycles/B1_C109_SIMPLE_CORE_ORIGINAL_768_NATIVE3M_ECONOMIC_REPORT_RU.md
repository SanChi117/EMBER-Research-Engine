# C109 — Простое цельное крипто-правило: реальные 768 ZIP, 55 сделок, улучшение БЕЗ доказанной устойчивости
2026-10-30, PAPER ONLY. Root cause C107: incomplete formation semantics. C108 strict 4H→1H child route n2 -2.176R. User demanded stop adding complexity and deliver a working research mechanism.

## Замороженный эксперимент ДО котировок
Precommit `cycles/B1_C109_PRECOMMIT_SINGLE_P4_CORE_VS_FROZEN_BASELINE_RU.md`. 12 заранее зафиксированных Binance USD-M crypto `BNB,XLM,HBAR,INJ,OP,ALGO,CHZ,ICP,SEI,PENDLE,LINK,UNI` USDT, 2026-05-01 00:00 UTC to 2026-07-04 00:00 UTC end exclusive, **64 full days** each symbol: 12 × 64 = **768 original Binance Vision daily 3m ZIP** same-host provider `.CHECKSUM`, every ZIP SHA256 & CSV SHA256, exactly 12×64×480=**368640 original native3m bars**. 7 complete calendar days context warmup, 48h end-right-censor embargo; C109 not tuned after file read. Earlier dates: no overlap with C108 Aug-Sep 2026 or C105/C106 Sept-Oct 2026; this is HISTORICAL earlier time, not prospective post-deployment OOS. All orders/fills/live trades `[]`.

### Locked arms, same source and cost assumptions
**B0 original baseline**: Existing untouched C105 formation predicates (4H FVG 3 closed 4H with old as-of D1/W1 filter; first closed 15m physical H4 touch; 1H bullish/bearish H4 gap midpoint rejection; 15m closed 3bar FVG OR previous 15m candle high/low close cross "SNR proxy"; next genuine 3m open). Replayed with extended 64d original source in C109 event loop because frozen C105 research harness expects exactly 32d.
**B1 simple CORE**: Same parent/first test D1/W1, but H1 reaction closes **BEYOND full 4H FVG near edge** in side direction while H1 physically intersected that gap, not merely beyond center of gap. After completed H1 confirmation, 15m VC must be **a genuine 3bar completed FVG** or closing across **a genuine 2-left/2-right 15m confirmed swing**, known BEFORE the breaker candle started; strictly disallows "close > previous single 15m high" as pseudo-BOS. No external LuxAlgo BOS/OB/EQH etc. All event clocks as-of. Structural signal is an explicitly C109 independent adaptation, not author-verified golden.
**Both:** SL 4H parent original far FVG edge ±0.15 ATR14 of 4H, target nearest original confirmed 4H pivot unswept by 3m ±0.15 ATR4H; unmodified `c105_parent4h_structural_geometry.parent_plan` source SHA, derived RR≥1.25 gate not fixed target, native3m hard stop first, 48h max hold, roundtrip modeled costs 14/25/40bps, modeling 1% risk per trade DD. Different trade timings on same 4H POI can yield different outcomes, so not necessarily paired identical trades.

## Original historical results in same exact period
| 64d × 12 crypto | B0 old C105-style | B1 simple CORE |
|---|---:|---:|
| Historical actual virtual trades | 54 | **55** |
| 25bps netR | **−0.546001R** | **+10.749521R** |
| 25bps PF | 0.98561 | **1.30903** |
| 25bps max modeled 1%/risk DD | 11.96448% | **10.51646%** |
| 25bps winrate | 38.889% | **41.818%** |
| 14bps netR | +3.671171R | **+14.464380R** |
| 40bps netR | −6.296692R | **+5.683805R** |
| 40bps PF | 0.84956 | **1.15166** |
| 25bps early 2026-05-01..June1 | n27 **−8.255844R** PF0.61493 | n26 **−4.559101R** PF0.76909 |
| 25bps late June2..July3 | n27 +7.709843R PF1.46694 | n29 **+15.308622R** PF2.01786 |

B1 source stage count: 196 4H FVG parents → 163 physical first tests → 107 H1 full exits/reclaims → 104 closed 15m VC events (79 confirmed-swing closes, 25 3bar IMB) → 55 full 4H risk-valid native3m paper trades (40 swing break,15 IMB). Exits n55: 30 native3m STOP_FIRST_SAME_3M, 16 4H FTA TP, 9 timeout 48h. B0: 196 parents→163 first touches→111 weak H1 reactions→104 weak/IMB 15m VC→54 trades; exits31 SL14 TP9 timeout.

**Exact admission verdict:** B0 **FAILED** nonpositive R25, PF25<=1.2, PF40<=1.1, DD25>=10%. B1 **FAILED** only **DD25=10.51646%** at 1% risk/trade against PREDECLARED <10% threshold. The n55 and 25bps/40bps PF thresholds and positive R passed, but **that is NOT a license to retroactively change the drawdown threshold or risk sizing to pronounce PASS**. In addition, B1 early regime n26 negative -4.559101R; late n29 positive. Robust performance remains uncertain: period-specific regime effect, costs, structural 4H SL wick vs 4H close, source-native3m not tick market impact. Do not claim "guaranteed gains". Any lower risk budget has to be a distinct precommitted capital control test; no hindsight trade selection on these 55.

## Evidence & CI
- `d05/c109_simple_p4_core_vs_original_research.py`: original provider ZIP+checksum and two-arm causal event logic; no live order transport.
- `d05/test_c109_simple_p4_complete_reclaim_real_bos.py`: 24 counterchecks including future swing embargo, H1 midpoint vs full zone, actual prior single candle not BOS, physical stop and H4-only FTA source.
- [C109 first CI 40984722421](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40984722421) red only because negative unittest call missed last empty swings argument, **test fixture corrected BEFORE real price source load**, not strategy source change.
- [C109 final price CI 40984772427](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40984772427) **4/4 SUCCESS**, 24 new +735 prior tests ×Python 3.10/3.11/3.12 = **2277/2277 PASS**; actual 768 source archives checksum+CSV SHA complete and original next native3m trade provenance.
- `evidence/c109/C109_CORE_VS_ORIGINAL_768_3M_PROVIDER_ZIPS.json` **737881 bytes, SHA256 `d8e4a39b5de6176227cd5e8fd6103278d6e032335341f8f098f930bdad305134`**. Contains every original provider zip SHA/CSV SHA, two full trading arms, all 55 B1/54 B0 paper trade attributes and 4H SL/TP source chain; all source originals unchanged.

## Next step, no after-the-fact tuning
Keep C109 single simple B1 frozen. Perform second time-domain **untouched period** (different months/regime) with identical thresholds and original source on 12 preregistered symbols; source date window and admissibility gates frozen BEFORE price download. If B1 fails independent OOS, no live. C109 positive R on one historical interval despite original D1/W1 primitive semantics is not a completed proof of a stable 40–60day profit machine.
