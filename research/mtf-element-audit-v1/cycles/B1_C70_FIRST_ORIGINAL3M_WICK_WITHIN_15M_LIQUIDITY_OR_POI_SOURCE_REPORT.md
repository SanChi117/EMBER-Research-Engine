# C70 — первое исходное 3m касание внутри первой 15m свечи: криптовалютная source-проверка

**2026-10-25 UTC.** Репозиторий `SanChi117/EMBER-Research-Engine`; ветка `research/academic-engine-recovery-20261015`. **PAPER ONLY / NOT_TRADE_READY / orders=fills=trades=0.**

## Правила автора

`Strong High & Low.txt` (Drive ID `1lvPRbhfM6ZjfW7UP-30y9uND1R6VC13t`) — сильный максимум/минимум формируется только после **реального контакта liquidity ИЛИ inefficiency** и последующего истинного **VC POI ИЛИ BOS** на том же либо младшем TF. `Order Flow.txt` (ID `1r6sH0XjEoK4Jwq4EVLz8vqPSWVh9qerN`) требует для истинного OF работу с liquidity **И** IMB. Это не означает, что 3m wick автоматически подтверждает авторский StrongHL, volume confirmation, BOS, направление сделки или structural SL.

## Выполнено

- [x] Отдельный `d05/c70_exact_native3m_first_raid_or_poi_source_wick.py`: из **C69** берётся ранее найденная действительно первая исходная 15m-свеча снятия заранее известной 1H SSL/BSL или первого технического касания предполагаемой NEW 1H POI. Для каждой такой свечи проверяются **ровно 5 исходных native3m SHA:timestamp**, сравнивается их точная **Decimal OHLCV** агрегация с оригинальной native15m свечой, выбирается **первое ЛЮБОЕ реальное 3m пересечение тенью** уровня или POI. Source 3m wick-only выделяется отдельно от source 3m body-close за SSL/BSL. Никакого выбора выгодной более поздней свечи.
- [x] Критически важно: **часовая** SSL/BSL raid-структура считается известной **ТОЛЬКО после полного закрытия original 1H**, даже если её тень впервые пересекла ликвидность раньше на 3m. `earliest_source_claim_eligible_ms=max(native3m first wick close, source1h full close)`. Для предполагаемой NEW1H POI всё равно лишь технический источник: native3m касание **НЕ авторский first VALID POI test**. Не изменены другие маршруты A/B/C, нет FTA, SL, TP, ордеров или PnL.
- [x] `d05/test_c70_exact_native3m_first_raid_or_poi_source_wick.py`: **20 негативных тестов × Python3.10/3.11/3.12**: первая 3m тень может возникнуть на любой из пяти, тело 3m за уровнем при последующем закрытии 15m внутри, forged SHA/time/volume/OHLCV, 3m gap/missing, author VC/StrongHL spoof, future/source timestamp и parent-ID. [CI 40222961681](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40222961681) **SUCCESS 3/3**.
- [x] `tests/probe_c70_original45zip_exact_first_native3m_wick.py`: **45 оригинальных независимо SHA-verified Binance USD-M ZIP** на BTC/ETH/SOL/XRP/BCH за Sep1–Oct2 2026, 76800 native3m, 15360 native15m, 160 native1d, 3840 derived closed1h. Все 153 исходных C46 parent прошли независимый пересчёт предыдущей последовательности C46→C60→C62→C63→C66→C67→C68→C69 с теми же OHLCV и SHA:bar IDs. Первый full [CI 40223455747](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40223455747) **SUCCESS 5/5** и независимый второй full fresh оригинальных 45 ZIP с **побайтным сравнением целого JSON** [CI 40223655477](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40223655477) **SUCCESS 4/4**, тесты 20×3 повторены.
- [x] Source `evidence/c70/C70_ORIGINAL45ZIP_EXACT_FIRST_NATIVE3M_WICK_WITHIN_C69_15M_SOURCE.json`: **214905 bytes**, SHA256 `b93edbb2eabdefeff6161f80c17d5e35013bc8b0205aaefac63e15f0a6b37ef9`, Git blob `e100ca8a70a32484fd311ae2dcf31a311d85865c`. Witness `evidence/c70/C70_INDEPENDENT_ORIGINAL45ZIP_FIRST_NATIVE3M_SOURCE_WITNESS_20261025.json`.

## Не подогнанная статистика SOURCE, исходные 153 технических 4H contexts

| Статус source | Случаев |
|---|---:|
| C69 не дал однозначного контекста или выбора предварительного уровня | 95 |
| Первый original3m пересекает SSL/BSL и закрывается внутри уровня | 15 |
| Первый original3m закрывается за SSL/BSL, более поздняя свеча восстанавливается | 8 |
| Первое source пересечение NEW1H POI на original3m — НЕ авторски VALID | 35 |
| **Всего** | **153** |

**Source-предложения не являются независимыми сделками и могут пересекаться.** Цены 15m для этих событий уже точно сверены по пятёрке исходных 3m баров. 95 = 92 без однозначной C67 цепочки + 3 source ambiguous по нескольким preknown уровням из C69. Результат на 3m может отличаться от закрытия 15m, поскольку более мелкая свеча могла закрыться за уровнем, а 15m восстановиться.

## Ограничения / дальнейший этап C71

Оригинальные курсовые графики — примеры **логики**, но **нет ни одного размеченного автором crypto-кейса Binance symbol+timestamp+native source SHA** для valid/invalid POI test, real BOS/VC и StrongHL. Поэтому реальные академические StrongHL, SL/TP/FTA, confidence, A+ candidate, OOS и торговый результат **не доказаны**. Следующий C71: source-independent 3m/15m/1H contact-close state machine для проверки post-contact VC/BOS и first VALID POI test fail-closed, с запретом раннего появления сигнала, затем структурная FTA/SL/TP и OOS с комиссиями только в PAPER.

## Запись A140

Шесть SHA evidence после двойного original45 ZIP и 20×3 tests: C70 module, 20 negatives, 45 ZIP probe, frozen 214905-byte source, independent witness, **этот отчёт**. Сохранить A139 `78271dd0a96a54713e4559fe47107ccf063b7ba8f4ed384d8aa166f2cae9c227`; после A140 сверить 140/140 SHA × три Python. Ни один из шести frozen файлов позднее не редактировать.

**PAPER ONLY / NOT_TRADE_READY.**
