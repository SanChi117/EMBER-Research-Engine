# Prior evidence reviewed for A217
Locked mandate supersedes old scalp-frequency/leverage gates; negative economics retained.

## origin/research/a188-doublema-causal-audit-20261031 / research/doublema_native_oos_20261031/03_A188_CAUSAL_TIME_BOUNDARY_AUDIT_RU.md
* Исходный Freqtrade `2026.4`; ранее в A187 получены 27 сделок (5 bps/side), прибыль +39.864%, PF2.239, DD7.332%; эти показатели **только воспроизводимы, не доказана причинная корректность**.
* Целевой повтор — **оригинальный Freqtrade 2026.4**, одинаковые 1h/4h/1d mark/funding Binance, OOS [2026-05-13,2026-10-30) UTC, базовая комиссия 0,05% за сторону и дополнительная 0,125% за сторону. Исходник и исправленная копия хранятся отдельно. Сравнить все сделки, exit reasons, net PnL, PF, DD.
* Freqtrade `lookahead-analysis` + `recursive-analysis` требуются как дополнительное доказательство, но нельзя автоматически считать их чистый результат отрицанием дефекта именно в callbacks. При спорных индикаторах/условиях — отдельный журнал.

## origin/research/a188-doublema-causal-audit-20261031 / research/doublema_native_oos_20261031/04_A188_NATIVE_CAUSAL_RESULT_RU.md

## origin/research/a194-three-mechanics-preregistered-oos-20261031 / research/backup_candidates_20261031/A194_FINAL_TRIAGE_RESULTS_RU.md
| Стратегия | Сделки BASE (BTC+ETH+SOL) | BASE доходность / 3 счета | BASE PF | STRESS сделки | STRESS доходность | STRESS PF | Вердикт |
| A: 15m trend pullback | 191 | **−17.8345%** | 0.5891 | 195 | **−35.2859%** | 0.3184 | REJECT |
| B: breakout + retest | 72 | **−3.2512%** | 0.7951 | 73 | **−11.4424%** | 0.4344 | REJECT; nearest of the three |
| C: 15m liquidity sweep | 310 | **−17.2881%** | 0.7321 | 331 | **−47.2085%** | 0.3731 | REJECT |
| Стратегия | BTC (N; %; PF) | ETH (N; %; PF) | SOL (N; %; PF) |
**B стресс по монетам:** BTC 19 trades −9.3688% PF0.4316; ETH 26 trades −22.1712% PF0.1684; SOL 28 trades −2.7872% PF0.8411. **Zero** positive pairs. Материалов недостаточно для утверждения, что это долгосрочное универсальное свойство всех пробоев/ретестов; данная реализация отвергнута.
2. B дал 2 положительные пары из 3 при BASE, но общий PnL отрицателен и при реальном stress **все пары отрицательны**. Это не «доказанная стратегия» и не основание оптимизировать TP/SL на тех же 61 днях, иначе будет data mining.
**Вердикт A194:** `THREE_PREREGISTERED_MECHANICS_REJECTED`; `NO_READY_SMALL_BANKROLL_SCALPING_EDGE`; `STOP_GENERIC_PUBLIC_GITHUB_STRATEGY_SEARCH`. Мы не доказали невозможность кратного роста маленького депозита, но **пока нет свидетельств управляемого положительного ожидания**, чтобы безопасно ускорять его плечом и частотой входов.

## origin/research/a195-doublema-original-crosspair-native-20261031 / research/doublema_native_oos_20261031/A195_CROSSPAIR_NATIVE_RESULTS_RU.md
| Монета | Сделки при 5bps/сторону | 5bps net% | 5bps PF | Native кошельковая maxDD | 12.5bps net% | 12.5bps PF | 12.5bps maxDD |
- ETH **104.24%** — без топ-3 суммарный итог стал бы отрицательным (модельная контрольная арифметика, не новый бэктест).
- SOL **183.50%** — без топ-3 итог явно отрицателен.
- BTC отрицателен целиком.
Другой prereg критерий top3 как доля **всех прибыльных сделок** (5bps): BTC 79.51%, ETH 58.19%, SOL **64.87%**, LINK **65.20%**. Предустановленный порог <60% по двум новым прибыльным парам SOL и LINK нарушен. LINK + SOL **НЕ ПРОХОДЯТ** заранее согласованный gate, несмотря на привлекательную доходность. BTC не проходит из-за убытка, числа входов <20, DD и PF. По 12.5bps для SOL top3 доля выигрышных сделок 66.66%, LINK 66.42%; порог снова провален.
Старый независимый A187 ETH использовал **другой, более длинный период** [2026-05-13,2026-10-30), другой статический **OKX** futures adapter. 27 ETH сделок/ +39.864% / PF2.239 / DD7.332% являются отдельным доказательством повторяемости, но **нельзя называть их равными** новому ETH 23 trades +34.8285% / PF2.264 на период до Oct1 и Binance adapter. Октябрьский месячный ZIP отсутствует в data.binance.vision на дату 2026-10-31. Границу изменили до вычисления сигналов, документально зафиксировано.
**Вердикт `NATIVE_STRATEGY_PARITY_ENGINE_PASS_CROSS_PAIR_WINNERS_3_OF_4`, `ECONOMIC_ROBUSTNESS_FAIL_TO_ADVANCE`, `NO_LIVE`, `NO_AUTO_PAPER`.**

