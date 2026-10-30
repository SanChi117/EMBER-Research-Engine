# C116 / A179 — оригинальная 1M-лента, единые 3M/5M, NO_POWER и отрицательная экономика

**Дата: 30 октября 2026 UTC. PAPER ONLY / LIVE BLOCKED.**

Предварительная регистрация: B1_C116_PRECOMMIT_SINGLE_ORIGINAL_1M_CANONICAL_SOURCE_RU.md.
Предыдущие источниковые негативные свидетельства: C114 A177 SOURCE_BLOCKED (Binance native3m/native5m volume расходится на 22.02%); C115 A178 SOURCE_BLOCKED (XLM 15m LOW 0.39478 против 0.39467). Оба сохранены, не заменены.

## Какая гипотеза реально проверена

**Не C109 и не изменение старой стратегии.** Другое независимое семейство C114: подтвержденная 5m 2L2R CHoCH после первого касания настоящей 4H FVG против касания без CHoCH, тот же шестичасовой LANDMARK, 4H-zone physical stop 0.15 ATR4H buffer, 4H preconfirmed unswept FTA target, held 48h, stop-first derived3m wick, 14/25/40bps modeled roundtrip. Обеим группам одинаковые времена и геометрия. Сопоставление без замены условий: symbol+month+side+preconfirmed 4H premium/discount + risk/RR strata. Сид бустрапа 11420261030, 2000 block-bootstrap replicates.

Единственное архитектурное изменение C116: **1344 оригинальных native1m daily Binance ZIP**, оригинальные 1m SHA/CHECKSUM, 1,935,360 физически исходных 1m свечей, из которых построено 645,120 3m и 387,072 5m по UTC границам. **Производные 3m/5m НЕ являются двумя независимыми оригинальными архивами.** На общей 15m сетке 3m+5m имеют строго одинаковые open/high/low/close/volume, потому что они агрегируются из одной минутной истории. Нельзя сравнивать это с C114 как точно идентичный источник; это отдельный canonical-source тест. Все входы и параметры экономической модели C114 сохранены.

## Источники и CI

WIN_A: 2025-01-01..2025-02-26 exclusive; WIN_B: 2026-02-01..2026-03-29 exclusive.
12 фиксированных Binance USD-M символов BNBUSDT, XLMUSDT, HBARUSDT, INJUSDT, OPUSDT, ALGOUSDT, CHZUSDT, ICPUSDT, SEIUSDT, PENDLEUSDT, LINKUSDT, UNIUSDT.
672 original1m SHA ZIP/window. Full 2 windows = 1344 original1m ZIP and all derived3m/5m 15m OHLCV parity.
Python 3.10/3.11/3.12: 11 C116 source/provenance/metadata adversarial tests each + C114 23 adversarial tests and C105/C113 regression tests — SUCCESS.
Final github CI: https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41111144046 — four jobs SUCCESS, deterministic JSON receipts, checksum SHA manifest. Earlier intermediary runner showed missing trade 'symbol' metadata and a non-fast-forward evidence push after newer branch commits; fixed **only trade identity** in C116 scoped wrapper. Tested that Entry/SL/TP/netR never change due to metadata. No post-outcome price/geometric threshold changed.

GitHub original-file receipts:
- evidence/c116/C116_SUMMARY.json
- evidence/c116/C116_WIN_A_ORIGINAL_1M_CANONICAL_AND_MATCHED_EVENTS.json
- evidence/c116/C116_WIN_B_ORIGINAL_1M_CANONICAL_AND_MATCHED_EVENTS.json

## Результат 25bps

| Показатель | WIN_A 2025 Jan-Feb | WIN_B 2026 Feb-Mar |
|---|---:|---:|
| Исходных 4H POI first touch, после допусков | 555 | 483 |
| 5m confirmed CHoCH treatment | 127 | 104 |
| Контроль без CHoCH | 428 | 379 |
| Treatment: геометрически допущенных виртуальных исполнений | 36 | 24 |
| Treatment 25bps gross of independent-risk sums netR | **−12.699636R** | **−7.157520R** |
| Treatment PF25 | **0.531206** | **0.618505** |
| Control: виртуальных исполнений | 99 | 85 |
| Control 25bps netR | −25.119183R | −20.114709R |
| Сопоставимых treatment/control пар | **2** | **5** |
| Необходимое число пар | 40 | 40 |
| Matched treatment netR25 | −0.145061R | −1.969039R |
| Matched control netR25 | −2.256007R | −5.952540R |
| Bootstrap 95% LOWER for mean paired T−C R | −0.026528 | −0.018518 |
| T filled TP-before-SL | 7/36 (19.44%) | 5/24 (20.83%) |
| Conserv. portfolio adverse-wick DD (1% starting capital risk/fill) | 15.077779% | 10.432321% |
| C114 economic prereg state | **NO_POWER** | **NO_POWER** |

Уже достаточная **несопоставленная treatment-когорта** показывает отрицательные 25bps netR и PF<1. matched разница T−C положительная **только на 2/5 парах** и 95% LOWER в обоих периодах отрицательная. Поэтому **нельзя заявлять, что CHoCH повышает вероятность движения к следующей 4H зоне**. Клинически и статистически это незрелая гипотеза, не торговый сигнал. Результат NO_POWER не оправдывает снижение минимального n=40 до 2 или 5. Нельзя ретроспективно менять risk bin/holding period/POI/CHoCH pivot width.

### Ограничения

- Исторические windows источниково экспонированы при проверке C114/C115. Экономические результаты тогда не были рассчитаны, но это НЕ полноценное prospective forward OOS.
- Данные подтверждают Binance original1m, а derived3m/5m — согласованное математическое разбиение; они могут отличаться от оригинальных независимых Binance 3m/5m архивов, как показывает C115.
- В протоколе matched sample extremely small, clinical inference or causal impact from observational CHoCH не подтверждены.
- 25bps costs are a model, funding/queue/market impact/latency absent. Portfolio DD is a conservative static-capital approximation with concurrency; not a verified exchange equity curve.
- Программный SL/TP построен из известных в момент entry 4H, не из 5m/3m. Fixed RR TP и live orders отсутствуют.
- Большинство кандидатов не допускается к торговле; early competing events (T 58/51; control 281/237) сохранены в ITT denominator. Matched-only wins are NOT a substitute for the failing full treatment cohort.
- Positive matched T−C vs even worse C on 7 pairs is NOT actionable.

## Терминальный вердикт

**C116 = NO_POWER + unfavourable observed economics.** Claim of CHoCH edge NOT VALIDATED. C109 family archived since C113. C114/C115 source-blocked preserved. All runs PAPER ONLY / NO LIVE.

Не оптимизировать параметры текущей реакции на раскрытых выборках. Для действительно новой исследовательской семьи сначала выяснить независимую 4H trading-range/target structure, сменить заранее зарегистрированные невиданные даты/проспективный PAPER и сравнивать не только PF, но и matched controls с достаточным количеством случаев. Не выдавать NO_POWER за PASS или за доказанную универсальную неработоспособность zone-to-zone.
