# A221 — широкий семантический отбор оригинальных стратегий + независимый Binance USD-M тест

**Дата:** 31.10.2026. **Мандат неизменен:** `main/RESEARCH_MANDATE_LOCKED.md`, только стратегии Binance USDT-M Futures. Запрещённые пользователем A220 C1/C2/C3 **не тестировались**. Прежние A188–A219 negative/blocked preserved.

## Масштаб реально сделанного за цикл

- **23 записи** в машинном источниковом реестре (из них **17 новых проверенных по доступности и релевантности публичных оригиналов / инструментов**, остальные — зафиксированные отказы и вето прошлых циклов). Подробно: `A221_SOURCE_SCREEN_23_REPOS_MACHINE.json`.
- **Один** оригинальный механизм прошёл исследовательский полноценный прогон на реальном Binance Futures рынке: **TSMOM (настоящие 204 месячных ZIP price + funding)**, 3 отдельные исторические окна, 2 денежных издержечных модели, исходный авторский TSMOM код SHA pinned.
- **18** prefix-tests по трём монетам × шести хронологическим отсечениям без изменений прежних сигналов (`CI PASS`).
- **Один** независимый отрицательный *операционный* контроль оригинальных live risk-ограничителей, с сохранённым кодом/доказательствами.
- У остальных 16 новых репозиториев **не было оснований расходовать реальные futures backtest ресурсы**: нереплицируемый исходник, подмена торгового рынка, риск или заведомый невалидный расчёт; эти отказы не называются «экономически убыточными» без теста.

## Источник, который выглядел сильнее остальных — TSMOM