## origin/research/a196-doublema-execution-causality-20261031 / research/doublema_native_oos_20261031/A196_CAUSALITY_AND_EXECUTION_RESULTS_RU.md
| Pair | Старый 1h native, N / Net% / PF / DD% | Новый 5m detail native, N / Net% / PF / DD% | Общие входы с изменившимся выходом |
| Pair | Старый 1h native, N / Net% / PF / DD% | Новый 5m detail native, N / Net% / PF / DD% | Общие входы с изменившимся выходом |
**Пререгистрированные критерии:** требовалось не менее двух из ETH/SOL/LINK с 20+ 5m trades, PF>=1.25, положительной net при 2 комиссиях, DD<15%, сохранение не менее70% доходности от своего 1h аналога при той же комиссии, доля top3 выигрышных сделок в общем gross profit **меньше60%**. Результат машинной проверки `ETH=false`, `SOL=true`, `LINK=false`. **Итоговый gate FAIL: только 1 из 3, требовалось хотя бы 2.** Положительный Net на ETH/LINK недостаточен для признания устойчивым быстрым заработком. Даже условно прошедший SOL требует новый период и более реалистичную модель затрат, прежде чем можно будет принимать PAPER-сигналы.
**Вердикт:** `NATIVE_5M_EXECUTION_SOURCE_REPRODUCED`; `SIGNAL_PREFIX_40_OF_40_CAUSALITY_NO_MISMATCH`; `ECONOMIC_CROSS_PAIR_ADVANCE_GATE_FAIL_1_OF_3`; `NO_LIVE`; `NO_AUTO_PAPER`.
**Double MA оставляем только в статусе исследовательского источника**: частота по четырём парам недостаточна для заявленной цели, более реалистичные свечи заметно меняют исходный выигрыш, экономический gate не пройден. Текущую 1h стратегию **не ускорять автоматически до 15m, не склеивать с EMBER, не подбирать SL/TP** на уже просмотренном отрезке. Если продолжаем, то обязательные новые нетронутые окна и полный официальный lookahead/recursive audit плюс 1m/real spread, отдельное снижение риска по всему депозиту.

## origin/research/a197-doublema-regime-and-bias-20261031 / research/doublema_native_oos_20261031/A197_BIAS_AND_2025_RESULTS_RU.md
**Честный итог QA:** `OFFICIAL_LOOKAHEAD_NO_BIAS_DETECTED_20_SIGNALS`; `RECURSIVE_STARTUP_HISTORY_SENSITIVITY_DETECTED`. Не заявлять, что входы гарантированно causal на всех свечах, что callbacks чисты, или что при старте недостаточной историей сигналы полностью воспроизводимы.
| Монета | Сделок, комиссия 0.05%/сторона | 5bps: net / PF / DD | 0.125%/сторона: net / PF / DD | TOP3 как % всех выигрышных сделок (5bps) |
Предварительно замороженный порог 2025: 0 из 3 ETH/SOL/LINK; требование 2/3, итог **FAIL**. Даже PASS не возмещает A196 gate FAIL на 2026 и известные риски.
Техническое исследование завершено: 4 официальных нативных Freqtrade анализа, 8 настоящих 5m сделок 2025 и 8 настоящих 5m causality-тестов 2026. Пререгистрированный узкий gate FAIL; **решение для живой торговли и автономных PAPER-ордеров — НЕ ДОПУСКАТЬ**. Нужны самостоятельные новые postpublication и live paper доказательства, прозрачная оценка риска 1% на весь счёт, действительное моделирование спреда и очереди лимитов; исходная частота недостаточна для 3–5 сделок ежедневно.

