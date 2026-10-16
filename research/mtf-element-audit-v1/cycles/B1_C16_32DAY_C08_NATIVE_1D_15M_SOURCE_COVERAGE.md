# B1/C16 — 32 последовательных UTC дня original Binance Futures 15m ↔ native 1D + производный 4H

**Дата:** 2026-10-16. **Приёмка в границах:** независимая SOURCE→OHLCV→TIMEFRAME continuity на **2026-09-01 — 2026-10-02**, пять USD-M Futures монет. **НЕ** авторская аттестация POI/StrongHL/VC, PAPER ONLY.

## Зачем продолжать после C15

C15 независимо сравнил 5m → оригинальные C08 15m и производные 1H/4H/1D лишь за **2 дня**. Двух дней недостаточно даже для содержательной проверки длинного старшего 1D/4H контекста. В уже проверенном C08 обнаружен запас источников без новой исторической пересборки: **33 помесячных исходных 1D ZIP (2024-01…2026-09) и 6 помесячных исходных 15m ZIP (2026-04…2026-09) на каждую из пяти монет**, плюс по 12 ежедневных 15m/1D ZIP за 1–12 октября 2026 года. Все 315 оригинальных C08 archives ранее отдельно SHA+remote-CHECKSUM replayed; **этот цикл** повторно независимо скачивает точно выбранные **30** из них.

## Реализация

- `d05/c16_c08_monthly_daily_htf_lineage.py`: read-only `c08_bound_archive` повторно вызывает **неизменённый** source D04 `verify_raw_zip(url, raw_zip, .CHECKSUM)`, после чего требует full original C08 receipt `zip_sha256`, `raw_csv_sha256`, URL, symbol, market USD-M, tf, rows и immutable `normalized_all_11_columns_matched=true`.
- `extended_32day_prefix`: строго трёхкомпонентные **месячный сентябрь + дневные 1 и 2 октября 2026** исходники отдельно для native **15m** и отдельно для native **1D**; 32 последовательных дня. Не допускает пропуск дня, неправильную сетку, source-ID или другой символ, отказ от авторской готовности.
- Из native 15m в `Decimal` выводятся полностью закрытые 1H (**4 × 15m**) и 4H (**16 × 15m**), 1D (**96 × 15m**). Для **каждой** закрытой 1D отдельный original native Binance 1D источник проверяется на *точное* O/H/L/C/volume/timestamp соответствие агрегированной 15m, без допуска. Из будущего дня не выдаётся ещё открытая 1D или 4H. Исходники source ZIP+CSV SHA сохраняются на каждом результирующем уровне.
- `d05/test_c16_c08_monthly_daily_htf_lineage.py`: **30** новых негативных/позитивных unittest-случаев: missing Oct day/month, 4H 03:45 vs 04:00, 1D закрытие, same day/time, lookahead, raw receipt sha mismatch, fake archive checksum, unknown market symbol, raw source ID tampering, 1D vs 15m volume/price disagreement, close-as-of future cannot change past, frozen `NOT_TRADE_READY`. Все синтетические fixture цены в unit tests обозначены как **synthetic; not original USD-M evidence**. Первая CI [38937085766](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/38937085766) завершилась **FAIL только из-за неверно ожидаемой категории исключения** на неизвестном символе; код правильно отклонил символ на более раннем фильтре. Тест скорректирован и перезапущен успешно.
- `tests/probe_c16_32day_native_htf_sources.py`: **30 оригинальных Binance USD-M ZIP**, из них 15 native 15m (5 × Sep monthly + Oct1 daily + Oct2 daily) и 15 native 1D с **теми же датами**. HTTPS+same-host .CHECKSUM и отдельные ранее закреплённые C08 receipts. За пределами этой ветки исходные C08 и v05 не переписаны.
- `evidence/c16/C16_32DAY_NATIVE_15M_1D_RECEIPT.json`: source-level квитанция 30 оригинальных ZIP+CSV SHA и точных чисел на каждую монету, Git blob **`bdaa008ce719254507ea95231cdc630bfa85cd67`**. Новая CI должна точно воспроизвести **каждый** из 30 источников по этой квитанции, а оригинальные C08 receipts по пяти символам отдельно Git SHA защищены. `tools/strict_vision_d04.py` не менялся.

## Независимая сеть и измеренный результат

[Первый CI с 30 raw Binance ZIP и 214 тестами — 38937390001](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/38937390001) **SUCCESS**. [Повторный CI с сохранённой 30-источниковой квитанцией 38937575008](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/38937575008) **SUCCESS**. Финальная SHA-pinned проверка пяти оригинальных C08 receipts запускается отдельно.

| Ценовая проверка | На один символ | Все 5 символов | Доказательство |
|---|---:|---:|---|
| Оригинальные native 15m | 3072 | **15 360** | 15 ZIP |
| Производные закрытые 1H | 768 | **3840** | по 4 native 15m |
| Производные закрытые 4H | 192 | **960** | по 16 native 15m, **не native 4H ZIP** |
| Independently native 1D | 32 | **160/160** | 15 отдельных native 1D ZIP, 100% exact Decimal OHLCV равенство с 15m |
| **Исходники сети всего** | 6 ZIP | **30 ZIP** | frozen C08 SHA & same-host HTTPS CHECKSUM |

Пример as-of: после первого часа 2 октября доступна 1D за 1 октября, но **ещё недоступна дневная свеча за 2 октября**. Никакое предварительное high/low внутри этой будущей дневной свечи не превращается в закрытый 1D-контекст.

## Что НЕ подтверждено

1. 32 дня позволяют анализировать более длинную историческую price structure, но **не доказывают** наличие хотя бы одного авторски правильно размеченного **1D/4H POI, StrongHL или VC**: нет независимо привязанных авторских меток к конкретным timestamp и OHLCV Binance Futures.
2. Данные 4H/**1H производные** из native 15m, не отдельные оригинальные архивы 4H/1H; нельзя приписывать им неизученную биржевую подпись происхождения. C08 provenance через HTTPS+same-host CHECKSUM **не** цифровая подпись Binance.
3. Остальные **2024-01…2026-08** monthly C08 1D и **2026-04…2026-08** monthly C08 15m существуют в ранее проверенном C08, но **этим циклом НЕ перескачаны** и не объединены в один многолетний replay. Нет доказанного полного route 1D→4H→1H→15m→5m на исторической длине.
4. Frozen course-v05 2+2 fractal pivots и raid 24h freshness всё ещё не утверждены авторской разметкой. Нет конкретного author-selected parent POI/BOS для ambiguous C12/C13, не определены stop/FTA и прибыльность.
5. Никаких торговых операций/ключей/SMOKE/V5/QFVG не трогали. **0 авторских StrongHL/VC, 0 READY.**

**Следующий шаг:** на новой native-32d цене добавить read-only независимый replay *контекстных* 1D/4H уровней и контрпримеры истинной/ложной реакции, но без авторской метки оставить `AUTHOR_GOLDEN_SOURCE_UNAVAILABLE`. После этого перейти к совмещённому MTF parent→child, оставаясь PAPER ONLY.
