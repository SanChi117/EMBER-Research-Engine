# C108 — минимальная связанная 4H→1H→15m ветка: проверка и отрицательный результат
Дата: 30.10.2026 UTC. **PAPER ONLY, не подтверждена прибыльность.** Заморожено до загрузки нового рыночного периода `cycles/B1_C108_PRECOMMIT_MINIMAL_OWNER_CHILD_FIRST_TEST_NATIVE3M_RU.md`. Не делаем постфактум-селекцию. Статус C108: **ENGINEERING PASS / ECONOMIC SCREEN FAIL / STATISTICAL NO_POWER**.

## Зачем C108 и что именно исправлялось
В C107 доказано, что прежний путь C105 смешивал без связки 4H FVG parent, простую 1H candle-midpoint реакцию и 15m prev-candle-high SNR proxy. Исходный текст `d05/c83_owner_course_text_crosswalk.py` требует `1H_PARENT` (дочерняя 1H POI создана на реакции от 4H POI) и `1H_FIRST_TEST` (новая 1H POI должна пройти первый тест). В C108 разрешён ровно **один уже известный из C91** путь 1H child IMB → first test → 15m direct IMB. Не внедрялся весь LuxAlgo, не добавлялся OB/BOS/CHoCH/EQH/PD, не переименовывался простой 15m previous-high SNR в BOS.

### Режим событий
**Завершённый 1D/1W контекст → завершённая 4H FVG POI → первое завершённое 15m касание parent → новая сформированная только на полностью закрытых 1H свечах согласованная 1H FVG child (с вложенным veto из C91) → физический FIRST_TEST дочерней 1H зоны на последующей завершённой 15m свече → строго после него закрытая 15m FVG IMB same-side → OPEN следующей оригинальной native3m свечи.** В отдельном состоянии каждый parent 4H и уникальный child id, без ретроактивного теста и без подмены. Остальные Route-A ветки не реализованы, поскольку для их 15m SNR / 5m VC нет полного проверенного семантического контракта.

**STOP и TP как прежде:** оба геометрически строятся **от 4H**, SL за дальним краем исходной 4H FVG ±0.15ATR14 4H, TP перед ближайшим подтверждённым 4H pivot ±0.15ATR4H, RR derived gate>=1.25, без искусственной RR-цели. Reuse untouched `c105_parent4h_structural_geometry.parent_plan/simulate`. Исполнимый **protective** SL на оригинальной 3m свечке — это политика ограничения риска; наличие 4H FVG на закрытии H4 — отдельный lifecycle criterion. **Стоп не переносится на 4H close и не расширяется при убытке.**

## Исходная выборка, заморозка
- Historical **2026-08-20 00:00..2026-09-21 00:00 UTC [end exclusive]**, до уже исследованного C105/C106 сентябрь–октябрьского интервала, но исторический earlier period **НЕ** truly prospective future validation.
- 10 заранее выбранных монет: `BNBUSDT, XLMUSDT, HBARUSDT, INJUSDT, OPUSDT, ALGOUSDT, CHZUSDT, ICPUSDT, SEIUSDT, PENDLEUSDT`.
- **320** Binance Vision оригинальных USD-M 3m daily ZIP, каждый same-host `.CHECKSUM`, ZIP SHA256 и CSV SHA256, целые 32 UTC days по480 свечей, **153600** оригинальных native3m candle, 7 полных warmup days, 48h эмбарго на exits, 48h max HOLD; издержки 14/25/40bps.
- Данные source manifest, все реестры отказов, trade geometry и source-time event chain в `evidence/c108/C108_OWNER_LINKED_4H_H1_CHILD_15M_IMB_ORIGINAL_320ZIP.json` **146773 bytes, sha256 `4e11402dcc1a5746601f7cd3efcba4d1bbced6e5044135e158913506b6567eb3`**. Не загружать и не заменять отсутствующие архивы задним числом.
- Исходные C105/C106/C107 source и 41 прежняя PAPER сделка сохранены неизменными, анонимизация результатов не проводилась.

## Реальная частота
| Полностью причинный stage | N across ten pairs |
|---|---:|
| Созданы 4H FVG POI по исходному завершённому D1/W1 | **47** |
| Первый 4H POI TEST | **33** |
| Новые 1H FVG child POI после parent TEST | **14** |
| Первый физический тест дочерней 1H FVG | **9** |
| Direct 15m IMB after 1H child's first test | **5** |
| Родительская 4H геометрия SL/TP/RR допустила сделки | **2** |

Реестры отказов: D1/W1 mismatch 286 кандидатских FVG, parent first touch 8h TTL expiry21, закрытая 4H parent invalidation7, parent 48h expiry10, derived 4H RR below1.25 два, уже занятый PAPER slot один. Они отражают пропуски; НЕ оптимизировались по результатам.

## Экономика PAPER
| Costs roundtrip | Trades | NetR | PF | Modeled DD 1%/trade | Win |
|---|---:|---:|---:|---:|---:|
|14bps|2|**−2.098605R**|0|2.0876%|0%|
|**25bps**|**2**|**−2.176080R**|**0**|2.16424%|0%|
|40bps|2|**−2.281729R**|0|2.26872%|0%|

Две оригинальные PAPER сделки `ALGOUSDT LONG` entry0.099460 SL0.09596175 TP0.10460175 derivedRR1.469806 и `HBARUSDT SHORT` entry0.07515 SL0.07693925 TP0.07219925 derivedRR1.649155; **обе native3m STOP_FIRST_SAME_3M**. Наличие 15m IMB после child first test технически не гарантирует отскок от родительской 4H зоны. Результат не годится для определения стабильности: **n2, early 0 late 2**, все precommitted economic thresholds FAILED, no live readiness.

## Инженерные проверки
`d05/c108_parent_h1_child_first_test_geometry.py`, `d05/c108_owner_child_native3m_paper_research.py`, `d05/test_c108_minimal_owner_h4_h1_child_firsttest.py`.
- **25 новых adversarial tests + 710 старых × Python3.10/3.11/3.12 = 2205/2205 PASS**, CI [40981601983](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40981601983) **4/4 SUCCESS**; strict original native 320 ZIP checksums, evidence 2/2 trade causal parent-child timestamps.
- Первый красный CI [40981524856](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40981524856) выявил только то, что синтетический original source ZIP тест был с дефолтной датой Sep26 при тесте Aug20. Исправлена дата **фикстуры**, а не торговые правила, **до скачивания нового рынка**.
- C105 H4 SL/TP source absolutely SHA-frozen, A170 tip `994ada611359b4ae555dff7ee102bedb531e70a3660a67bab9eb8440706fed45` unchanged.

## Смысл отрицательного результата и следующее ограниченное направление
**C108 доказывает, что одна аккуратно связанная академически предусмотренная ветка воспроизводима на реальных Binance данных, но появляется редко и НЕ показала прибыльность.** Нет основания объявлять, будто C108 полностью восстановил исходный торговый механизм, или будто повышение строгости гарантирует edge. No optimization on n2. Возможные причины малой частоты: только 1H child IMB ветка; запрет вложенной зоны; 8h TTL после 4H touch; только direct15m IMB; 4H FTA and RR gate. **Это не разрешение ослабить параметры:** ещё нужна проверка других **уже предусмотренных источником** альтернатив 1H liquidity raid→15m VC или child→15m trigger→5m VC на независимой заранее зафиксированной sample, и устойчивость по независимым рыночным режимам. 4H SL/TP только структурные, hard risk stop остаётся физически исполнимым. До полноты собственных требований NO TRADE READY.