## origin/research/a198-sol-pullback-v9-original-signal-20261031 / research/backup_candidates_20261031/A198_SOL_V9_INDEPENDENT_ORIGINAL_SOURCE_RESULTS_RU.md
**Контрольная дата:** 2026-10-31. **Решение: экономический критерий FAILED, систему НЕ адаптировать, ничего не исполнять.** Отдельный механизм V9, не EMBER и не Double MA.
| Модель риска / расходов | Кол-во сделок | Net return | PF | Max peak-to-trough DD |
По каждому из четырёх сценариев **отрицательное net, PF<1, низкая частота, N=12<20, пререгистрированный gate=FAILED**. Эти результаты опровергают **именно независимую proxy-реализацию с оригинальным кодом входов на конкретном историческом периоде**, а не математически опровергают все стратегии типа «откат по тренду».
**Решение A198:** `ORIGINAL_SOURCE_SIGNAL_REPLAY_PASS`, `EXECUTION_PROXY_REPRODUCIBLE_PASS`, `ECONOMIC_GATE_FAIL_4_OF_4`, `NO_LIVE`, `NO_AUTONOMOUS_PAPER`. Сохранить стратегию как гипотезу; не возвращать к старой убыточной EMBER и не оптимизировать V9 под уже просмотренные 2026 свечи. Для цели нескольких коротких сделок ежедневно нужен кандидат с другой доказанной частотой, отдельными фальсифицирующими окнами и реалистичной моделью комиссий.

## origin/research/a199-futures-source-5m-1h-native-screen-20261031 / research/native_candidate_screen_20261031/A199_NATIVE_FUTURES_SOURCE_SCREEN_RESULTS_RU.md
| Pair | N native | Комиссия 0.05% за сторону net% / PF / DD% | Комиссия 0.125% за сторону net% / PF / DD% | Доля top3 в gross winners при 0.05% |
Совокупно **23 native Freqtrade сделки на 4 отдельных wallets за 141 день ≈ 0.163/day**, не портфельная оценка, никакие проценты не суммируются. **Предварительный gate = FAIL 0 из 4**: требовались >=2/4 с N>=35, net>0 обе комиссии, PF>=1.2, DD<15%, top3 <60% gross winners; сама частота не достигла минимального 1/день для четырёх пар. Рост плеча проблему редкости/низкого математического ожидания не исправит.
| Монета | Сделок | Комиссия 0.05% за сторону: net% / PF / DD% | Комиссия 0.125% за сторону: net% / PF / DD% | Top3 gross winners share (5bps) |
**281 отдельных сделок за 141 день = 1.993/day в четырёх отдельностоящих модельных счетах**, против 0.163/day в часовой A199a. Даже с учётом 5m частоты это **НЕ 3–5/day**, и общая кореллированная система кошелька с 4 одновременными монетами **не была проверена**. Но здесь нет положительного edge: **PF<1 во всех четырёх парах при обеих комиссиях**, то есть увеличение плеча увеличит убытки и риск ликвидации, а не математическое ожидание.
**Пререгистрированный gate: FAIL 0 из 4** при обеих комиссиях; частота 1+ trade/day на 4 раздельных счётах есть, прибыльности нет. **Не оптимизировать** пороги на уже просмотренном 2026 отрезке и не выдавать Freqtrade учебный репозиторий за готовую прибыльную систему.

