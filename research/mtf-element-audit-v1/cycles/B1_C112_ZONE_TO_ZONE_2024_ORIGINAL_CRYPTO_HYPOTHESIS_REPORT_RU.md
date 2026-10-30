# C112 — «движение цены от зоны к зоне» проверено на оригинальных криптосвечах; гипотеза не дала устойчивого преимущества
**2026-10-30. PAPER ONLY.** Юзер: «рынок движеться от зоны к зоне с подтвержденной реакцией в ту или инную сторону». Речь о вероятностной гипотезе, не о бесспорном законе.

## 1. Указанная пользователем модель и фактический разрыв с C109
В изначальных C105–C111 TP обычно привязан к ближайшему заранее известному, не снятому 4H **swing pivot экстремуму FTA**, но это уровень, не обязательно встречная торговая **зона**. Поэтому даже положительный C109 по отдельному месяцу не доказывал «цена идёт из FVG к FVG». Мы исследовали именно ближайшую **заранее существовавшую и ещё ни разу физически не тестированную ВСТРЕЧНУЮ 4H FVG**: для LONG это bearish supply gap выше входа с ближайшей границей lower; для SHORT — bullish demand gap ниже входа с ближайшей границей upper. Это **конкретная программная операционализация** слов пользователя, а не единственная возможная зона; другие SNR/OB нельзя без источников выдавать за FVG.

**Precommit до 2024 raw data**: `cycles/B1_C112_PRECOMMIT_ZONE_TO_ZONE_CORE_FVG_DESTINATION_HYPOTHESIS_RU.md`. Та же **неизменная версия C109** (SHA256 `39bf28a44cec0356b256853514c532b8f37be48f3da3477a365bd19c4add5557`) рождает 4H родительскую FVG, первое закрытое15m касание, закрытую H1 реакцию с выходом за весь gap, 15m preconfirmed swing BOS/3bar IMB, потом original native3m next OPEN. **SL в обеих сравниваемых моделях НЕ ИЗМЕНЁН**, это original parent 4H FVG far edge ±0.15 H4 ATR14, native3m wick/gap hard stop. Комиссии+slippage roundtrip модель14/25/40bps,48h max hold, stop-first ambiguous original3m. 
Цель А = исходный nearest unconsumed confirmed 4H pivot FTA ± original ATR padding; цель Б = near edge ближайшей *preknown never-touched opposing H4 FVG* ± same 0.15 ATR padding. B target only if derived original 4H RR≥1.25, no invented fixed RR. **А и Б сравниваются парно на одних и тех же admitted C109 trade entry**; если нет Б, никакая придуманная зона не подставляется и исходный A не перезаписывается. Историческая остановка/прибыль Б смоделирована оригинальным unchanged 3m stop-first simulator `c105_parent4h_structural_geometry.simulate`, не абстрактным H4 OHLC.

## 2. Новый независимый исходный источник
ДВА 64day исторических окна (НЕ участвовали в C105–C111):
**WIN_A 2024-07-01..2024-09-02**, **WIN_B 2024-10-01..2024-12-03** UTC inclusive (end 2024-09-03 и 2024-12-04 exclusive), 12 заранее выбранных Binance USD-M crypto `BNB,XLM,HBAR,INJ,OP,ALGO,CHZ,ICP,SEI,PENDLE,LINK,UNI` USDT.
**1536** настоящих original Binance Vision USD-M daily native3m ZIP, каждая provider .CHECKSUM, ZIP SHA + CSV SHA, все **737280** оригинальных3m OHLC, без искусственной подстановки отсутствующих дней, 7д warmup+48ч terminal embargo. 4H/FVG строятся исключительно из fully closed original3m. Входы historical paper, actual live fills NONE.
SHA evidence:
- `evidence/c112/C112_WIN_A_ZONE_TO_ZONE_ORIGINAL_768_ZIPS.json` **741249 bytes, SHA `9d6a82a878dda72ee248c260398c7140771014930119ad6600cc9c3a4469e67f`**
- `evidence/c112/C112_WIN_B_ZONE_TO_ZONE_ORIGINAL_768_ZIPS.json` **491791 bytes, SHA `8df88f6335f09d7725353d3276c31fdb67a593beb303cab7e038b43c3a978184`**
- `evidence/c112/C112_TWO_WINDOWS_SUMMARY.json` **5225 bytes, SHA `37509564c0accdd2eaee1cbae912d07a4907377fa5d0b3f1231abdf19daa7a9a`**

## 3. Проверка наличия и фактического достижения следующей зоны
| Факт | WIN_A | WIN_B | Совокупно |
|---|---:|---:|---:|
| Все изначальные C109 B1 PAPER входы | 81 | 45 | 126 |
| Заранее известна хотя бы одна свежая встречная 4H FVG | 52 | 15 | 67 (53.2% исходных входов) |
| Цена физически пересекла её ближнюю границу в исходные 48ч после входа (даже после стопа!) | 20/52 (38.5%) | 8/15 (53.3%) | **28/67 (41.8%)** |
| Такая цель подходит по исходной структуре SL и RR≥1.25 |42|10|52|
| Физический 3m TP до SL у этих альтернативных 4H FVG сделок |8/42|1/10|**9/52 (17.3%)**|

