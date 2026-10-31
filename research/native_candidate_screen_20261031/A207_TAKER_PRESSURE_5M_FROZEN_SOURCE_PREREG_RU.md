# A207 — предварительная регистрация: taker-buy/sell pressure 5m без подгонки

Дата: 2026-10-31; строго RESEARCH/PAPER ONLY. Никаких действий с биржевыми/API ключами, планировщиками, позициями, SMOKE. Не подменять архивный оригинал прибыльным самодельным вариантом.

## Причина выбора
После A197–A205 не найдена комбинация edge+разумный риск+3–5 независимых закрытий/сутки. A205 было 7 завершённых сделок / 141 день на четырёх символах; A206 raw signal-to-fill диагностика выполняется отдельно, результат пока недоступен.

Независимый исходник класса сигналов: `Gotodataru/binance-futures-backtest@5ed0d6e39d8a3e951bea40c66e2638c213012e1b`, `strategy_2_taker_momentum/signals.py` Git blob `b8a2840618c4fb02a2d90120deed5771b34bdbd6`. Long/short по **реальному агрессивному объёму (taker-buy base volume/total base volume)**, 5m, rolling ratio и три подтверждённых бара, ATR volatility filter. Только raw buy-side pressure оригинальных свечей Binance Vision USD-M, НЕ синтетический RSI вместо taker flow.

Честный аудит оригинального `strategy_2_taker_momentum/backtest.py`: авторский код **перебирает sl/tp комбинации и выбирает лучшую по метрике на уже увиденном OOS** (external holdout leakage). В `shared/backtest_engine.py` fees and slippage constants используются глобально и не всегда соответствуют объекту hyperopt; без отдельного независимого replay нельзя принимать рекламируемые walk-forward метрики. Поэтому A207 — **не верификация авторского WFA**, а независимый *fixed rules* frozen experiment с байт-в-байт импортом original `generate_signals` и отдельным строгим исполнителем; при любом отличии назвать это отдельным экспериментом. Не называем «оригинальным native Freqtrade».

## Фиксируем параметры до просмотра Binance PnL
- ma_period=15, confirm_bars=3, threshold_high=0.62, threshold_low=0.38, atr_period=14 (исходные дефолты source), ATR active threshold0.8×MA50. Сигналы long +1/short −1; не заменять.
- hold_bars=16 (max 80m по 5m), **STOP 1.0% движения цены, TP2.0% цены**, исходные value из авторского `PARAM_GRID` (`sl_pct=0.01`, `tp_pct=0.02`). Эта комбинация зафиксирована ДО PnL по здравому risk geometry 1:2; не выбиралась из исторического OOS. Размер $100 nominal на отдельный кошелёк $1000, isolated 1×, одна позиция / монета, нет DCA/маржи.
- **Исторические тестовые периоды**: 2024 May13–Sep30 **первый заранее выбранный контроль** ранее не использованный EMBER, 2025 May13–Sep30 и 2026 May13–Sep30 уже ранее много раз использовались EMBER (не называть их pristine OOS!). Данные Binance Vision monthly May–Sep и April warmup, если доступны 2024–2026. Честно фиксировать источники, SHA zip/CSV, trade SHA, timestamps. Проверить, что 2024 действительно не содержит 2017-2019 «фьючерсных» фальшивых свечей.
- Entry at **next candle open after signal**, not on signal bar. SL/TP with 5m OHLC **SL FIRST** if both touch same bar. Gaps beyond SL on next candle: worse open, not stop fiction. Time expiration: market at *next* open after 16 elapsed bars. Baseline cost fee0.0005 and slippage0.0001 **each side**; stress fee0.00125 and slippage0.0003 each side; no maker non-fill invention. Funding from actual Binance USD-M monthly fundingRate by settlement time, signed LONG pays positive, SHORT earns positive (if negative signs opposite). No future funding used at opening.
- Trading at 1× only for strategy edge test. No 20×/30× extrapolation or approval. Quarterly performance per actual $1000-wallet, no fictional combined portfolio.
- **Research gate** predeclared: ≥2/4 symbols show simultaneously in all three years both cost tiers N≥35, net>0, PF≥1.2, wallet DD<15%, top3 winning trade concentration <60%; each year at least141 trades across 4 separate wallets for BASE and STRESS. **Tempo gate**: ≥3/day across 4 coins in each year, p90 hold ≤24h, <30% next-bar reentries, all-4 slots occupied less than80% of timeline, and no persistent `signal=True` artefact. Both economics and tempo must hold. Overlap 2025/26 has selection history so even PASS requires fresh forward paper.
- Stress fees 0.125% each side may exceed spot current actual; this is conservative scenario, not claim of exact Binance tier. No market microstructure fills beyond modeled OHLC.
- Include **source signal causal-prefix test** on real OHLC 2024 first, 2025 second; if full df alters historical signal prefixes: reject before economics. Note raw buy ratio signals use only historical rolling shift(1), but current ATR is known at *bar close* and next-open entry follows, so causality holds if checked.
- Require raw event-onset count, percent repeated persistence, no instant post-TP reentry. A permanent phase signal which reopens 5m after close is unacceptable even with positive historical PnL.
- Need *point-in-time* data integrity; when mixed Binance raw URL 2024/2025/2026 is absent, BLOCKED, no made-up candles or invented ROI.

## Source code statuses screened first
- `Kureshi25/cryptobot` transparent authors report: 39/68 public freqtrade strategies execute, only3/39 profitable on their dataset; 1m high-freq demo 15949 trades/13d, 67% wins but -97.6% wallet after costs; adaptive daily with +5% WFA ~one trade/18 days; useful **negative baseline not our candidate**.
- `darkvolg/Trading:TrendRiderStrategy_public.py` 1h long-only and stop6% price, despite public paper logs and WFA: not 5m/15m dual side.
- `RamXX/freqtrade-public-bots` 1m `onem_wavecatcher` long only, -99% base stop; TheForceMod_3 5m long-only with questionable MTF merges; `VolatilityCatcher` -99% base / custom 18.9% SL, reject for 20-30×.
- `Gotodataru` original taker-momentum source is selected for different market information; raw signal from ORIGINAL .py, execution **separately reconstructed and clearly labelled**, stress and frozen test. No reinterpretation of author's claimed OOS.

## Auditable result contract
1. Prereg committed BEFORE new workflow/market data.
2. Exact source commit + Git blob, original unchanged .py.
3. Genuine Binance CSV+ZIP SHA, per-year 5m gaps, source taker volume and funding event audit.
4. Machine trade log per year/coin/scenario with entry/exit timestamp, direction, fees, costs, funding, TP/SL/timeout and gaps. Verify sum trade PnL, position nonoverlap and capital exposure. Source Python and engine SHA.
5. Persist JSON results and report to branch only upon real GitHub Actions completion. Technical SUCCESS ≠ economic PASS. Fail-closed on missing history.

No user trade journal edits or signals. No fitting after view.