[Оригинал](https://github.com/yongzhe2160cs/trading-engine/tree/efa37deac60fb9d91abcb181440c94f2f0eac4b8), исходники `strategy/tsmom.py` blob `af7d999ff114a872df6bfe65fb5376577451021b`, `config/settings.py` blob `579df537946b20ce2c8ca55d4a8ab47629b769ba`, параметры original deploy `720h/336h/20% vol/1x cap/daily rebalance`. Реальные BTC/ETH/SOL USD-M; истинные fundingRate settlement, 204 ZIP verified SHA против A217, 3 отдельных $3000 portfolio years. Программная CI-проверка и полные поступления: [run 41224708395](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41224708395).

### Проверка без live risk-контуров — **не исполнимый результат**

| Год | BASE % | STRESS % | MaxDD STRESS % |
|---|---:|---:|---:|
| 2024 | +1.75 | −0.91 | −16.53 |
| 2025 | +17.46 | +14.01 | −12.86 |
| 2026 Jan–Sep | +12.41 | +8.66 | −13.14 |

Позволяла назвать `PRELIMINARY 2/3`, но источник позднее показал обязательные live safety gates. **Историческая кривая без них не является live parity.**

### Тест без изменения сигналов с оригинальными ограничителями риска

Из `config/settings.py` документированы `max_daily_loss=0.03`, `max_total_dd=0.10`, `RISK=RiskParams()`; [оригинальный RiskManager](https://github.com/yongzhe2160cs/trading-engine/blob/efa37deac60fb9d91abcb181440c94f2f0eac4b8/risk/manager.py) blob `398b5280d123120027f54be85ae80b22e16e9da5` при нарушении **латчит `_halted`**; [оригинальный daemon](https://github.com/yongzhe2160cs/trading-engine/blob/efa37deac60fb9d91abcb181440c94f2f0eac4b8/live/tsmom_daemon.py) blob `f19895a124328cd52ba8232d3a6c5cc9f29e8e10` gates all rebalances. В независимом модельном 1h risk shadow после нарушения переводим счёт в cash до разрешения оператора; flatten cost положителен. Это **не** идентичный live path (там poll mid-window, реальные спреды, ликвидация); знак и наличие нарушения доказаны на модельной линии, а точность конкретных fills не гарантирована.

| Период | BASE с остановкой | STRESS с остановкой | Первая остановка BASE |
|---|---:|---:|---|
| 2024 | **+0.97%** | **−7.76%** | 11 июня, дневной −3% |
| 2025 | **−2.04%** | **−2.66%** | 2 марта, дневной −3% |
| 2026 Jan–Sep | **−9.95%** | **−9.85%** | 29 января, DD >10% |

Оригинальный trade-live при такой остановке не продолжал бы получать прибыль оставшейся части каждого года, пока оператор не возобновит. **Гейт стратегии `REJECT_OPERATIONAL_RISK_GATE_PARITY`**. Не менять лимиты на просмотренной истории, не «воскрешать» год после стопа без реального restart-protocol и не именовать `VERIFIED`.

**Доказательства:** `A221_TSMOM_204_BINANCE_MONTHS_VERIFIED_RESULTS.json` (неограниченная кривая), `A221_ORIGINAL_RISK_BREAKERS_NEGATIVE_VERIFIED.json`, machine replay script и pinned original sources, CI SHA artifact.

## Остальные репозитории: «по смыслу», без рекламы

| Источник | Механизм | Решение |
|---|---|---|
| [OctopusTakopi/crypto-trend-following](https://github.com/OctopusTakopi/crypto-trend-following) | 788-contract CTA trend, long+short | Оригинал полноценнее других (actual perps/funding, point-in-time); но средний 143-контрактный portfolio, $100k baseline, net Sharpe 1.04, DD −30.1%, нет margin/liquidation полной модели. **Отложен, не второй независимый механизм** относительно TSMOM |
| [fortunato/pymarket-structure](https://github.com/fortunato/pymarket-structure) | 4h zones / wave retest | +70.32% авторский пример, но **нет оригинального source самой Freqtrade стратегии**; материал только trade JSON/4h candles, params прямо curve-fit; экономически не проверял |
| [MG-Trading-Terminal/trading-strategy](https://github.com/MG-Trading-Terminal/trading-strategy) | OI/позиционирование толпы | Документы без исполнимой оригинальной стратегии; собственный честный OOS «barrel» снизился до +0.08%/сделку prefees, ниже условного breakeven, ранние красивые цифры опровергнуты |
| [MiltonTulli/trading-bot](https://github.com/MiltonTulli/trading-bot) | BTC breakout+volume | Автор признаёт SAME-CLOSE fill/lookahead, funding/slippage не в PnL, 3240+ проверенных конфигураций; заголовок «$10k->$229k» **не верифицирован** |
| [Adeline117/Strategy-project](https://github.com/Adeline117/Strategy-project) | Контртренд по funding zscore | В историческом OOS 2021/22 минус, сильная зависимость от режима и оптимизированных параметров |
| [DylanSiegel/GO-Microstructures](https://github.com/DylanSiegel/GO-Microstructures) | Hawkes order-flow, aggTrades Futures | Код потока и моделей есть, но нет полноценного послеиздержечного portfolio fills/queue, повторяет часть исследовательских источников A207; **не готовая стратегия** |
| [tsuithomas/crypto_research_order_book_imbalance](https://github.com/tsuithomas/crypto_research_order_book_imbalance) | L2 order-book microprice | Вывод сильно зависит от предположений о maker/limit fills, без проверенного исторического orderbook FIFO/очереди нельзя измерить реализуемый edge |
| [mamipour/lead-lag-trader](https://github.com/mamipour/lead-lag-trader) | Межмонетная реакция | Основная эмпирика Kraken Futures и DD −47%; не наш USD-M оригинал |
| [xujaan/futurabot](https://github.com/xujaan/futurabot) | Комплекс SMC/OBI/CVD/VPIN + runner | Много эвристик без достаточного оригинального независимого USD-M OOS journal; не тратить время на «добавим ещё индикаторы» |
| [bockuden/crypto-cointegration-research](https://github.com/bockuden/crypto-cointegration-research) | Spot/perp basis | У автора тяжёлый отрицательный послеиздержечный результат; близко к A212/213, не новая независимая идея |
| [SebastianBoehler/MarketTensor](https://github.com/SebastianBoehler/MarketTensor) | ML-regime и OHLCV+OI | Историческое Sharpe лучшей ML стратегии всего 0.0828 против 0.0822 для majority baseline — нет полезной разницы |
| [freqtrade/freqtrade-strategies/VolatilitySystem](https://github.com/freqtrade/freqtrade-strategies/blob/main/user_data/strategies/futures/VolatilitySystem.py) | 1h ATR shock, 2x futures | Настоящий original SHORT/LONG, но stoploss=−1 (100% цены), разрешённый DCA stake и 2×; блок по tail risk до дорогого теста |
| [PVinh-Quant/Kairos-v2](https://github.com/PVinh-Quant/Kairos-v2), [zabor-crypto/zaBor](https://github.com/zabor-crypto/zaBor) | Исследовательские инфраструктуры | Предназначены для анализа и управления риском, **не готовые independently profitable original стратегии** |
| [Superjojo74/nautilus-perp-funding](https://github.com/Superjojo74/nautilus-perp-funding) | Funding settlement addon NautilusTrader | Инженерно полезная библиотека, **не стратегия**; может помочь будущему testing QA |
| [younghwan91/quantbox-engine](https://github.com/younghwan91/quantbox-engine) | Фьючерсный тестер | GitHub исходник не доступен по найденному названию, без доверенного SHA не использовать |
| [juriok/chart-pattern-backtester](https://github.com/juriok/chart-pattern-backtester) | Формации 4h | Отброшен в A219 как SPOT-data disguised as Futures |
| [Kureshi25/cryptobot](https://github.com/Kureshi25/cryptobot) | Donchian | A211 настоящие USD-M native отрицательные |
| [MirrorNew/2026DoubleMaFuturesStrategy](https://github.com/MirrorNew/2026DoubleMaFuturesStrategy) | Double MA | A188–A197 native causal & robustness gates fail; **не повторять** |
| Три A220 user-veto | XS momentum, funding level carry, post-pump short | **Прямой запрет на дальнейшие тесты**, не пересматривать |

В эту таблицу вошли и архивные источники, поэтому **отдельно настоящих экономических прогонов в A221 был только один**, а не 17 и не 23. Результаты доступны исходным кодом и подтверждённым CI.

## Итог

- **0 VERIFIED_FUTURES_CANDIDATES.**
- A221 TSMOM: исторический net после real funding восстановлен, тест source causality 18/18, но **live parity with hard halt FAILED**, поэтому **не продвигать**.
- CTA с 788 монетами: source-only / отложен, потому что не дает нужного нового независимого семейства и имеет крупные ограничения/просадку.
- Остальные: явный source blocker, риск, уже отрицательный опыт или просто отсутствие исполнимой стратегии; **не представлять как экономически проигравшие** там, где этого не проверяли.

**Следующая независимая гипотеза должна иметь исходный метод, которого не было в A188–A221, и доказательства экономической причинности.** Отдельных новых PAPER или реальных ордеров и изменений планировщиков нет. Мандат `main/RESEARCH_MANDATE_LOCKED.md` действует без изменений.