Фраза **«сырое достижение зоны»** отличается от прибыли: `unconditioned_first_visit` отдельно продолжает наблюдать источник 48 часов, даже если реальный стоп или исходный 4H TP сработал ранее. Поэтому 28/67 никогда не интерпретировать как реальные 28 выигрышей. Реальных 3m TP-before-SL **9/52** на допустимых альтернативных сделках, остальные STOP/TIMEOUT.

## 4. ПАРНЫЙ экономический исход при 25 bps на ИДЕНТИЧНЫХ входах
| 25bps, original crypto | WIN_A июль–сентябрь 2024 | WIN_B октябрь–декабрь 2024 |
|---|---:|---:|
| Полный C109 4H pivot baseline (все входы) | n81 **+31.893675R**, PF1.58203, DD12.22786% | n45 **+6.630285R**, PF1.20990, DD8.48262% |
| Pivot FTA на **только парном доступном** подмножестве | n42 **+15.867690R**, PF1.48078, DD10.26263% | n10 **+2.215300R**, PF1.22190, DD6.70805% |
| Opposing fresh 4H FVG на том ЖЕ подмножестве | n42 **+26.971843R**, PF1.76554, DD15.77426% | n10 **−9.180549R**, PF0.19292, DD9.20359% |
| Opposing FVG при40bps | n42 **+20.934272R**, PF1.52693 | n10 **−10.670783R**, PF0.16635 |
| Opposing FVG target TP-first / stop / timeout |8 TP, 27 STOP,7 timeout|1 TP,9 STOP,0 timeout|

**На WIN_A FVG destination математически даёт больше netR, но переносит более высокий tail risk и больший DD 15.77% (превышение первоначального предобъявленного ограничения <10%). В WIN_B та же точная гипотеза проигрывает −9.18R на n10, хуже исходной 4H pivot FTA цели.** Пререгистрированный экономический admission FAIL в обоих окнах: WIN_A ранний n9<10 и DD>=10, WIN_B n10<30, ранний n3<10, отрицательный NetR25 и PF25/40 низкие.

**Важная интерпретация**: не доказано, что «переход из зоны в зону» не существует, потому что FVG — только один тип зоны, 48 часов и точный never-touched veto могут исключить большинство настоящих структурных перемещений. Но **в том смысле, в каком мы сделали гипотезу исполнимым правилом на 4H**, нет устойчивой прибыльности и нет оснований менять оригинальный TP с 4H pivot на встречную FVG во всех сделках.

## 5. Проверка инженеринга и источников
- `d05/c112_zone_to_zone_fvg_destination_audit.py` sidecar only. Никакой имитации 1D/4H lookahead; FVG источник — три уже **закрытые** 4H свечи до original next3m entry, зона never previously touched по оригинальным 3m high/low. Никакого «отбор лучшего TP после результата»: nearest opposite fresh price band selected before next3m start.
- `d05/test_c112_original_4h_zone_to_zone_first_passage.py`: 20 новых негативных тестов и 789 оригинальных предыдущих tests ×Python3.10/3.11/3.12 = **2427 PASS**, [GitHub original source CI 41090551989](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41090551989) **SUCCESS4/4**. Два первых красных CI относились к синтетической 4H фикстуре, включавшей ещё не закрытый H4 бар на момент synthetic3m entry, исправлено ТОЛЬКО в тестах до доступа к новым source price, что защищает от future leak. C109, C105, старые SHA unchanged.
- Owner source academic values: 4H zone, reaction and need coherent dealing range. Distinguish our operationalization from exact original author-golden. Public [GitHub joshyattridge/smart-money-concepts](https://github.com/joshyattridge/smart-money-concepts) identifies FVG/mitigation and BOS/pivot as distinct structures. [TradingView Pine docs repainting](https://www.tradingview.com/pine-script-docs/concepts/repainting/) require no unconfirmed future HTF fields; audit uses historical closed native3m aggregate rather than `security(...lookahead_on)`. These references support semantics, NOT market edge.

## 6. Решение для EMBER
**C112 FVG-to-FVG destination НЕ ДОПУЩЕН в production / auto-futures**, не заменить оригинальный C109 TP, не расширять стоп или снижать порог admission под 2024 outcomes. Ещё более важный результат: свойство «цена доходит до зоны» и свойство «можно систематически заработать на этом событии после подтверждения и риска» — разные утверждения. Для них нужен отдельный тест:
1. Нарисовать заранее известную **структурную карту 4H**: FVG, подтверждённые 4H swing зоны и SNR только при точных source-contract (не любой pivot объявлять зоной). Сначала проверить **same dealing range** и time-stamped formation lifecycle, а не менять TP вслепую.
2. Провести **условное сравнение confirmed reaction vs first-touch WITHOUT confirmed reaction** с совпадающим ticker/year, native3m risk horizon, D1/W1 source conditions, заранее заданными baseline controls; без этого C112 не доказывает даже incremental predictive value реакции.
3. Для C113 предзарегистрировать новые source windows, честные bps и не выбирать только удачные предыдущие 2024 годы. If no conditional advantage: NO_TRADE.
