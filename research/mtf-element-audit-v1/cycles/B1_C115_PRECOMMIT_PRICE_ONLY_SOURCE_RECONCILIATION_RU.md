# C115 — source-only rerun C114 без изменения торговой гипотезы

2026-10-30, перед любым экономическим результатом. Только PAPER. Предыдущий C114 = SOURCE_BLOCKED, A177 immutable SHA journal, 22.01977% несогласие 15m volume BNBUSDT 2025-01-14. Не C109 rescue, не новая пороговая оптимизация.

## Исследование

Это контролируемая повторная попытка провести уже предрегистрированный C114 4H FVG first touch -> подтверждённый 5m 2L2R structural CHoCH, по source-логике для PRICE ONLY. Исполнение/стоп/цель/контрольные пары/бустрап все 1:1 из B1_C114_PRECOMMIT_INDEPENDENT_4H_POI_5M_REACTION_PREDICTIVE_VALUE_RU.md и замороженного C114 исходника. Котировки с 2025-01 и 2026-02 уже были запрошены в C114 на уровне source; следовательно НЕ ПОЛНОСТЬЮ BLIND. Однако в C114 не был произведён ни один calculation signal/TP/SL/PnL, поэтому экономические outcome не использовались для изменения правил C115.

Остаются прежние два окна по 56 дней, 12 монет, 2688 оригинальных ZIP:
2025-01-01 .. 2025-02-26 exclusive; 2026-02-01 .. 2026-03-29 exclusive. Периоды нельзя менять, увидев сделки. Bootstrap 2000, seed 11420261030, matched symbol-week blocks.

## Единственный исправляемый дефект source qualification

В C114 был добавлен некорректный для PRICE-ONLY стратегии дополнительный source gate: интервал 15m должен иметь одинаковый суммарный объём в Binance 3m и 5m ZIP до 0.01%. Оба официальных SHA/CHECKSUM-verified интервала на одной 15m свече имели 22.02% разницу, хотя OHLC совпали.

В C115: для каждой 15m группы из пяти оригинальных native3m и трёх оригинальных native5m:
1. STRICT OHLC open/high/low/close и UTC start/end совпадают точно (Decimal). Любое несовпадение => SOURCE_BLOCKED, даже 1 тик.
2. Обе независимые daily ZIP проверены по Binance provider CHECKSUM и raw CSV + ZIP SHA; ровно 480 original 3m / 288 original 5m свечей/день, без пропусков/дублей.
3. Volume не является источником ни одного сигнала, отказа, входа, SL, TP или подборного коэффициента, поэтому несовпадение объёма не должно останавливать PRICE-ONLY проверку. Любой volume drift НЕ СКРЫВАТЬ: число несовпадающих 15m buckets, max relative/absolute, число >1bp и общее число проверенных. Volume-dependent стратегии по этим данным НЕ допускаются до отдельного аудита.
4. Отдельный негативный тест: изменение synthetic volume при неизменном OHLC не меняет price signals. Price divergence, таймстампы или SHA => SOURCE_BLOCKED, без фолбэков.

## Экономический критерий — НЕ меняется

В каждом периоде matched T-C pairs >=40 и >=10 early/late, T 25bps netR>0/PF>1.2; 40bps PF>1.1; matched delta 25bps bootstrap 95% lower>0; TP-before-4H-SL superiority across both halves; conservative 1% starting-equity risk DD<10%; explicit ITT early competing and unmatched; без новых фильтров. N<40 => NO_POWER; иные провалы => FAIL. Даже положительный результат означает historical exploratory screen, НЕ prospective forward OOS, LIVE BLOCKED.

## Антиподгонка

Исходный C114 strict 1bp-source verdict и A177 сохранены и НЕ изменяются. В новой ветке research/c115-price-only-source-reconciliation-20261030 source function подменяется лишь для проверки exact OHLC и регистрации объёма; исходная C114 entry/execution logic, окна, пороги и статистика не изменяются и C114 исходник сохраняется нетронутым. Любые новые диагностические исправления фиксируются отдельными SHA.
