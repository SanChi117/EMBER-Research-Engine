# B1/C15 — проверенная исходная MTF-сетка 5m → 15m → 1H → 4H → 1D

**Дата:** 2026-10-16. **Область приёмки:** CLOSED_PRICE_LINEAGE_AND_SOURCE_PARITY_ONLY, **NOT_TRADE_READY**, PAPER ONLY.

## Принцип

Для механики TDA, 4H POI → 1H Trigger/VC → 15m/5m Entry нельзя использовать неодновременно закрытые свечи, будущую 1D/4H структуру и подменять 5m источники агрегированной минуткой другого рынка. Данные должны соответствовать своему таймфрейму, инструменту, USD-M Futures происхождению и `as_of`.

Академические источники StrongHL, POI, IMB и TDA действительно требуют старший контекст и подтверждение на соответствующем TF, но они **не утверждают**, что две дневных свечи дают полноценную историю 1D POI. Также по ним нельзя автоматически сделать авторскую разметку 4H/1D POI из одного OHLCV.

## Реализация

- Новый read-only `d05/c15_closed_multi_tf_source_grid.py` принимает два `Verified5m` из прежнего F06, сначала повторяет строгие C10 проверку symbol/day/time/as-of, затем **каждую** исходную строку 5m сверяет по 12 raw CSV полям, Decimal O/H/L/C/V, timestamp, bar `end` exclusive, Git-raw ZIP ID. Не принимает декларацию автора `READY`.
- Из **исключительно уже закрытых** 5m создаёт immutable `ClosedMtfCandle`:
  - 15m = **3×5m**, 1H = **12×5m**, 4H = **48×5m**, 1D = **288×5m**.
  - OHLCV через Decimal без float при агрегации, `known_at_ms` = close exclusive, `source_5m_ids` и archive SHA сохраняются для проверки.
  - Неполные 4H/1D **не входят** в наблюдаемый префикс; 0, 1 или 2 закрытых дневных свечи возвращают раздельные `daily_coverage` с блокировкой авторской HTF готовности.
  - Нет выдуманных 1D/4H native ZIP; эти TF **DERIVED**. Нельзя подменить их source attestation других архивов.
- `d05/test_c15_closed_multi_tf_source_grid.py`: **32** негативных и позитивных теста на частичное закрытие 15m/1H/4H/1D, перенос UTC дня, запись объёма, raw CSV timestamp/high/low/close против объекта `Bar`, non-finite/negative volume, future-as-of, cross-symbol, поддельный авторский READY и сохранение прошлого при замене будущего.
- `tests/probe_c15_original_full_tf_grid.py`: **10 настоящих оригинальных ZIP 5m** + **10 независимо скачанных оригинальных ZIP 15m из C08** вместе с HTTPS same-host CHECKSUM. Каждый источник сверяется с отдельными ранее замороженными SHA ZIP и CSV F06/C08, после чего строятся обе независимые сетки: исходная 5m→15m/1H/4H/1D и оригинальная 15m→1H/4H/1D. Полное и точное совпадение Decimal OHLCV и known_at по каждому закрытому периоду — обязательное условие.
- Сформирована новая immutable квитанция `evidence/c15/C15_F06_5M_NATIVE_15M_DERIVED_1D_4H_SOURCE_RECEIPT.json`, Git blob **`696065b29bbe45f5f4fdd0bf8042c4f5781c170d`**, где сохранены все **20 исходных ZIP/CSV SHA**, ожидаемые counts и непризнанные academic labels.

## Исходная проверка Oct 1–2, 2026 UTC

Инструменты BTCUSDT, ETHUSDT, SOLUSDT, XRPUSDT и BCHUSDT. **2 полных дня по каждому**, 10 исходных 5m и 10 C08 исходных 15m архивов.

| TF результата | По одной монете | По пяти монетам | Статус источника |
|---|---:|---:|---|
| 5m raw | 576 | 2880 | original Futures 5m ZIP |
| 15m | 192 | **960/960 OHLCV** | сравнен с отдельным original C08 15m ZIP |
| 1H | 48 | **240/240 OHLCV** | derived independently from original 5m и original 15m |
| 4H | 12 | **60/60 OHLCV** | derived independently, **не** native 4H |
| 1D | 2 | **10/10 OHLCV** | derived independently, **не** native 1D |
| **Все сравнения OHLCV** | **254** | **1270/1270** | Decimal exact, strict UTC closure |

После закрытия второго дня + 1H система всё ещё видит лишь **одну ранее закрытую 1D свечу**; текущая 1D до конца суток не видна. Это предотвращает future HTF lookahead.

[Первый независимый сетевой CI 38934933859](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/38934933859) **SUCCESS**. [Повторный независимый CI с закреплённой C15 квитанцией 38935237106](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/38935237106) **SUCCESS**. Для исходного v05 29 + новых C15 32 = **61** source unit-tests PASS. Полная проверка 184 тестов (29 v05+155 C10–C15) проходит в отдельном усиленном CI.

## Контрпроверки и неустранимые ограничения

1. Попытка запустить расширенную CI 184 тестов при правке workflow временно создала испорченный YAML. В GitHub [run 38935360031](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/38935360031) **FAIL ДО тестов**, исходные ZIP или цена не признаны неправильными. Workflow переписан корректным целиком, затем повторно запущены 184 теста и все 20 ZIP. История FAIL/исправления сохраняется, нельзя подменить успешными ранними запусками.
2. **2 дня истории недостаточно** для независимого авторского определения 1D HTF POI, StrongHL, структура Order Flow, FTA, SL, полноценный контекст маршрутов 1D→4H→1H. У данного цикла нет алгоритма самостоятельного author-level recognition.
3. Результат **не утверждает** наличие оригинальных native Binance 1H, 4H или 1D ZIP, даже если Decimal OHLCV совпадает при агрегировании. Native источник — 15m и 5m; 1H/4H/1D производные.
4. Предыдущие source-v05 pivots 2+2 и 24H raid freshness всё ещё инженерные допущения. Двойная source-stream parity не создаёт академический gold label: 0 author-certified VC, StrongHL, entry, PnL и ордеров.
5. Binance Vision TLS+same-host CHECKSUM обеспечивает source/integrity контроль внутри одного origin, но **не** цифровую подпись от независимой третьей стороны. Freeze original C08 315 archives, F06, C13, C14, SMOKE/V5/QFVG остаётся неизменным.

**Следующий шаг:** добавить достаточный многодневный/многонедельный original Futures 15m/1D lookback и затем проверять независимо HTF POI, контакты и авторские подтверждения 4H/1H/15m/5m. При отсутствии качественной авторской разметки должен возвращаться явный `AUTHOR_GOLDEN_SOURCE_UNAVAILABLE`, а не торговый вход. PAPER ONLY.
