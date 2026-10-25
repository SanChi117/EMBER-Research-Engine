# B1/C62 — академическое разделение SNR / RB / MB / IMB на ORIGINAL CRYPTO, без подмены авторских кейсов

**Дата:** 25 октября 2026, UTC. **Ветка:** `research/academic-engine-recovery-20261015`, `SanChi117/EMBER-Research-Engine`. **Режим: CRYPTO ONLY, PAPER ONLY / NOT_TRADE_READY. Ни одного ордера.**

## Первая проверка — первичные уроки академии

Прочитаны повторно реальные файлы на Google Drive (не подменять общими ICT/SMC эвристиками):

- **`5. Support And Resistance .txt`**, ID `1OOyS7C8T8H4FdD47dXsnx7y3u33lNG7m`: SNR — проторгованная область, имеет две противоположные свечи Buy+Sell или Sell+Buy, затем **следующая полноценная свеча** должна закрепиться в нужную сторону выше/ниже уровня пары; сильная POI работает со снятием BSL/SSL или тестом FVG/IMB, **SNR без этой работы — weaker Mitigation Block (MB), не Volume Confirmation**. Для SNR raid/IMB-тест может выполняться телом свечи.
- **`3. Rejection Block.txt`**, ID `1bFjOPZdiHEAdM_QN58EWBDpgsYx_p0nT`: RB тоже две противоположные свечи, но **ликвидность либо IMB обязаны взаимодействовать строго тенью**, а не телом, и при тесте IMB тело закрепляется за его границей. RB не следует называть SNR автоматически. Только по теням может строиться зона RB; локализация авторской зоны на схематических рисунках ещё требует отдельных price-goldens.
- **`Fair Value Gap  Imbalance.txt`**, ID `1ajvG1554qQ-5AnIV8HVmoDflkNRrU-LN`: классический 3-свечный FVG/IMB является **свободным пространством между тенями** первой и третьей свечи после закрытия третьей; цвет первой/третьей не важен. BPR/iFVG разновидности существуют, но C62 их ещё не распознаёт — не смешивать с classic.
- **`2. Entry by IMB & SNR.txt`**, ID `1hkKKwy60-VIoqEsVYAq12mnPZA7ySXFQ`: Route A строится от старшего контекста; 1H RB может быть контекстным VC/POI, но для непосредственного final entry эта академия допускает только **SNR либо IMB** на финальном LTF; не переводить просто 1H RB в ордер.

## Восстановленная классификация C62 — строго раздельная, без ретроспективной подгонки

- [x] `d05/c62_academic_snr_rb_imb_liquidity_source_separation.py`: отдельные 1H source observations от оригинальных native15m, `preknown` confirmed 1H fractal BSL/SSL проверяется **раньше первой свечи пары**, отброшенные source-breach уровни не используются. Не считать bare fractal StrongHL. Категории SNR / MB / RB формируются независимо от трёхсвечного classic IMB.
- [x] **SNR_SOURCE**: две свечи противоположного тела, затем *следующая* закрытая свеча нужного направления завершает close строго за экстремумом пары (техническая консервативная версия «закрепа», не академическая price-разметка); если был заранее известный SSL/BSL source breach либо контакт с ранее закрытым 1H FVG — source evidence SNR, иначе `MB_WEAKER_SOURCE_ONLY_NO_RAID_OR_IMB_NOT_VOLUME_CONFIRMATION`. **Это прокси**, нет измерения настоящего профиля проторгованного объёма.
- [x] **RB_SOURCE**: две противоположные закрытые свечи, strict заранее известный unswept 1H source SSL/BSL пересечён **только тенью** (open/close не ушли за уровень) ИЛИ раньше сформированный source classic IMB протестирован тенью при close тела вне gap. Если тело пересекло известную ликвидность, **не классифицировать это как RB wick-raid**. Категория без доказательства `RB_TWO_OPPOSITE_HOURLY_CANDLES_WITHOUT_VERIFIED_WICK_RAID` не имеет права становиться академическим RB.
- [x] **IMB_SOURCE**: только после полной 3-свечной native-derived 1H структуры; строгий gap по high/low, provenance по оригинальным SHA:15m timestamp, без будущих баров.
- [x] source 1H уровни, IMB и свечи по исходным SHA проверяются перед классификацией, незакрытая свеча и поддельная строка не принимаются. Source physical cutoff at as-of = полный оригинальный поток ограниченный тем же as-of.
- [x] 22 теста `d05/test_c62_academic_snr_rb_imb_liquidity_source_separation.py` × Python3.10/3.11/3.12 на ложные wick/body raids, слабый MB, не-закреплённый SNR, неверное время появления FVG, поддельную исходную OHLC цену/объём, неверный SHA/timestamp, незакрытый 1H и физический as-of.

