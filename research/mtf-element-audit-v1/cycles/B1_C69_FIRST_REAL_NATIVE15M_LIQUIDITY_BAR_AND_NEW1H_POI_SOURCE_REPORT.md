# C69 — первая исходная 15m-свеча снятия ликвидности внутри 1H; первый source-тест NEW 1H POI

Дата: 25.10.2026. Binance USD-M crypto **PAPER ONLY / NOT_TRADE_READY**. Репозиторий `SanChi117/EMBER-Research-Engine`, ветка `research/academic-engine-recovery-20261015`.

### Академия

Непосредственно прочитаны `Strong High & Low.txt` (Drive ID `1lvPRbhfM6ZjfW7UP-30y9uND1R6VC13t`), `Order Flow.txt` (`1r6sH0XjEoK4Jwq4EVLz8vqPSWVh9qerN`), `POI.txt` (`1C5sAzdOON4iMxLVdrBD5XMXUj3bVcZ-R`). Настоящий StrongHL требует реального контакта с ликвидностью **ИЛИ** неэффективностью **ЗАТЕМ** движения с формированием авторской VC POI **ИЛИ** BOS на том же либо младшем TF. Для настоящего OF одновременно обязательна работа с ликвидностью **И** IMB. Сами технические wick, swing и IMB **не авторские goldens**, не дают валидности POI/SL/TP.

### Выполнено

- `d05/c69_exact_native15m_first_liquidity_raid_vs_poi_test.py`: вместо C68 proxy «последняя 15m свеча 1H raid» восстанавливает полный **4× оригинальный native15m OHLCV Decimal + raw ZIP SHA:timestamp**, самостоятельно заново вычисляет все **СТРОГО заранее известные и неснятые** source 1H SSL/BSL, подтверждённые на предыдущих закрытых 1H свечах. Для выбранного C67 1H wick raid проверяет фактический исходный уровень, 1H open/close reclaim и **самую раннюю из четырёх** исходных 15m свечу, чья тень действительно проходит через уровень. Сохраняет **15m body close за уровнем, но 1H recovery**, отдельно от 15m wick-only reclaim. Если первый бар одновременно пересёк несколько preknown уровней — **AMBIGUOUS**, не назначает выгодный level.
- Для `NEW_1H_VC_POI` сохраняет ранее фактически первый native15m wick intersection только **после полного закрытия исходного 1H контекстного события**, проверяет, что ID действительно первый среди всех исходных native15m. Но этот источник **НЕ является авторским первым VALID POI test**. Все author flags false. Route B IDM/Route C raid→BOS не смешаны; 0 SL/TP/orders.
- `d05/test_c69_exact_native15m_first_liquidity_raid_vs_poi_test.py`: **30** adversarial тестов × 3.10/3.11/3.12, original 1H Decimal aggregation parity, first15m can be second or first in hour, 15m body vs 1H reclaim, several simultaneously raided levels, false owner POI/StrongHL, forged SHA/time/mixed symbol, historical source gate. [CI 40222310507](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40222310507) **SUCCESS 3/3**.
- `tests/probe_c69_original45zip_exact_first_native15m_raid_poi.py`: fresh authenticated original Binance USDT-M **45 SHA-verified signed ZIP BTC/ETH/SOL/XRP/BCH** Sep1–Oct2 2026: **76800 native3m, 15360 native15m, 160 native1d, 3840 derived1h**. Все **153** C46→C60→C62→C63→C66→C67→C68 original price and raw IDs заново восстановлены и сверены по Git frozen SHA. Первый полный [CI 40222498858](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40222498858) **SUCCESS 5/5**, второй независимо снова скачал все 45 ZIP и сравнил **каждый байт** [CI 40222632285](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40222632285) **SUCCESS 4/4**, 30×3 повторены.
- Полный immutable source `evidence/c69/C69_ORIGINAL45ZIP_FIRST_NATIVE15M_LIQUIDITY_RAID_OR_NEW1H_POI_SOURCE_TEST.json`: **214806 bytes**, SHA256 `ffe2568a1c8384630bed156d94e0dbd4cf89ce6d03ab79ce5946e31ec88fab1c`, Git blob `b22860dfa13e4b19d16e8dd892719a772485e847`. Второй independent `evidence/c69/C69_INDEPENDENT_ORIGINAL45ZIP_PREKNOWN_1H_15M_FIRST_WICK_WITNESS_20261025.json`.

### Результат без подгонки — исходные 153 технических 4H parent contexts

| Источник 15m | Число |
|---|---:|
| Нет однозначной C67 ветки контакта | **92** |
| Претендент 1H wick raid: первая 15m уже возвратилась за уровень до её закрытия | **19** |
| Претендент 1H wick raid: 15m закрылась за уровнем, 1H позже вернулся | **4** |
| Несколько preknown SSL/BSL уровней пересечены одной первой 15m — ambiguity | **3** |
| Первый 15m wick-test предполагаемой новой 1H POI, **не** owner VALID | **35** |
| **Итого** | **153** |

**Нет доказанной авторской POI first valid test, 1H actual trigger, настоящей VC POI/BOS, StrongHL, OrderFlow, FTA/SL/TP. Нет сделок, winrate и PnL.** 3m внутри первой 15m ещё не проверены — следующий **C70**. Оригинальные курсовые примеры — логика, не криптографически сверенные положительные/отрицательные Binance crypto goldens. Их ноль.

### SHA A139

Принимать **после двойного original45 ZIP и 30×3**: шесть новых `SHA256` evidence — C69 module, C69 30 adversarial tests, C69 original45ZIP probe, полный frozen 214806 byte JSON, независимый witness, этот report. Предыдущий A138 tip `c2b93436d2e9990d64501ed4289cd19ebba265bde2ea8b8150e9069d11618d0a`. Добавить A139 ровно один раз, затем independent 139 SHA × Python3.10/3.11/3.12. После этого эти шесть файлов не изменять.

**PAPER ONLY / NOT_TRADE_READY / orders=fills=trades=0.**
