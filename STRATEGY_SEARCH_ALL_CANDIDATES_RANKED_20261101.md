# ИНВЕНТАРИЗАЦИЯ ВСЕХ НАЙДЕННЫХ КАНДИДАТОВ — АРХИВ ПОИСКА ПЕРЕД ПЕРЕЗАПУСКОМ

**Срез 01.11.2026. СТАТУС НАПРАВЛЕНИЯ: STOP / NO AUTOMATIC RESEARCH.**

**Первое решение начать ПОИСК вместо создания системы:** 30.10.2026, около 22:04 UTC (31.10, 00:04 Киев), вопрос пользователя «А не проще взять уже готовую?». Это не дата прежнего развития academic EMBER C-серии. Текущее исследование **остановить**, ничего нового не тестировать до последующей команды.

**Источник объёма:** [A234 реестр 74 записей](https://github.com/SanChi117/EMBER-Research-Engine/blob/research/a234-all-promising-candidates-review/research/all_candidates_a234/registry.json) + [A236 2 расширения и ещё 21 внешняя ссылка](https://github.com/SanChi117/EMBER-Research-Engine/blob/research/a236-unclassified-source-triage-20261031/research/all_candidates_a234/A236_TRIAGE_21_SOURCES_RU.md). Здесь **ровно 76/76 записей R001–R076**, но это *варианты и иногда группы нескольких стратегий*, не 76 независимых проверенных механизмов. В приложении 18 дополнительных не-кандидатов и 3 источника с прямым вето. Нельзя гарантировать, что ранние переписки до этого документированного реестра не содержали ещё названий.

**Ранжирование — экспертная оценка пригодности к дальнейшему исследованию**, а не доходность, не статистический score, не доказанная вероятность успеха. Высокие места требуют меньше пустых догадок о реальной модели; при огромных стопах/ликвидациях рейтинг означает научный интерес, НЕ готовность к торговле. Внутри группы порядок ориентировочный и спорный. Данные авторских README и наши реальные native trials **различаются**. Все 76 — **NOT_VERIFIED**, 0 утверждённых прибыльных USDT-M систем. `RUN SUCCESS` ≠ `ECONOMIC PASS`. Ссылка на единый [текущий архив статусов](https://github.com/SanChi117/EMBER-Research-Engine/blob/main/RESEARCH_STATUS_CANONICAL.md).

**Историческая модель и периоды:** A245 CONTROLLED BTC/ETH/SOL $1000/stake $100/max3, комиссионная BASE 0.05% и STRESS 0.11% на сторону (не реальная очередь и ликвидации); A245 30/36 успешных economics и 6 блокированных; A243 оригинальный Winner 6/6, но не нетронутый OOS. А238/А240 воспроизводили исходные shared wallets, но не подтверждали live/margin. Никогда не переносить авторские ROI между рынками или частный ETH/3-pair на весь авторский universe.

## Все 76 позиций в порядке убывания исследовательской перспективности

### A — максимум исследовательского интереса, но НЕ торговая готовность

| Место | ID — стратегия | Происхождение | Что реально известно / почему ниже или выше | Отдельный незакрытый вопрос |
|---:|---|---|---|---|
| 1 | **R030 VolatilitySystem** | `freqtrade/freqtrade-strategies` | USD-M A245 STRESS: +15.63% / +16.17% / +2.24%; но 2×, DCA, источник stop −100%: проверка ликвидации не выполнена | Проверить максимум одного добора, 2x liquidation; не путать риск с отрицательным PnL |
| 2 | **R004 Risk_Stair_S5** | `linhuang1212-coder/crypto-quant-trading` | Авторский общий счёт A238 STRESS +22.29% / +11.80% / −2.74%, исходный 5× и риск ликвидации | Портфель, действующий 5x риск, официальная маржа и ликвидация |
| 3 | **R011 Octopus multi-perp CTA** | `OctopusTakopi/crypto-trend-following` | Авторский многофьючерсный CTA +242.1% за 2020–2026, Sharpe1.04, DD30.1%, ~145 контрактов одновременно; независимого replay нет | Point-in-time контрактный состав, капитал, ликвидации |
| 4 | **R029 FailureToReturnStrategy** | `hrodrig/freqhub-strategies` | A245 STRESS +0.392% / +0.407% / +0.409%, всего 24/12/6 закрытий; малый эффект и малая выборка | Ноль сделок не экономический FAIL; session bool и daily guard parity |
| 5 | **R033 MsSupportResistanceV1** | `fortunato/pymarket-structure` | Авторские 404 сделок, +70.32%, PF1.38; ПОЛНЫЙ исходный класс НЕ опубликован, воспроизведение заблокировано | Восстановить полный оригинальный класс; не сочинять его по журналу |
| 6 | **R009 SingleB_FixedRR** | `liu57liu456/backtest-autopsy` | Исходный OKX 10 пар; Binance ETH A191 STRESS −0.42% — один ETH не доказывает провал 10-парного портфеля | 10 исходных OKX пар против одного ETH; USD-M перенос отдельно |

### B — значимые оригиналы/гипотезы, недостаёт надёжного доказательства

| Место | ID — стратегия | Происхождение | Что реально известно / почему ниже или выше | Отдельный незакрытый вопрос |
|---:|---|---|---|---|
| 7 | **R008 TSMOM** | `yongzhe2160cs/trading-engine` | Без штатного safety breaker авторская модель положительна; с ним прежняя экономика убыточна — restart не восстановлен | Штатная остановка и restart; не отключать breaker |
| 8 | **R002 DualTrendCompressionRestartShortV1** | `wangc-joker/ft_userdata` | Оригинальный short BTC режим, но 4H→1H merge/момент доступности старшего сигнала не доказан | 4h BTC merge: доказать время доступности и отдельно проверить исправление |
| 9 | **R022 Acekiller MTF scanner** | `Acekiller88/crypto-signal-scanner` | Готовый MTF BOS/FVG/OB scanner; source может молча подменять USD-M свечи Spot | Оригинальный USD-M replay без spot fallback |
| 10 | **R023 XRP funding mean reversion** | `Gotodataru/binance-futures-backtest` | Автор заявляет XRP +0.19%/44 trades; в опубликованном source CSV есть только BTC, приватные данные отсутствуют | Восстановить настоящие funding данные и исходный полный исполнитель |
| 11 | **R034 MsFilterV6** | `fortunato/pymarket-structure` | Авторский +39.85%, но 96.2% суммарного плюса дают 3 сделки; исходный исполнимый класс отсутствует | Восстановить класс; top3-концентрация не автоматический отказ |
| 12 | **R035 MsFilterV6NoMs** | `fortunato/pymarket-structure` | Авторский контроль +22.59%, PF1.21, 208 trades; класс не восстановлен | Положительный авторский контроль сохранить отдельно, не новое семейство |
| 13 | **R016 BIGBEAR** | `genia503/mean-reversion-backtester` | Оригинальный TP/SL исходил из случайного 50/50 при касании обоих в свече; требуется реальный 1m порядок | Оригинальный портфель, случайные SL/TP ties, разрешение на 1m |
| 14 | **R017 BIGBULL** | `genia503/mean-reversion-backtester` | Очень малое N, не причина универсального FAIL; исходный tie/intrabar сомнителен | Не делать общий FAIL из малого N; проверить исходное исполнение |
| 15 | **R039 nateemma gbb/reversion** | `nateemma/strategies` | По автору концентрируется PnL в неликвидном ZEC; непригодно без исторических bid/ask | Установить точный класс и SHA; полный портфель и ликвидность ZEC |
| 16 | **R045 LightGBM Jansen** | `djienne/ML_Trading_Strategy_Crypto_BTC_LightGBM_Jansen` | ML research, полный источник Python есть, но исторические модели и честные train/test версии не восстановлены | Восстановить исторические модели и train/test границы; long-only разрешён |
| 17 | **R042 RSI/ADX scalper** | `jiangkaili/binance-trader-bot` | RSI/ADX на BTC, отрицательный ETH transfer и неполный учёт entry-fee | BTC авторский календарь, обе комиссии; ETH провал не универсальный |
| 18 | **R046 Pair Trading NEDL** | `djienne/pair_trading_NEDL` | Парная статистическая арбитражная механика; 2 legs, funding и PnL портфеля не сверены | Две perpetual ноги, turnover, funding и next-open; блок не убыток |
| 19 | **R075 V5 Crypto Scalper — perp Momentum theoretical** | `knacker65/v5-crypto-scalper` | Автор $415 gross 3x теоретический perp результат за 3 года, funding и реальный источник свечей отсутствуют | Restore source pickle provenance and original perps simulator ledger; causal fill + funding/margin; only then independent Binance USD-M test |
| 20 | **R057 gmchun breakout** | `gmchun83/binancefuturebot` | Родной Binance Futures breakout code имеется; нет полноценного исполнителя и журнала PnL | Исходный Binance futures класс есть, runner/журналы требуется восстановить |

### C — резерв, ограниченная подтверждённость или перенос между рынками

| Место | ID — стратегия | Происхождение | Что реально известно / почему ниже или выше | Отдельный незакрытый вопрос |
|---:|---|---|---|---|
| 21 | **R014 momentum_wick** | `TheoBrigitte/freqtrade` | Оригинал 5m long/short, фактический SL10% цены; старый A201 требует проверки всех пар | Все пары без отбора ETH; проверить path-dependent exits и прежний gate |
| 22 | **R015 momentum_rsi** | `TheoBrigitte/freqtrade` | Оригинал 5m, строка `enter_long=0` делает фактически short-only, стоп10%; нельзя считать long/short | Все пары без отбора BTC; проверить действующее short-only поведение |
| 23 | **R019 TrendRider** | `darkvolg/Trading` | 1H+4H+1D тренд, фактический стоп6%; прежний net после комиссий отрицателен | Проверить оригинальный портфель, прогрев daily EMA, активный стоп |
| 24 | **R031 FSupertrendStrategy** | `freqtrade/freqtrade-strategies` | 1H long-only пример futures, stop −26.5%, не готов к малому капиталу | Long-only допустим; фактический стоп и показатели исходника |
| 25 | **R032 FOttStrategy** | `freqtrade/freqtrade-strategies` | Исходник `from numpy.lib import math` конфликтует с современной NumPy, stop −26.5%; SOURCE RUNTIME BLOCK | Зафиксировать совместимые зависимости; широкий стоп не экономический FAIL |
| 26 | **R043 Bollinger Reverter / Donchian** | `Superior-Trade/superior-skills` | Hyperliquid две разных гипотезы; 84/6 сделок, авторские результаты не Binance USD-M | Восстановить полные оригиналы Hyperliquid и разнести два механизма |
| 27 | **R044 ETH Momentum 2h / DumpReversal** | `grinay/geektrade-strategies` | 2h Momentum PF3.08 у автора, но около 12 сделок/год, исполнимый оригинал/доказательства не собраны | Достать оригинальные исполнимые варианты; низкая частота не FAIL |
| 28 | **R051 AdaptiveRegime / AdaptiveRegimeLong** | `Kureshi25/cryptobot` | AdaptiveRegime отличается от отрицательного TrendFutures; исходные метрики и полный портфель не проверены | Отдельные исходники не равны отвергнутому TrendFutures; восстановить evidence |
| 29 | **R058 stolgo PA variants** | `stockalgo/stolgo` | Набор PA вариантов без отдельного корректного causal-fills backtest | Разнести 21d SR, failed break, intraday и consolidation; next-close bracket semantics |
| 30 | **R060 Zenith / GEM** | `traderhydr/krpticz` | Zenith/GEM BloFin; перенос на Binance USD-M без исходных fills ещё не испытан | BloFin оригинал; frozen variants и USD-M parity отдельно |
| 31 | **R066 Orderbook imbalance** | `tsuithomas/crypto_research_order_book_imbalance` | OI/стакан невозможно воспроизвести историческими OHLC; full-depth/queue data отсутствуют | Историческая очередь/fills и полнота исходной стратегии |
| 32 | **R067 Lead-lag trader** | `mamipour/lead-lag-trader` | Kraken futures, venue risk и DD без независимого USD-M | Kraken futures source; DD и воспроизводимость USD-M отдельно |
| 33 | **R068 FMZ SR breakout** | `fmzquant/strategies` | Оригинал FMZ для фьючерсов, но нет безопасного начального стопа | Futures Binance оригинал, отсутствие initial stop; независимый tail audit |
| 34 | **R048 NostalgiaForInfinity X8** | `iterativv/NostalgiaForInfinity` | Nostalgia X8 сложный spot family, настоящий futures config не доказан | Восстановить точную futures поддержку и портфель; не отбрасывать за сложность |
| 35 | **R020 Revelio sweep→BOS V1** | `hroussel18/Revelio_Improved_Strategy` | Сигнал sweep→BOS может быть полезен, но оригинальная same-close модель исполнения некорректна | Same-close diagnostic не final net; next-open parity без изменения сигналов |

### D — выполненные отрицательные/смешанные испытания или жёсткий риск

| Место | ID — стратегия | Происхождение | Что реально известно / почему ниже или выше | Отдельный незакрытый вопрос |
|---:|---|---|---|---|
| 36 | **R010 SOL Trend Pullback V9** | `kboranyldz/sol-trading-research` | SOL V9: 12 сделок/141 день, оригинальные сигналы + 5m proxy STRESS −19.43%, полноценный mark/15s НЕ воспроизведён | Полный 15s runtime и mark stop; независимый proxy не авторский тест |
| 37 | **R024 OI momentum/divergence** | `Gotodataru/binance-futures-backtest` | Авторский OI divergence SUI PF1.108 при DD −97.5%, ETH PF1.023 при DD −49.5%, point-in-time OI в приватных данных | Отдельный вариант; восстановить OI point-in-time, портфель и риски |
| 38 | **R025 Taker momentum** | `Gotodataru/binance-futures-backtest` | Авторский taker momentum PF BTC.332 ETH.516 SOL.750 SUI.829 — сильное отрицательное свидетельство | Сверить источник SL/TP/80m и размер позиции независимого исполнителя |
| 39 | **R012 FAdxSmaStrategy** | `freqtrade/freqtrade-strategies` | A245 STRESS +1.04% / −3.54% / −0.69% на 3-парном контрольном счёте | Конфиг, портфель, полные периоды вместо узкого gate |
| 40 | **R013 FReinforcedStrategy** | `freqtrade/freqtrade-strategies` | A245: 6/6 сценариeв BLOCKED ошибкой оригинала `adx_period`, нет прибыльности/убыточности | Конфиг, resampled merge, расходы и портфель |
| 41 | **R026 Winner15m** | `win-boom/BTCquant` | Оригинальный bt.json $100 BTC/ETH; A243 STRESS 2024 −19.06%, 2025 −21.46%, 2026 Jan-May −10.36% | Повторные входы не основание отказа; восстановить исходные конфиг/портфель |
| 42 | **R001 Double MA** | `MirrorNew/2026DoubleMaFuturesStrategy` | А240 оригинальный BTC/ETH shared wallet STRESS 2025 +0.38%, 2026 −13.97% — A233 4 независимых счёта нельзя считать авторским | Оригинальный общий BTC/ETH счёт вместо четырёх независимых |
| 43 | **R003 BearRegimeShortV1** | `IvPalmer/Master-Trader` | Авторский 20-парный результат за годы нестабилен и самим автором RETIRE; independent full portfolio не повторён | 480h индикатор против startup250; полный исходный портфель |
| 44 | **R005 TrendFollowing** | `krantikaridev/freqtrade` | A237 оригинальный общий TrendFollowing wallet STRESS убыточен; нет нового основания для повтора | Разделить авторский конфиг и 33-парный Freqle benchmark; protections |
| 45 | **R006 NASOSv7LongShort** | `remiotore/ccxt-freqtrade` | NASOS native TF A235 стресс 2024/25 отрицателен, 2026 N0; source custom-stop фактически отключён | Портфель, отключённый custom stop, подробные fills |
| 46 | **R028 FVGChannel** | `jaredrsommer/freqtradestrategies` | A245 STRESS 2024 −23.70% / 2025 −19.43% / 2026 −18.24%; long-only стратегия перенесена на USD-M | Не требовать 4h; проверить long-only USD-M совместимость и состояние индикаторов |
| 47 | **R027 MTF_Hybrid** | `win-boom/BTCquant` | A245 STRESS 2024 −34.47% / 2025 −10.63% / 2026 −10.10%, EMA19200 против startup500 | EMA19200 + lag96 против startup500; нейтральный режим при NaN |
| 48 | **R007 dip_catcher** | `viktors1982/trading` | dip_catcher 2026 были плюсы, но 2025 STRESS 0/4 и 98% времени все 4 позиции заняты | Оригинальный состав, 98% exposure, повторные входы, реальные заявки |

### E — низкий приоритет: критические недоработки, venue или нечастые сигналы

| Место | ID — стратегия | Происхождение | Что реально известно / почему ниже или выше | Отдельный незакрытый вопрос |
|---:|---|---|---|---|
| 49 | **R018 AggressiveSupportResistanceScalper** | `Meszqt/freqtrade-test` | A205 7 закрытий/141д на 4 монеты за каждый из двух годов; слишком мало сделок, LIMIT/TTL mismatch | Full-series зависимости и fill mismatch; низкая частота не FAIL |
| 50 | **R021 Pranay FVG/OB** | `pranay123-stack/Algorithmic-Trading-Projects` | Авторский same-bar close fill после формирования сигнала, заявленные +25.7% нельзя считать исполненными | Причинное исполнение отдельно от авторского same-close отчёта |
| 51 | **R036 HERMES SuperTrend** | `chrysek70/hermes-trading` | HERMES исследования на Binance SPOT, а не USD-M | Авторский SPOT, causal fill audit; не выдавать за готовый USD-M |
| 52 | **R037 APEX no-pyramid** | `EstebanSP23/crypto_systematic_research` | APEX история Spot, live на BloFin; original USD-M нет | SPOT research/BloFin live; восстановить исходные 8 пар и исполнение |
| 53 | **R038 Quattro Donchian** | `EstebanSP23/crypto_systematic_research` | Quattro Spot pyramid, маржа и исполнение 4 доборов не верифицированы, DD37.5% | Пирамидинг и маржа; не переносить авторскую spot доходность на futures |
| 54 | **R040 MomentumRegimeBasket15mFast** | `nateemma/strategies` | MomentumRegimeBasket spot, огромная концентрация ZEC и DD>40% | Авторский spot basket; концентрация не FAIL, требуется отдельный USD-M протокол |
| 55 | **R041 OversoldReversion** | `nateemma/strategies` | Spot long-only, нет нормального стопа, startup1250h | Spot long-only; stop и 1250h прогрев, не менять исходник |
| 56 | **R047 Chart-pattern backtester** | `juriok/chart-pattern-backtester` | Chart-pattern source spot/историческая выборка с текущим survivorship | Spot данные и текущий список пар; отследить заявленную futures реализацию |
| 57 | **R049 Funding Carry OU** | `aayanvatsa04/btc-perpetual-funding-arbitrage` | 2-leg carry спот+perp, недостаточная полная маржа, не частые сделки | Двухногий профиль; рынок/мандат прежде исполнения |
| 58 | **R050 TrendFutures** | `Kureshi25/cryptobot` | Автор full original TrendFutures потеря −66.5% при1×, редкая daily частота | Проверить корректность старого теста; без новой ошибки не повторять тот же эксперимент |
| 59 | **R052 Den­niskid research / production** | `denniskid2520/btcusdt-research-archive` | Research archive: 59/59 ранних сигналов читали ещё незакрытую 4h; production отдельно и не доказан | Проверить отдельно архив и production: прежний lookahead относится к конкретному слою |
| 60 | **R053 Dynamic gainers** | `kiattisakph/crypto-scalp-bot` | Ошибка timestamp сигнала в исходном dynamic gainer | Ошибка timestamp: контроль отдельно, не прибыль оригинала |
| 61 | **R055 DivergenceStrategy** | `jamniol/freqtrade-setup` | Pivot argrelextrema вероятно знает будущие бары до подтверждения | Время подтверждения argrelextrema, не исходная прибыль |
| 62 | **R056 MandelbrotFibonacciStrategy** | `hrodrig/freqhub-strategies` | Отрицательный shift даёт future leakage в исходном сигнале | Отрицательные shift; нельзя считать оригинал causal |
| 63 | **R059 SC4RECOIN breakout** | `SC4RECOIN/simple-crypto-breakout-strategy` | Spot/FTX perp provenance не установлен, USD-M нет | SPOT historical / FTX perp source; futures provenance не доказан |
| 64 | **R061 Milton BTC breakout** | `MiltonTulli/trading-bot` | same-close вход и тысячи подбираемых параметров, красивый заголовок не воспроизводится | Same-close и тысячи подборов; авторский headline не доказательство |
| 65 | **R062 BinHV45 v3 / v4** | `zevrichards/freqtrade-strategies` | BinHV45 SPOT и деградация paper, валютный рынок оригинала не USD-M | Spot only в старом аудите; сохранить, не заменять им предмет USD-M |
| 66 | **R071 DS_BNC_EV1E_5m** | `Danson77/Freqtrade_AIO_UI` | SPOT fallback и стоп, USD-M source parity отсутствует | Spot и fallback стоп; не экономический verdict |

### F — исключить из нового старта без существенных новых исходников/данных

| Место | ID — стратегия | Происхождение | Что реально известно / почему ниже или выше | Отдельный незакрытый вопрос |
|---:|---|---|---|---|
| 67 | **R054 RsiquiV5** | `TheoBrigitte/freqtrade` | Centered gradient использует будущие свечи; нельзя принимать original backtest как causal | Centered gradient; заблокировать вывод о прибыли до причинной проверки |
| 68 | **R063 GeneticEngineV1** | `ceyhanmolla` | Не найден точный source SHA и trade receipts, 98.9% WR по автору не доказан | Точный repo/SHA и trade receipts не восстановлены; не экономический FAIL |
| 69 | **R064 Ultimate Alpha v16** | `OfficialGIGA/freqtrade-ml-strategy` | Ultimate Alpha 139 PAPER сделок −94 USD, win32.4%, автор отрицательный | Проверить авторский отрицательный PAPER и версии, не выдумывать преимущество |
| 70 | **R065 Funding zscore** | `Adeline117/Strategy-project` | Авторский funding-zscore OOS отрицателен | Проверить границы авторского OOS и отрицательные результаты |
| 71 | **R069 FMZ retest 482873** | `https://www.fmz.com/strategy/482873` | FMZ 4h описан, но в исходнике SPOT daily header, venue/timeframe mismatch | SPOT daily header против 4h текста; уточнить source прежде запуска |
| 72 | **R070 2Candle** | `jaredrsommer/freqtradestrategies` | Класс `2Candle` как Python identifier невалиден; оригинал напрямую не запускается | Невалидное имя класса; исправление только отдельным журналом |
| 73 | **R072 NFI5MOHO_WIP** | `davidzr/freqtrade-strategies` | Старая API версия и нефиксированный риск, нет экономической паритетности | Старая версия интерфейса/риск; аудит отдельно от текущего NFI |
| 74 | **R073 AKzar walk-forward** | `AKzar1el/walk-forward-crypto` | Полный original execution/model закрыты; SOURCE BLOCK | Закрытые реализации/модель; сохранять source blocked, не FAIL |
| 75 | **R074 DevAntsa models** | `DevAntsa/DevAntsa-Algo-Public` | 22 production models закрыты; доступен лишь пример SMA | 22 production стратегии закрыты; не подменять учебной SMA |
| 76 | **R076 Crypto Stat Arb — spot mean reversion gross edge** | `billybraith17/crypto-stat-arb` | Kraken Spot mean-reversion gross edge ниже издержек; автор PERP только предложил, не реализовал | Find full live-ready original futures implementation; if absent record SOURCE/MARKET block, never transplant spot profitability to USD-M |

## Дополнительные 18 обнаруженных внешних источников, НЕ входящих в R001–R076

Это **ещё 18 отдельных найденных ссылок**, но не подтверждённые пригодные стратегии. Они не пропали: получили конкретное основание исключения/блокировки. Кроме них A236 содержит 2 новых кандидата R075/R076 и один дубль уже учтённого R052.

| № | Источник | Почему не отдельный пронумерованный полноценный кандидат |
|---:|---|---|
| X01 | `xujaan/futurabot` | SMC/OBI/CVD/VPIN; нет независимого оригинального OOS-журнала |
| X02 | `DylanSiegel/GO-Microstructures` | Hawkes/aggTrades, исследовательская модель, нет самостоятельной net стратегии |
| X03 | `HodlHook/momentum-breakout-postmortem` | опубликован отрицательный OOS, не восстановлена прибыльная отдельная система |
| X04 | `MG-Trading-Terminal/trading-strategy` | позиционирование/OI: документация без полного оригинального исполнителя |
| X05 | `Mykola-Quant/retail-crypto-alpha` | отрицательный авторский futures OOS |
| X06 | `PVinh-Quant/Kairos-v2` | инфраструктура, не верифицированный прибыльный алгоритм |
| X07 | `SebastianBoehler/MarketTensor` | ML эксперимент с практически нулевой разницей Sharpe |
| X08 | `Superjojo74/nautilus-perp-funding` | исторический settlement/tool, не стратегия |
| X09 | `analogdada/perplab` | инструмент проверки, не опубликованный edge |
| X10 | `behlulgoker/price-action-engine` | исходник использует Binance spot API, не USDT-M |
| X11 | `bockuden/crypto-cointegration-research` | авторский after-cost basis отрицательный |
| X12 | `chiragbitoni/binance-paper-trading-lab` | PAPER инфраструктура, исходная стратегия spot |
| X13 | `francisx1999/crypto-trading-bot-postmortem` | 7 негативных тестов на Kraken/Coinbase, отдельная неUSD-M venue |
| X14 | `joseph280/crypto-backtest-lab` | прибыль демонстрационной синтетики, не настоящая Binance стратегия |
| X15 | `spagnola-analytics/intraday-strategies` | CME MES/equity futures, другой рынок |
| X16 | `ycchew/CQ_breakout_strategy` | Yahoo/equities и подгонка, не crypto USD-M |
| X17 | `younghwan91/quantbox-engine` | оригинальный repo не восстановлен |
| X18 | `zabor-crypto/zaBor` | инфраструктура/риск, не отдельный исходный торговый edge |

## 3 отдельных прямых запрета пользователя — НЕ «рыночный FAIL»

| Источник | Статус |
|---|---|
| `AbdullaE100/perp-quant-lab` | USER_VETO / DO_NOT_REQUEUE, прежнее прямое несогласие |
| `OctopusTakopi/funding-rate-alpha` | USER_VETO / DO_NOT_REQUEUE; **другой репозиторий**, не R011 multi-perp trend CTA |
| `agarwalchirag535-lab/smallcap-pump-reversal` | USER_VETO / DO_NOT_REQUEUE |

## Контроль результата инвентаризации

- **76/76** строк из машинного реестра включены **по одному разу**, порядок 1–76.
- Ещё **18** ссылок A236 без полноценного отдельного подтверждённого торгового оригинала; **3** пользовательских вето. Итого **97 позиций источников/вариантов по сохранившимся учётным записям**, а НЕ 97 торговых стратегий и не доказанная полнота всей мировой/ранней истории.
- Старые `PASS` функционального кода, source semantic audit, авторская реклама и исторические симуляции **не гарантируют прибыльность**. Настоящий статус `VERIFIED_FUTURES_CANDIDATE=0`.
- **Запрет на новые автоматические тесты до следующего прямого указания.** Это архив, не план на немедленное исполнение. PAPER задачи другой ветки проекта не переписывались.
