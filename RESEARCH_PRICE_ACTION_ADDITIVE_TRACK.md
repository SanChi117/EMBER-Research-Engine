# Price Action — дополнительная линия исследования (2026-10-31)

**Неизменный мандат:** [RESEARCH_MANDATE_LOCKED.md](RESEARCH_MANDATE_LOCKED.md).

По прямому поручению пользователя Price Action добавлен в общий поиск торговых стратегий; предыдущие фильтры и параллельные направления **не отменяются**.

Предмет: готовые открытые модели Binance USDT-M Futures с наблюдаемой структурой — sweep/reclaim/BOS, пробой и ретест уровня, реакция на заранее зафиксированную зону, сжатие диапазона и выход из него.

Для любой модели остаются обязательными причинность событий без перерисовки, независимая проверка оригинала, реальные Binance USD-M данные, полный учёт расходов и funding, исполнение, структурный риск, просадка, устойчивость и нетронутая OOS/forward проверка. Красивые сигналы и бэктест на той же закрывающейся свече не являются подтверждённой прибылью.

Сохраняется отказ от трёх источников A220: [RESEARCH_USER_VETO_A220.md](RESEARCH_USER_VETO_A220.md).

[Результат A222 — аудит восьми исходников](https://github.com/SanChi117/EMBER-Research-Engine/blob/research/a222-price-action-source-first-locked-mandate-20261031/research/a222_price_action/A222_PRICE_ACTION_8_ORIGINAL_SOURCE_SEMANTIC_SCREEN_RU.md).

Изменений PAPER-планировщиков и реальных сделок нет.
## A223 — продолжение и независимый отказ источника (31.10.2026)

[Аудит двенадцати новых оригиналов](https://github.com/SanChi117/EMBER-Research-Engine/blob/research/a223-price-action-structural-retest-independent-source-audit-20261031/research/a223_price_action/A223_TWELVE_ORIGINAL_SOURCE_SCREEN_AND_GATES_RU.md). На 35 подлинных SHA-проверенных Binance USD-M BTCUSDT 1h месячных архивах исходный код `denniskid2520/btcusdt-research-archive` выдал 59 из 59 базовых входов в зону 4H RSI до закрытия определяющей 4H свечи: 2024 28/28; 2025 18/18; 2026 Jan–Sep 13/13. [Проверенный CI](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41226851100). Значит источник не проходит causality gate — его авторский 6-летний PnL не становится VERIFIED. Это не доказанная экономика этих 59 входов и не утверждение о реализации отдельного production-бота.

Найдены дополнительные проблемы источников: Spot-данные вместо perp, отсутствие структурного стопа, stop-price с исполнением по закрытию следующей свечи и положительные отчёты с lookahead. Пока **0 подтверждённых прибыльных Futures стратегий**. Мандат поиска всех других механизмов и вето A220 неизменны.
