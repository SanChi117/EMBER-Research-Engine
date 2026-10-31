# A234 — расширенный реестр переоценки

74 записи источников/вариантов, не 74 завершённых теста и не 74 независимых механизма. Все REVIEW_OPEN.

| ID | Кандидат | Циклы | Ветка проверки | Что требуется |
|---|---|---|---|---|
| R001 | Double MA | A188–A197,A232–A233 | PARITY | Оригинальный общий BTC/ETH счёт вместо четырёх независимых |
| R002 | DualTrendCompressionRestartShortV1 | A228–A230 | CAUSALITY | 4h BTC merge: доказать время доступности и отдельно проверить исправление |
| R003 | BearRegimeShortV1 | A205,A228–A230 | PARITY | 480h индикатор против startup250; полный исходный портфель |
| R004 | Risk_Stair_S5 | A228–A230 | PARITY | Портфель, действующий 5x риск, официальная маржа и ликвидация |
| R005 | TrendFollowing | A228–A230 | PARITY | Разделить авторский конфиг и 33-парный Freqle benchmark; protections |
| R006 | NASOSv7LongShort | A228–A230 | PARITY | Портфель, отключённый custom stop, подробные fills |
| R007 | dip_catcher | A202–A203 | PARITY | Оригинальный состав, 98% exposure, повторные входы, реальные заявки |
| R008 | TSMOM | A221 | PARITY | Штатная остановка и restart; не отключать breaker |
| R009 | SingleB_FixedRR | A189–A191 | PARITY | 10 исходных OKX пар против одного ETH; USD-M перенос отдельно |
| R010 | SOL Trend Pullback V9 | A193,A198 | PARITY | Полный 15s runtime и mark stop; независимый proxy не авторский тест |
| R011 | Octopus multi-perp CTA | A221 | PARITY | Point-in-time контрактный состав, капитал, ликвидации |
| R012 | FAdxSmaStrategy | A199 | PARITY | Конфиг, портфель, полные периоды вместо узкого gate |
| R013 | FReinforcedStrategy | A199 | PARITY | Конфиг, resampled merge, расходы и портфель |
| R014 | momentum_wick | A201 | PARITY | Все пары без отбора ETH; проверить path-dependent exits и прежний gate |
| R015 | momentum_rsi | A201 | PARITY | Все пары без отбора BTC; проверить действующее short-only поведение |
| R016 | BIGBEAR | A200 | EXECUTION | Оригинальный портфель, случайные SL/TP ties, разрешение на 1m |
| R017 | BIGBULL | A200 | EXECUTION | Не делать общий FAIL из малого N; проверить исходное исполнение |
| R018 | AggressiveSupportResistanceScalper | A205–A206 | CAUSALITY | Full-series зависимости и fill mismatch; низкая частота не FAIL |
| R019 | TrendRider | A210,A217 | PARITY | Проверить оригинальный портфель, прогрев daily EMA, активный стоп |
| R020 | Revelio sweep→BOS V1 | A222 | EXECUTION | Same-close diagnostic не final net; next-open parity без изменения сигналов |
| R021 | Pranay FVG/OB | A222 | EXECUTION | Причинное исполнение отдельно от авторского same-close отчёта |
| R022 | Acekiller MTF scanner | A222 | PARITY | Оригинальный USD-M replay без spot fallback |
| R023 | XRP funding mean reversion | A223 | DATA | Восстановить настоящие funding данные и исходный полный исполнитель |
| R024 | OI momentum/divergence | A193,A223 | DATA | Отдельный вариант; восстановить OI point-in-time, портфель и риски |
| R025 | Taker momentum | A207 | PARITY | Сверить источник SL/TP/80m и размер позиции независимого исполнителя |
| R026 | Winner15m | A205,A234 | PARITY | Повторные входы не основание отказа; восстановить исходные конфиг/портфель |
| R027 | MTF_Hybrid | A205,A234 | WARMUP | EMA19200 + lag96 против startup500; нейтральный режим при NaN |
| R028 | FVGChannel | A205,A234 | PARITY | Не требовать 4h; проверить long-only USD-M совместимость и состояние индикаторов |
| R029 | FailureToReturnStrategy | A192,A234 | PARITY | Ноль сделок не экономический FAIL; session bool и daily guard parity |
| R030 | VolatilitySystem | A221,A234 | RISK | Проверить максимум одного добора, 2x liquidation; не путать риск с отрицательным PnL |
| R031 | FSupertrendStrategy | A199 | RISK | Long-only допустим; фактический стоп и показатели исходника |
| R032 | FOttStrategy | A199 | COMPATIBILITY | Зафиксировать совместимые зависимости; широкий стоп не экономический FAIL |
| R033 | MsSupportResistanceV1 | A189–A190 | SOURCE | Восстановить полный оригинальный класс; не сочинять его по журналу |
| R034 | MsFilterV6 | A189 | SOURCE | Восстановить класс; top3-концентрация не автоматический отказ |
| R035 | MsFilterV6NoMs | A189 | SOURCE | Положительный авторский контроль сохранить отдельно, не новое семейство |
| R036 | HERMES SuperTrend | A192,A231 | TRANSFER | Авторский SPOT, causal fill audit; не выдавать за готовый USD-M |
| R037 | APEX no-pyramid | A192,A231 | TRANSFER | SPOT research/BloFin live; восстановить исходные 8 пар и исполнение |
| R038 | Quattro Donchian | A192 | TRANSFER | Пирамидинг и маржа; не переносить авторскую spot доходность на futures |
| R039 | nateemma gbb/reversion | A193 | SOURCE | Установить точный класс и SHA; полный портфель и ликвидность ZEC |
| R040 | MomentumRegimeBasket15mFast | A193,A199 | TRANSFER | Авторский spot basket; концентрация не FAIL, требуется отдельный USD-M протокол |
| R041 | OversoldReversion | A199 | TRANSFER | Spot long-only; stop и 1250h прогрев, не менять исходник |
| R042 | RSI/ADX scalper | A193 | ACCOUNTING | BTC авторский календарь, обе комиссии; ETH провал не универсальный |
| R043 | Bollinger Reverter / Donchian | A193 | SOURCE | Восстановить полные оригиналы Hyperliquid и разнести два механизма |
| R044 | ETH Momentum 2h / DumpReversal | A193 | SOURCE | Достать оригинальные исполнимые варианты; низкая частота не FAIL |
| R045 | LightGBM Jansen | A200 | SOURCE | Восстановить исторические модели и train/test границы; long-only разрешён |
| R046 | Pair Trading NEDL | A218 | ACCOUNTING | Две perpetual ноги, turnover, funding и next-open; блок не убыток |
| R047 | Chart-pattern backtester | A219 | TRANSFER | Spot данные и текущий список пар; отследить заявленную futures реализацию |
| R048 | NostalgiaForInfinity X8 | A199 | SOURCE | Восстановить точную futures поддержку и портфель; не отбрасывать за сложность |
| R049 | Funding Carry OU | A189 | TRANSFER | Двухногий профиль; рынок/мандат прежде исполнения |
| R050 | TrendFutures | A210–A211 | NEGATIVE_AUDIT | Проверить корректность старого теста; без новой ошибки не повторять тот же эксперимент |
| R051 | AdaptiveRegime / AdaptiveRegimeLong | A210 | SOURCE | Отдельные исходники не равны отвергнутому TrendFutures; восстановить evidence |
| R052 | Den­niskid research / production | A223 | CAUSALITY | Проверить отдельно архив и production: прежний lookahead относится к конкретному слою |
| R053 | Dynamic gainers | A208 | CAUSALITY | Ошибка timestamp: контроль отдельно, не прибыль оригинала |
| R054 | RsiquiV5 | A205 | CAUSALITY | Centered gradient; заблокировать вывод о прибыли до причинной проверки |
| R055 | DivergenceStrategy | A192 | CAUSALITY | Время подтверждения argrelextrema, не исходная прибыль |
| R056 | MandelbrotFibonacciStrategy | A192 | CAUSALITY | Отрицательные shift; нельзя считать оригинал causal |
| R057 | gmchun breakout | A222 | SOURCE | Исходный Binance futures класс есть, runner/журналы требуется восстановить |
| R058 | stolgo PA variants | A223 | EXECUTION | Разнести 21d SR, failed break, intraday и consolidation; next-close bracket semantics |
| R059 | SC4RECOIN breakout | A223 | TRANSFER | SPOT historical / FTX perp source; futures provenance не доказан |
| R060 | Zenith / GEM | A222 | TRANSFER | BloFin оригинал; frozen variants и USD-M parity отдельно |
| R061 | Milton BTC breakout | A221 | EXECUTION | Same-close и тысячи подборов; авторский headline не доказательство |
| R062 | BinHV45 v3 / v4 | A189 | TRANSFER | Spot only в старом аудите; сохранить, не заменять им предмет USD-M |
| R063 | GeneticEngineV1 | A189 | SOURCE | Точный repo/SHA и trade receipts не восстановлены; не экономический FAIL |
| R064 | Ultimate Alpha v16 | A189 | NEGATIVE_AUDIT | Проверить авторский отрицательный PAPER и версии, не выдумывать преимущество |
| R065 | Funding zscore | A221 | NEGATIVE_AUDIT | Проверить границы авторского OOS и отрицательные результаты |
| R066 | Orderbook imbalance | A221 | DATA | Историческая очередь/fills и полнота исходной стратегии |
| R067 | Lead-lag trader | A221 | TRANSFER | Kraken futures source; DD и воспроизводимость USD-M отдельно |
| R068 | FMZ SR breakout | A223 | RISK | Futures Binance оригинал, отсутствие initial stop; независимый tail audit |
| R069 | FMZ retest 482873 | A223 | TRANSFER | SPOT daily header против 4h текста; уточнить source прежде запуска |
| R070 | 2Candle | A205 | COMPATIBILITY | Невалидное имя класса; исправление только отдельным журналом |
| R071 | DS_BNC_EV1E_5m | A192 | TRANSFER | Spot и fallback стоп; не экономический verdict |
| R072 | NFI5MOHO_WIP | A192 | COMPATIBILITY | Старая версия интерфейса/риск; аудит отдельно от текущего NFI |
| R073 | AKzar walk-forward | A192 | SOURCE | Закрытые реализации/модель; сохранять source blocked, не FAIL |
| R074 | DevAntsa models | A200 | SOURCE | 22 production стратегии закрыты; не подменять учебной SMA |