## origin/research/a200-open-15m-event-driven-validation-20261031 / research/native_candidate_screen_20261031/A200_15M_ORIGINAL_SOURCE_REAL_BINANCE_RESULTS_RU.md
31.10.2026. **РЕЗУЛЬТАТ ЭКОНОМИЧЕСКОГО ОТБОРА: FAILED 0/4 по обеим моделям. Никаких PAPER/REAL ордеров.** Предрегистрация до расчетов: [A200_15M_EVENT_DRIVEN_ORIGINAL_SOURCE_PREREG_RU.md](A200_15M_EVENT_DRIVEN_ORIGINAL_SOURCE_PREREG_RU.md).
| Символ | Trades | BASE net wallet % | BASE PF | BASE max adverse 5m DD% | STRESS net wallet % | STRESS PF |
| Символ | Trades | BASE net wallet % | BASE PF | STRESS net wallet % | STRESS PF |
По заранее установленному критерию хотя бы **2/4** отдельно положительных после base/stress, PF≥1.20, N≥25/пара, DD≤10%, top3 выигрышей <60% и суммарно ≥141 трейд за 141 день:
- **BIGBEAR: 0/4, FAIL**.
- **BIGBULL: 0/4, FAIL**.
- `Gotodataru/binance-futures-backtest`: 5m taker momentum авторский подлинный CSV в репозитории отрицателен на BTC/ETH/SOL, PF≈0.33/0.52/0.75, большое число сделок не спасает.
Это **исходный стохастический авторский `run_book`**, не подсчёт 2025 числа из README. Авторский исходник сам по себе не воспроизводит строго один постоянный исторический PnL; когда внутри свечи неопределённый порядок цен меняется от произвольного seed, положительные единичные прогоны — не доказательство экономического преимущества. Применение настоящих 5m делает последовательность точнее, но всё ещё не знает порядка price ticks внутри одной 5m; поэтому 5m конфликт трактуется STOP-first. Все 16 сценариев после обработки расходов остаются отрицательными.
**Независимая GitHub Actions повторная проверка 16 журналов и источников:** [run 41154189967](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41154189967) `SUCCESS`. A200 append-only journal 200 entries `INTEGRITY_PASS`, `cycle_result=FAILED`. Материальные receipts: `A200_16_SOURCE_ORIGINAL_5M_TRADES_MACHINE_VERIFIED.json`, `A200_16_REAL_BINANCE_5M_TRADE_SHA256_VERIFIED.json`, `A200_ORIGINAL_15M_RANDOM_SEED_SENSITIVITY_VERIFIED.json`, `A200_BINANCE_MARK_FUNDING_5M_SOURCE_SHA_VERIFIED.json`.
**A200 — экономический FAIL.** Никаких 15m параметрических «исправлений» после уже просмотренного 2026, никакого подключения к SMOKE или Binance; сигнальные движки и исторические 5m-данные пригодны как **исследовательский инструментарий**, но стратегию для реального малого депозита они не доказали. Источник авторского результата 2025–марта2026 не воспроизведён на его исходных (неопубликованных) parquet; тест May–Sep2026 не является истинно новым OOS (большинство дат до публикации 06.08.2026).

## origin/research/a201-momentum-wick-rsi-native-screen-20261031 / research/native_candidate_screen_20261031/A201_NATIVE_ORIGINAL_SOURCE_REAL_BINANCE_RESULTS_RU.md
# A201 — фактический результат: 16 подлинных Freqtrade 2026.4 native ZIP, экономический FAIL
% доходности и DD — к $1000 модельному кошельку, не изменение цены. PF — отношение сумм прибыли и убытков. `N` может отличаться между комиссиями из-за изменений времени выходов, что требует осторожности при сравнении fee stress.
| Стратегия | Монета | N BASE / STRESS | BASE net % | BASE PF | BASE DD % | STRESS net % | STRESS PF | N LONG / SHORT BASE |
Это **НЕ** частота единого портфеля и даже не гарантированные независимые сигналы. Экономический отбор каждой стратегии отдельно: **0/4 PASS** (нужно 2 из 4 с N≥35 и net>0, PF≥1.20 на обоих тарифах плюс рисковые гейты).
- `momentum_wick ETH` BASE: +0.408%, PF1.079, 34 сделки — не проходит PF1.2 и N35; STRESS даёт +1.453%, PF1.276, 40 сделок. То, что с повышенной комиссией результат кажется лучше, **не означает, что комиссия повышает прибыльность**: количество и состав исполненных сделок изменились из-за path dependency симулятора, комиссии влияют на моменты выхода, и это дополнительный повод не экстраполировать на реальные исполнения.
- `momentum_rsi BTC` BASE: +0.643%, PF1.249, но 28 сделок; STRESS: +0.495%, PF1.193, 27 сделок. Недостаточно частоты и STRESS PF.
- Остальные шесть монета×стратегия BASE отрицательны; исходный **SL 10% цены ради TP 2% цены** создаёт невыгодную геометрию: без комиссий и дополнительных выходов break-even winrate 83.33%; в базовом сценарии с комиссиями нужен ещё выше. В «сделка должна жить от зоны до зоны» это не вписывается.
### Артефакты и отрицательный контроль
**A201 = экономический FAIL.** Обе исходные стратегии вывести из short-list, но сохранить исходники/тестовые инструменты. **Никаких виртуальных или реальных сделок по ним**. Не подгонять `momentum_wick` под один ETH и `momentum_rsi` под один BTC на той же истории.