## Реальная проверка только на ORIGINAL Binance USD-M источнике

- [x] `tests/probe_c62_original45zip_1h_snr_rb_imb_separate_source.py` **дважды самостоятельно** загрузил **45 оригинальных подписанных Binance USD-M ZIP + checksum** за 01.09–02.10.2026 (15 original native3m, 15 original native15m, 15 original native1d) на BTC, ETH, SOL, XRP, BCH. **76800** closed native3m; **160** closed original native1d; **15360** exact Decimal original15m parity; **3840** derived полностью закрытых 1H.
- [x] Все **153** исторических technical 4H C46 source parents сверены без изменения C46 blob `dc03c181912ffbb800bc191fbc16ec0d05c335e0`. Независимый C61 source blob `305624e592f55bd699e94e45f4316e4efabdb726` не изменялся.
- [x] Первичная полноценная [CI 40210255871](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40210255871) **SUCCESS**: полная original45ZIP проверка, 22 negative tests ×3 Python, original source freeze 2 498 773 bytes Git blob `8428bf7d6cd3bc26f617cfc32a34c91a27c813b2`, SHA256 `8ac92d6406845568a2e0178be81fc2fec529da2d26697b6f08b7fbaa4e5a0c80`.
- [x] Вторая **независимая** fresh original45ZIP полностью повторная [CI 40210402103](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40210402103) **SUCCESS 4/4**, все **2 498 773 байта** JSON совпали (`cmp -s` и SHA256), 22 negatives на Python 3.10/3.11/3.12 повторно.
- [!] Первый негативный [CI 40209939146](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40209939146) FAIL из-за ошибочно составленного синтетического исходного бара (`open=88`, `low=99`). Исправлена **тестовая свеча** с корректным low=88, **не ослаблены** реальные OHLC проверки. Успешный повтор [CI 40210045297](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40210045297) SUCCESS 3/3 и проверка после оптимизации source уровней [CI 40210099486](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40210099486) SUCCESS 3/3. Исторический FAIL хранить.

## Истинные числа исходных технических классов — НЕ авторские POI / сделки

| Техническая классификация на 3840 fully closed оригинальных derived1h | Количество |
|---|---:|
| Classic 1H IMB (3-candle wick gap) | **646** |
| Source SNR, третья свеча закрылась за экстремумом пары + есть earlier source liquidity | **128** |
| Source SNR, третья свеча закрылась + есть earlier source IMB interaction | **213** |
| Source слабый MB (закреп пары без доказанного source liquidity/IMB) | **62** |
| Source RB с wick-only earlier strict fractal raid | **394** |
| Source RB с wick-only preknown source IMB work | **556** |
| Opposing 1H pairs БЕЗ доказанного wick-only RB source precondition | **1039** |

Все классификации — **прокси**; 1H технические кандидаты могут иметь общие свечи, source pair быть классифицирована RB и через следующую свечу как SNR (другое событие), поэтому числа нельзя суммировать как независимые возможности входа. 1H source FVG и три-свечный strict fractal **не** авторски отобранные 1H POI / StrongHL. Нет исследования торговой прибыли и статистики успеха. Нет утверждения о фактической торговле реальными ордерами.

## Границы и что дальше

**Не завершено:** настоящее авторское позиционирование зоны SNR по областям интенсивного проторгованного объёма, MB/опорная область, RB точные wick boundaries/0.5, author SNR/RB/IMB graphical goldens, 4H/1H StrongHL source context contact→REACTION confirmed VC/BOS, BPR/iFVG/OB, инвалидация, FTA/SL/TP. Не путать исходные прокси с истинной академией. C62 подтверждает **разделение категорий и исходные данные**, а не сделки. Отчётность `CRYPTO ONLY / PAPER ONLY / NOT_TRADE_READY`, `orders=0`, `trades=0`, `fills=0`.

**Следующее:** C63 — изолировать source chronological first POI contact → подтверждённую реакцию / BOS/VC → статус StrongHL без horizon lookahead; получить академические конкретные goldens из учебных схем, если доступны, отдельно от исторических crypto source. Ни один SNR/RB source case не становится автоматическим приказом.

## SHA-приёмка A132

После двух независимых original45ZIP SOURCE CI и 22 ×3 негативных тестов append-once **A132**: ровно 6 evidence paths (source classification module, 22 tests, original full45zip script, 2.5MB complete JSON, independent witness, этот отчёт). Сохранить полный прежний **A131/131 tip** `c68b21ba65b97f2ef39441227a3dd18e32564bd05bc95e3bcdb05571106c785d` и все замороженные source evidence C46…C61. Затем отдельная финальная независимая `132/132 SHA × Python3.10/3.11/3.12`.
