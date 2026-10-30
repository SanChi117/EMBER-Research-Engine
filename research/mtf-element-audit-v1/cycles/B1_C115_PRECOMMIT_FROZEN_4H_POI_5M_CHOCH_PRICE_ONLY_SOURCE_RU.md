# C115 / PRECOMMIT — независимая репликация C114 price-only, без подгонки торговых правил

Дата: 2026-10-30 UTC. Новый источник семьи, новое семейство проверки источников, **не** исправление C114 по просмотренным outcome. PAPER ONLY. Создан до запроса новых архивов по указанным периодам.

## Причина

C114 A177 SOURCE_BLOCKED до расчёта сделок из-за объёмов между оригинальными Binance 3m и 5m. Независимая C114-F A178 проверка выявила в BNB 2025-01-14T13:30 UTC оригинальный base volume 24700.27 (1m/3m), 31675.04 (5m/15m), 35790.57 (aggTrades), причём original daily и monthly для каждого интервала совпали по всем 96 OHLC и объёмам. Нельзя назначать правильный volume по предпочтению алгоритма.

В торговой гипотезе C114 **вообще нет объёмного фильтра или использования base/taker volume для решений**. Адаптация касается только source-acceptance и должна быть проверена на новом периоде.

## ЕДИНСТВЕННАЯ перемена относительно C114

**C114 trading/scoring engine SHA256 до рефакторинга:**
`36d677166f4091f2ce66084dfb75f2407c72cbf735483cb3ee584a687ba41e6f`
(файл `d05/c114_independent_poi_native5m_choch_research.py`; нельзя его менять).

Для каждого оригинального Binance USD-M 3m+5m ZIP:
- Архивы 3m и 5m **независимые**, проверенные с оригинальным Binance provider .CHECKSUM, SHA ZIP+CSV, без синтетического 5m из 3m;
- строго 480 native3m + 288 native5m свечей/день, UTC-contiguous, no gaps/duplicates;
- каждые 15m OHLC и timestamp из 5 native3m свечей должны **СТРОГО** равняться OHLC и timestamp из 3 independent native5m свечей. Любое отличие — `SOURCE_BLOCKED`, никакой PnL;
- base volume обязан быть finite and nonnegative как прежде, но расхождение между TF теперь **диагностика без порога допуска**: количество конфликтных 15m bucket, максимальное relative drift, примеры и source receipts без изменения OHLC.
- При обнаружении gap/невалидного checksum/несовпадения цены НЕ переключать источник на monthly, lower TF, API в обход проверки. Никаких задних исправлений/цены из большинства.

Ни 1m, ни aggTrades **не** являются третьим сигналом, объёмом, фильтром или торговым input. Данные C114 A177/A178 используются только для обоснования **источниковой** гипотезы, никаких C115 outcome на них не вычисляется.

## Новые заранее выбранные окна (вне C109–C114 тестов)

Список из тех же 12 USD-M пар BNB/XLM/HBAR/INJ/OP/ALGO/CHZ/ICP/SEI/PENDLE/LINK/UNI:
- **WIN_A** 2023-09-01T00:00:00Z .. 2023-10-27T00:00:00Z exclusive, 56 полных дней.
- **WIN_B** 2023-11-01T00:00:00Z .. 2023-12-27T00:00:00Z exclusive, 56 полных дней.

На каждый период 672 проверенных native3m ZIP + 672 проверенных native5m ZIP (общая сумма 2688 ZIP; 645120 оригинальных 3m и 387072 оригинальных 5m свечей за оба окна). 7 суток warmup, 54 часа embargo (6h landmark+48h hold); 28-й день temporal fold. Если какой-либо символ не существовал, unavailable ZIP, gaps/price mismatch — SOURCE_BLOCKED. **Нельзя** заменить дату или пару ради n.

## Замороженный торговый механизм

**Вся стратегия, matching, costs и статистический gate целиком берутся из C114 без изменений**:
1D structure = report only; parent 4H FVG POI = первые 3 полностью закрытые 4H свечи, first physical native3m touch ≤48h. 5m CHoCH требует полностью известные pre-touch 2L2R lower highs/lower lows или higher highs/higher lows и подтверждение закрытым native5m close, не wick. После общего 6h landmark обе группы CHoCH/NO_CHoCH входят на следующем original native3m OPEN, same-asof 4H SL/TP, max 48h, stop-first и model friction 14/25/40bps, matched controls без outcomes, ITT непрошедшие, matched block bootstrap 2000 / seed 11420261030; 1% starting paper equity risk. NO LOOKAHEAD. Ни 15m OB после просмотра outcomes, ни фильтры 1D направления, ни фиксированные цели R:R. Ledger включает all first-touch, treated, controls, early competing, pairs, source-not-known и no-trades.

Оригинальная C114 модель признаёт некоторые ранние competing события, что может приводить к NO_POWER; расширять условие CHoCH, искусственно создавать пары или исключать unfilled/early events ради улучшения метрик нельзя.

## Бинарный gate, тот же C114

Каждый период: минимум 40 matched T/C pairs, ранняя и поздняя половина ≥10 пар каждая; matched T netR25>0, PF25>1.2, PF40>1.1, average netR25(T−C)>0 и нижняя 95% block-bootstrap граница >0, TP-before-SL T > C включая обе temporal folds, консервативный 1%-per-fill adverse-wick portfolio DD <10%. Все условия должны быть выполнены **на каждом** окне. Недобор N = NO_POWER без смягчения. Историческое PASS ≠ доказательство причинности и ≠ LIVE APPROVAL: максимум отдельный prospective PAPER.

## Реализация и обязательные контрпроверки

1. Новый source-acceptance contract как отдельный C115 wrapper (оригинальный C114 engine неизменяем) + 8+ adversarial no-peeking/source/volume tests на Py3.10–3.12;
2. При строгом оригинальном source PASS — полноценный replay двух этих окон без ручного выбора сделок;
3. SHA receipts всех 2688 ZIP, полные исходные события/контроли и бинарный verdict; без сырого ZIP коммита допускается только sha/source+CSV manifest;
4. Запись A179 только **после** реальной обработки и независимого countercheck; при блокировке record BLOCKED, а не выдуманная экономика.

C115 пока не имеет экономического результата. **LIVE BLOCKED безусловно.**