## origin/research/a202-dipcatcher-original-native-screen-20261031 / research/native_candidate_screen_20261031/A202_NATIVE_DIPCATCHER_REAL_BINANCE_VERIFIED_RESULTS_RU.md
# A202 — VERIFIED оригинальный dip_catcher (REAL Binance Futures 5m native Freqtrade): ECONOMIC PASS, SPEED FAIL, RISK FAIL
- Independently compared to pre-registered A202 rules BEFORE results: at least 2 of 4 pairs simultaneously both tiers N≥35, net>0, PF≥1.2, wallet DD<15%, top3 win<60%, total >=141 trades /141d each tier.
| Pair | N base / stress | net wallet BASE | PF BASE | maxDD BASE | net wallet STRESS | PF STRESS | maxDD STRESS | QUALIFIES ECON? |
| SOL | 146 / 130 | +3.863385% | 1.32786 | 3.14504% | +1.357194% | 1.11294 | 3.55188% | **NO**, stress PF<1.20 |
В оригинале `stoploss=-0.08` (8% **цены**, даже при 1×), time-based exit отсутствует, ROI динамически снижается до 1% после 60m. При предлагаемом пользователем плече 20–30× ликвидация почти наверняка будет раньше 8% стопа в зависимости от margin tier и комиссий. **SPEED / EXECUTION RISK GATES: FAIL 0/4**, поскольку для всех символов p90>24 часа и стоп неприемлемо широк. Это препятствует подключению к торговому PAPER или реальному исполнению, несмотря на economics.
[Freqle league dip_catcher](https://freqle.org/strategy/72c23c05faa67eaa): 33 инструмента, **10 общих слотов**, период 2022–2024, 21,150 trades, net+747.5%, PF1.37, DD6.71, 1×, stake100, wallet1000, avg HOLD12h26m, max HOLD669h25m, no fresh walk-forward. **Не равняется** нашему 4-карманному Binance May–Sep2026. В Freqle отсутствует `--timeframe-detail 1m`; 5m intra-bar stop/ROI order may bias.
- **A202 = ECONOMIC PASS 3/4, SPEED FAIL 0/4, RISK FAIL, EXECUTION APPROVAL FALSE.**

## origin/research/a203-dipcatcher-2025-independent-holdout-20261031 / research/native_candidate_screen_20261031/A203_INDEPENDENT_2025_ORIGINAL_DIPCATCHER_FAIL_RESULTS_RU.md
# A203 — независимый holdout оригинальной стратегии dip_catcher (2025 May–Sep): ECONOMIC FAIL 0/4, full evidence
- Frozen prereg `A203_DIPCATCHER_2025_FROZEN_HOLDOUT_PREREG_RU.md` committed BEFORE data. Compare original A202 May–Sep2026 economic PASS3/4, speed/risk FAIL.
| Пара | N BASE / STRESS | net BASE wallet | PF BASE | net STRESS wallet | PF STRESS | Economic pair PASS |
**ECONOMIC PASS 0/4.** Gate requires >=2 symbols simultaneously at both fees N>=35, net>0, PF>=1.20, walletDD<15%, top3 winners<60%. Original code not retuned, no best-case selection. 2025 benchmark source unseen in A202, after Freqle original 2022–2024 period, but not actual forward-live as of Oct2026.
- Median/p90 BASE HOLD по BTC **18.33h/289.17h**, ETH **4.92h/54.29h**, SOL **5.67h/46.63h**, LINK **3.5h/43.43h**. Speed gate FAIL 0/4 (p90>24h).
| SOL | +3.863% | +3.280% | stress PF<1.2 both years |
**A203 = economic FAIL 0/4; speed FAIL 0/4; risk FAIL; execution approval FALSE.**

## origin/research/a205-original-sr-rejection-5m-independent-20261031 / research/native_candidate_screen_20261031/A205_NATIVE_2YEAR_ORIGINAL_SR_VERIFIED_FAIL_RU.md
# A205 — проверенный результат 16 оригинальных Freqtrade 2026.4 ZIP: ECONOMIC FAIL, FREQUENCY FAIL
- Фиксированный документ запрета ретюнинга `A205_SR_REJECTION_ORIGINAL_2YEAR_PREREG_RU.md` опубликован ДО тестирования.
| Год | Символ | N BASE/STRESS | Wallet net BASE | PF BASE | Wallet net STRESS | PF STRESS |
**2025: всего 7 BASE и 7 STRESS завершённых сделок/4 монеты/141 день**. **2026: тоже 7 и 7**. Это **0.04965 закрытий/сутки** на четыре монеты, около **1 закрытия в 20.14 дня**. Один ETH 2025, SOL оба года и BTC 2026 не совершили вообще ни одной сделки. Если N<35, даже PF 27 на 4 сделках не имеет статистической ценности; PF=0 с 100% победами на LINK2026 — это техническая особенность backtest агрегатора при отсутствии gross loss, **не показатель отрицательной математики** и не повод повышать оценку.
Ранее prereg economic gate: минимум **2 из 4 монет проходят обе комиссии и оба года** с N≥35, net>0, PF≥1.2, maxDD<15%, top3 выигрышей<60%; plus total N≥141/year/fee — **FAIL 0/4, N7 <141**. Speed gate target >=3 closed trades/day — **FAIL 0.04965/day**.
- 2025 BTC максимальное удержание **550 мин (9ч10м)**; 2025 LINK **1275 мин (21ч15м)**. Обе >90m, исходный `custom_exit` декларирует закрытие при 90 мин; native лимитный выход может зависнуть без исполнения — **parity gate FAIL**. Указанное внешним Freqle среднее46ч не совпадает с целью TTL90m, поэтому необходимо моделировать nonfill/exit fallback до каких-либо адаптаций.

## origin/research/a205-original-sr-rejection-5m-independent-20261031 / research/native_candidate_screen_20261031/A205_SOURCE_CANDIDATE_RISK_FILTER_AND_REJECTIONS_RU.md
Дата 2026-10-31. Все ссылки на внешние рейтинги — вторичный источник; это **НЕ** независимые торговые результаты EMBER. Цель — не переизобретать отрицательные кандидаты; хранить исходники и реестр отказов.
| `Meszqt/freqtrade-test@7062cdd4` | AggressiveSupportResistanceScalper | закрытая предыдущая 48×5m S/R зона, фитиль отбой, RSI/EMA, 10x (6% equity-risk ≈0.6% price), TP11% маржи, time exit90m, нет DCA | **A205 TEST NOW** на независимых 2025/2026; исходный рейтинг PF1.86, но всего 381/33 пары/3 года, очень редкие входы, и в рейтинге 46h avg hold вопреки 90m exit — сомнение/гейт |
| `win-boom/BTCquant@main` | Winner15m | 15m EMA/MACD/ADX/ROC, stop2.5% price, состояния входа много баров подряд, нет time limit | **REJECT FOR EVENT-ENTRY**: высокая частота исходного рейтинга получена при постоянной готовности повторно входить, исходник без one-shot edge; не считать событием |
| `win-boom/BTCquant@main` | MTF_Hybrid | `ema200_1d` есть `EMA(close,19200)` на 15m, startup500 vs требуются 19200 баров, не настоящая daily informative свеча; PF≈1.08 внешне | **REJECT** ненадёжная warmup/«1D» маркировка, состояние сигнала; не выдавать за true MTF |
| `TheoBrigitte/freqtrade@c9def379` | RsiquiV5 | centered `np.gradient` внутри полного ряда | **REJECT** истинный future dependency на прошлых сигналах; original can't be backtested as causal |
| `jaredrsommer/freqtradestrategies@9d66f71c` | FVGChannel | TF1h, исходный SL10% price, форсированная ширина FVG 23.67% цены | **REJECT** уровень FVG сконструирован эвристически, а не реальная локальная 4H структура |
| `jaredrsommer/freqtradestrategies@9d66f71c` | 2Candle | `class 2Candle` невалидный Python identifier, нет `can_short=True`, комментированный `1% stop` фактически `stoploss=-0.03`, ROI1.5% | **REJECT** source not directly runnable и ложная документация стопа; rewriting changes candidate |
| `cheafi/trading-team@5a8336d6` | A51Strategy | 5m S/R/VWAP, stop0.5% price, TP0.8%, но сам автор в TODO.md приводит 2021–25 backtest −2.94% за пять лет и PF0.60 за 2023–25 | **REJECT** нет основания повторять на уже изученных годах, автор признал отрицательную доходность |
- Подгонять параметры задним числом. Если A205 по одному году/fee убыточен или имеет недостаточно сделок — FAIL, даже если отдельный ETH-участок красивый.
Результат самого A205 будет только в `A205_SR_ORIGINAL_TWO_YEAR_NATIVE_VERIFIED.json` или в отдельном FAIL/BLOCKED отчёте по подтверждённым логам. Существующие SMOKE, PAPER scheduler и live trades не затронуты.

## origin/research/a205-original-sr-rejection-5m-independent-20261031 / research/native_candidate_screen_20261031/A205_SR_REJECTION_ORIGINAL_2YEAR_PREREG_RU.md
A197–A203 зафиксированы в `A204_POSTMORTEM_SCREENING_AND_REUSABLE_TOOLING_RU.md`. Не повторять стратегию dip_catcher, которая дала PASS в 2026, но FAIL 2025 и 98% постоянной экспозиции. Не выбирать победителя среди многократных тестов по последним наилучшим процентам.
- `Winner15m` из `win-boom/BTCquant`: оригинальные EMA/MACD/ADX/ROC **состояния**, а не короткие one-shot события; `enter_long` и `enter_short` выставляются многим барам подряд. Оставлен отдельным отрицательным контролем на возможную постоянную экспозицию, НЕ выбран и НЕ оптимизируется.
- `RsiquiV5` отклонён уже из-за `np.gradient` centered future contamination в прошлых оригинальных тестах; `HighFrequencyStrategyV1/2` имеют внешние ранжированные экономические FAIL.
- Его внешний [Freqle League](https://freqle.org/strategy/36e5874af3a1ebcf) утверждает **381 trade на 33 монетах/3 года**, PF1.86, +55.8%, DD4.51%. Это ПРОИЗВОДНАЯ многомонетного исторического leaderboard, а не независимый 4-символьный backtest. 381/(33×1095)≈0.0105 сделок в день на монету; для 4 монет ожидание лишь ~0.04/сутки, если средние равномерны. Эта крайне низкая внешняя частота уже предупреждает, что наша цель 3–5 закрытых A+ в сутки вероятно не будет достигнута. Мы это НЕ будем скрывать даже при прибыльном результате.
- Внешний отчёт также сообщает среднее удержание **46h**, MAX >200 суток вопреки `custom_exit` 90m. Возможный дефект исполнения модели/лимиток/версии в исходном рейтинге; проверяем `open_date`→`close_date` из подлинных ZIP, `exit_reason`. Если backtest нарушает авторский TTL, это FAIL уровня parity.
- 16 подлинных native ZIP (4 coins×2 fees×2 years), SHA256 Freqtrade, fixed source blob, сверка trade PnL sum, абсолютная прибыль по индивидуальному кошельку, PF/DD, winrate, median/p90/max duration, reentry gap и utilisation. Символ и год запрещено выбирать post hoc.
- ECONOMY GATE: >=2 ИЗ 4 монет показывают одновременно в **обоих годах и обоих расходных сценариях** N>=35, wallet net>0, PF>=1.2, wallet DD<15%, top3 gross wins share<60%. Кроме того, >=141 завершённых trades на 4 отдельных wallets в каждом году/fee (~1/day). Целевой TEMPO GATE: >=3/day across 4, p90 hold<=24h, минимум 70% повторных входов спустя >5m после предыдущей сделки, >=20% времени имеются свободные слоты.
3. Только после получения native ZIP опубликовать подписанный машинными SHA отчёт и **FAIL/PASS без ретюнинга**.
4. Если CI не работает → BLOCKED, нет искусственных данных.

## origin/research/a207-taker-pressure-5m-2024-frozen-holdout-20261031 / research/native_candidate_screen_20261031/A207_ORIGINAL_TAKER_VOLUME_3YEAR_FROZEN_REAL_BINANCE_FAIL_RU.md
# A207 — реальная проверка taker buy/sell pressure 5m: FAIL 0/4 во всех 2024–2026 годах
| Year | BTC N/net%/PF | ETH N/net%/PF | SOL N/net%/PF | LINK N/net%/PF | Trades total |
**Все 12 BASE year×coin результатов отрицательны, все STRESS ещё хуже.** При более дорогих исполнениях каждый исходный set N сохранился (независимая fixed bracket модель).
**A207 — ECONOMIC FAIL 0/4 and TEMPO FAIL**, strategy rejected intact; no modifications of parameters on the 2024–26 data allowed. Достоинство эксперимента — настоящий buy/sell aggressor flow, архивные SHA и три года. Сам по себе taker ratio нельзя использовать как готовый A+ entry trigger.

## origin/research/a208-dynamic-gainer-scalper-original-code-rejection-20261031 / research/native_candidate_screen_20261031/A208_DYNAMIC_GAINERS_3M_15M_ORIGINAL_BACKTEST_SOURCE_REJECT_RU.md
**A208 = BLOCKED/REJECT для оригинального «готового» бэктестера без финансового теста**. Не смешивать с A207 (тот действительно прошёл 120 real Binance source ZIP, 24 торговых журнала; A207 экономически FAIL). Нельзя делать вид, что текущий гейнер показывает доказанную прибыль. Можно исследовать после восстановления причинной временной шкалы, восстановления PnL и fee/funding, но такая версия **будет другой, адаптированной системой, не результатом оригинала** и требует отдельного pre-registration.

## origin/research/a209-fast-scalper-source-short-activation-audit-20261031 / research/native_candidate_screen_20261031/A209_2_MORE_SCALPERS_ORIGINAL_SOURCE_AUDIT_AND_RESET_RU.md
Дата: 2026-10-31. RESEARCH ONLY. Это исходный аудит, **не финансовый бэктест**, доходность и PF ниже не утверждаются. Отделять source facts от рекламных claim.
- A207 source `Gotodataru/binance-futures-backtest` настоящие taker-buy pressure 5m, 2024/2025/2026 May-Sep, 120 Binance source ZIP и 24 trade receipt SHA: **economic FAIL 0/4 все три года, N24/53/101**. Среди 178 сделок 166 вышли по time exit 80m, десять по SL, две по TP2%; даже до сильного стресс-тарифа сигнала направления почти нет. См. `A207_ORIGINAL_TAKER_VOLUME_3YEAR_FROZEN_REAL_BINANCE_FAIL_RU.md`.
- A208 source `kiattisakph/crypto-scalp-bot` 3m+15m динамический топ-гейнер, авторский тестер **lookahead future 3m/15m close at open_time**, `pnl_pct` undefined in `_close_position`, no fee/slippage/funding in `_calc_pnl`, значит исходник не годится для честной оценки, см. `A208_DYNAMIC_GAINERS_3M_15M_ORIGINAL_BACKTEST_SOURCE_REJECT_RU.md`.
- A206 независимая raw-signal vs fill проверка A205 была опубликована как workflow, но CI JSON до сих пор не подтверждён. **Не считать A206 законченным**; A205=FAIL не пересматривать.

## origin/research/a211-daily-donchian-original-futures-3year-native-20261031 / research/strategy_research_reset_20261031/A211_ORIGINAL_DAILY_TREND_NATIVE_THREE_YEAR_FAIL_RESULTS_RU.md
| Period | BASE N | BASE wallet return | BASE PF across 4 ledgers | STRESS wallet return | matched $100/coin price-only hold |
ETH 2026 +4.105045% / PF11.95 with **only 5 trades**; это недостаточная статистика, нельзя объявить отдельную доходную ETH-стратегию. 2024 ETH +0.3919%/PF1.085, 2025 ETH +0.4161%/PF1.065 — PF<1.2. 2024 and 2025 worst LINK account -4.57%/-6.83%, 2025 maximum **reported realized** account DD9.84%, но настоящий portfolio marked-to-market DD не вычислен: не подменять один другим.
**Research economic gate FAIL, no forward approval.** 2026 положителен в одном режиме, 2024/2025 отрицательны. Даже до extra live spread/slippage нет устойчивого положительного преимущества. Не оптимизировать 20/10/3→18/16/9.5 задним числом на тех же окнах и не рекламировать «1d лучше, потому что редкие сделки».

## origin/research/a213-two-leg-carry-offseason-heldout-20261031 / research/strategy_research_reset_20261031/A213_FULL_SEASON_FUNDING_CARRY_ROBUSTNESS_AND_MARGIN_REJECTION_RU.md
# A212 + A213 — закрытие исследовательской проверки двухногого funding carry: доход есть, ГЕЙТ РИСКА FAIL
A212 positive modeled economy in May-Sep but A213 FULL CHECK **FAIL due to 2023/24 SOL collateral risk and 2025/26 yield deterioration.** This is a *credible mechanism* but not a deployable system. Existing SMOKE/PAPER, user positions and schedulers unchanged.
