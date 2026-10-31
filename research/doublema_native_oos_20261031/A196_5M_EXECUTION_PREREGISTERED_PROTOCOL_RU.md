# A196 — независимый контроль ИСПОЛНЕНИЯ Double MA на 5m (протокол ДО первого прогона)

Дата: 31.10.2026; исследование PAPER ONLY. **Не подгонять старые параметры, не адаптировать 15m, не подключать реальное исполнение.**

**Основание:** оригинальная Double MA на Binance USD-M BTC ETH SOL LINK 1h/4h, подтверждённый source-pinned A195; в нативном Freqtrade2026.4 при 1h-only 84 сделки, BTC −20.70%, ETH +34.83%, SOL +17.28%, LINK +36.52%. Все три положительные зависели от очень крупных единичных плюсов. Эти цифры не доказывают реальные лимитные fills.

**Цель A196:** проверить, поменяется ли результат при более детальной хронологии заявок/стопов/выходов. Цены 1h сигналов и сама стратегия останутся **byte-identical** оригиналу автора, исходный commit `40af5c7c1c44253766428cfb06babf22f9817aa4`, blob `22ca6588bbd056e671783f676f1a4010cbfc1bb6`. Не допускается полностью новый вычислитель сигналов.

## Фиксированные сравнения

- Freqtrade==2026.4 **true original source class** `VideoDoubleMaFuturesStrategy`, Freqtrade 1h baseline versus **`--timeframe-detail 5m`** с настоящими 5m историческими Binance Vision. Оба режима имеют identical 1h/4h candles, mark, funding, strategy, per-symbol 10k wallet, original 2x leverage and near-full-stake and same cost. Это сравнение *реальной Freqtrade модели исполнения*, а не подтверждение бид/аск/лимитной очереди.
- **4 монеты × 2 комиссии = 8 отдельных detail-прогонов**: BTC, ETH, SOL, LINK; fee5bps и fee12.5bps за сторону. Нет отсева BTC, нет отключения shorts. Сравниваем с **архивом A195 из GitHub Actions #41147367668**, а не вручную скопированными числами. Verify every detailed trade receipt vs Freqtrade native ZIP.
- История [2026-05-13,2026-10-01) UTC. Для данных 1h/4h/mark/funding используются 84+4 исходных публичных ZIP A195, including authentic daily mark repair for 2026-06-29, SHA checks; 5m данные из 20 исходных месячных ZIP Binance Vision от May01 to Sep30, strict 5min continuity and real OHLC, SHA attached. Первоначальные 5m detail первые 12 дней — прогрев/полнота, target May13 onward.
- **No extra slippage yet.** Здесь тестируем строго изменение маршрута 1h OHLC→5m OHLC, не будем приписывать изменение при extra 2–5bps проскальзывания без фактического нового теста. Funding history from original Binance settled.
- Пререгистрированный экономический критерий перехода: на ETH+SOL+LINK не менее 2 из 3 должны оставаться прибыльны на 5m detail **при обеих комиссиях**, native equity DD <15%, PF>=1.25, N≥20; и 5m detailed native net return не менее **70%** соответствующего 1h baseline дохода при одинаковых symbol+fee, no unrealistic huge entry/exit trade mismatch. Дополнительно top3 winning trades <60% total *positive* gains на каждой прошедшей паре (те же A195 критерии, не ослаблять после результатов). Если 5m detail хуже — reject, не оптимизировать на этом окне.
- Сравнить all entry and exits by timestamps, fee-induced path flip, close reasons, native wallet DD and top3 / net, average trade duration.
- Критически: 5m OHLC улучшает моделирование, но **не знает порядок high/low внутри 5m**, не моделирует брокерский bid/ask/orderbook, реальную очередь лимитов, проскальзывание, ликвидации в нестандартных условиях. Не прогноз доходности.
- **Full Freqtrade lookahead-analysis и recursive-analysis** запланированы как следующий независимый этап; тест 5m detail НЕ является достаточной проверкой отсутствия data leakage. A188 one-line callback parity 27/27 не закрывает все другие источники bias.

**Запланированный вердикт:** `5M_EXECUTION_REPLAY_REPRODUCIBLE` для true native source/data, и `ECONOMIC_ADVANCE_GATE_PASS` либо `FAIL` строго по числам. Даже при PASS — PAPER-only further validation, NO LIVE.
