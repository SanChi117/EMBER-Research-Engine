# A228–A229 — итоги независимого нативного теста ПЯТИ готовых Binance USDT-M Futures стратегий

**31 октября 2026 года · ПЕРВЫЙ ЗАКОНЧЕННЫЙ СРАВНИТЕЛЬНЫЙ ЭКОНОМИЧЕСКИЙ ПРОГОН · НЕ РЕКОМЕНДАЦИЯ ОТКРЫВАТЬ СДЕЛКИ.**

Первоначальный список [`main/RESEARCH_SHORTLIST_FIVE_ORIGINAL_FUTURES_20261031.md`](https://github.com/SanChi117/EMBER-Research-Engine/blob/main/RESEARCH_SHORTLIST_FIVE_ORIGINAL_FUTURES_20261031.md). В настоящем тесте **выполнялись оригинальные авторские Freqtrade-исходники без изменения сигналов, параметров, стопов/тейков и плеча**. Все пять исходных Git blob SHA проверены. Никаких авторских модификаций, оптимизации на 2024/25/26 или «собственных новых стратегий» нет.

**Оригинальные исходники** (в исходном порядке):
1. `DualTrendCompressionRestartShortV1Strategy`: [wangc-joker/ft_userdata](https://github.com/wangc-joker/ft_userdata/blob/6833cb9b4bc5bfb01c3f5829ff11cc02b0814fd9/user_data/strategies/DualTrendCompressionRestartShortV1Strategy.py), blob `36cfb029cd7dc871160b037548db2c57de852969`;
2. `TrendFollowing`: [krantikaridev/freqtrade](https://github.com/krantikaridev/freqtrade/blob/11d7d66c60cf49a148cb61619b8061dc40d2510c/strategies/TrendFollowing.py), blob `ee2293e19f3cdecb082525f6d55a166249f74eb2`;
3. `NASOSv7LongShort`: [remiotore/ccxt-freqtrade](https://github.com/remiotore/ccxt-freqtrade/blob/44beaeb6a420cd8e9f2e4ea93e11d6cfa192ee03/strategies/NASOSv7_FuturesC.py), blob `172fd2b5e76cb1b14d4c9547b6046bff7f19ba7a`;
4. `BearRegimeShortV1`: [IvPalmer/Master-Trader](https://github.com/IvPalmer/Master-Trader/blob/8e29d170982c36a502de2c6ed14a80c6510c4921/ft_userdata/user_data/strategies/BearRegimeShortV1.py), blob `a6c62639e60a28b050a462f646241e7a2ba9076c`;
5. `Risk_Stair_S5`: [linhuang1212-coder/crypto-quant-trading](https://github.com/linhuang1212-coder/crypto-quant-trading/blob/63c012a0329a280f99fe57896456d4b9363c9c71/user_data/strategies/risk_exp/Risk_Stair_S5.py), blob `9b6ba1f5466727da1e9446f4e283b1c555fca59b`.

## Методика

- Исследовательские протоколы заморожены ДО результатов: A228 [пререгистрация](https://github.com/SanChi117/EMBER-Research-Engine/blob/research/a228-five-original-native-freqtrade-replay-20261031/research/a228_five_original/PREREG_FIVE_FROZEN_NATIVE_REPLAY_RU.md) и A229 [пререгистрация](A229_THREE_ORIGINAL_CROSS_REGIME_PREREG_RU.md).
- Инструмент — настоящий **Freqtrade 2026.9**, `futures`, isolated. Рынок — реальные архивы **Binance MAINNET USDT-M Futures** BTCUSDT, ETHUSDT и SOLUSDT: native `5m` OHLCV, actual `8h` fundingRate and genuine `8h` mark-price, resampling 5m→15m/1h/4h только по закрытым, непрерывным свечам. В 2025 A228 подтверждены **126 месячных ZIP** SHA (42 5m +42 mark +42 funding), A229 **279 месячных ZIP** SHA по ноябрю 2023…маю 2026. Нет Spot. 2023 funding warmup берётся из настоящего SHA-чекнутого официального ZIP.
- Из-за HTTP451 для Binance MAINNET API на GitHub-runner **только справочник параметров/precision контрактов** взят из публичного официального BINANCE FUTURES TESTNET `exchangeInfo`. Price/funding/mark берутся из MAINNET официального архива. Это **не полная mainnet execution parity**.
- $1000 начальный Freqtrade wallet, $100 stake, 3 одновременных пары, оригинальное leverage (Risk S5 — 5×), defaults original. BASE комиссия `0.05%` на сторону; STRESS `0.11%` на сторону. Это fee surcharge, **НЕ точная имитация биржевого spread, orderbook queue или slippage**. Freqtrade OHLC high/low order fill может быть оптимистичен, margin tiers и intrabar liquidation **независимо не проверены**.
- Годы **2024, 2025, 2026-01-01…2026-05-31** — самостоятельные reset-wallet прогоны. **2026-06** не включать: Binance архив markPriceKlines 8h BTC 2026-06 отсутствуют 3 свечи (87/90), в backup `1h` 24 свечи (696/720): целый день. Не восполняли пробел фантазией и не считали Jan–Sep 2026. Для сокращения расходов A229 на 2024 и Jan–May 2026 перепроверял **три** из пяти, позитивные BASE+STRESS на 2025; 2 с отрицательной экономикой 2025 не перезапускались.
- Все результаты **наших** нативных самостоятельных трейдовых прогонов, НЕ оригинальные саморекламные результаты Freqle 2022–2024 (которые имели 33 пары и другой календарь). Претендент считается VERIFIED только после положительной after-cost устойчивости на нескольких годах, механики без lookahead, реальной fill/margin/liq parity, независимого OOS/forward PAPER. Пока **0 VERIFIED**.

## Полная таблица нативных испытаний

Ниже каждый формат `BASE% / STRESS%` — ЧИСТАЯ прибыль/убыток капитала (модель Freqtrade) от $1000 с учётом Freqtrade commissions, funding (насколько задействована нативным движком), оригинальных exit/stop. Знак строго сохранён. **Плюс в отдельном периоде не означает устойчивую прибыльную систему.**

| Оригинал | 2024 | 2025 | 2026 Jan–May | STRESS max DD 2025 | Сделок 2024 / 2025 / Jan–May | Итог |
|---|---:|---:|---:|---:|---|---|
| **DualTrend Compression Short** | −2.28% / **−2.80%** | +7.08% / **+5.74%** | +6.47% / **+6.05%** | −9.03% | 21 / 49 / 18 | `FAIL_3_PERIOD_ROBUSTNESS`: 2024 минус; небольшой объём сделок; можно оставить как исследовательскую резервную гипотезу, НЕ verified |
| **TrendFollowing** | не тестировали | −37.00% / **−71.41%** | не тестировали | −73.81% | – / 1906→1828 / – | `FAIL_2025_ECONOMICS` и катастрофический DD |
| **NASOSv7LongShort** | не тестировали | −5.59% / **−5.85%** | не тестировали | −5.85% | – / 59→57 / – | `FAIL_2025_ECONOMICS` (PF<1) |
| **BearRegimeShortV1** | +2.72% / **+2.56%** | +3.87% / **+3.27%** | −0.63% / **−0.72%** | −2.87% | 12 / 40 / 4 | `INSUFFICIENT_TRADE_COUNT_AND_NEGATIVE_2026` |
| **Risk_Stair_S5** | +9.87% / **+0.93%** | +21.47% / **+19.14%** | −9.49% / **−11.01%** | −4.73% | 74→76 / 59 / 26 | `FAIL_2026_STRESS` плюс исходное 5x плечо и margin/liq не верифицированы |

**STRESS максимальные просадки в остальных окнах**:
- Dual 2024 DD −7.11%, Jan–May 2026 −5.66%.
- Bear 2024 DD −0.78%, Jan–May 2026 −1.08%.
- Risk S5 2024 DD −10.98%, Jan–May2026 −11.26%.

Дополнительные показатели за 2025:
- Dual: PF BASE 1.341, STRESS 1.264, 49 trades.
- TrendFollowing: PF .865/.754, 1906/1828 trades.
- NASOS: PF .648/.633, 59/57 trades.
- Bear: PF 1.634/1.508, 40 trades.
- Risk S5: PF 1.892/1.780, 59 trades.

## CI-доказательства

1. [A228 успешный 5 оригиналов 2025, native Freqtrade, реальные источники](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41234973955); полные архивированные trade logs; artifact ID `13055425136` SHA256 `2849356e25b0508b983e6df0202fda7bf835b4ed0f59eebff28fa7efb82b6645`.
2. [A228 неизменный журнал Freqtrade пересчитан в реальные проценты от $1000](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41235205249); 10 отдельных nativerun BASE/STRESS и PF.
3. [A229 успешные 12 независимых нативных прогонов 3 оригиналов на 2024 и Jan–May 2026](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41235465437); artifact ID `13055059629`, SHA256 `8eaabfaaab5ae429705e65732cf288d2b9bc73bd5d1612e35633750a7b70bfc1`, данные из 279 genuine official ZIPs.
4. [Отдельная проверка official exchangeInfo](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41234750479): GitHub API mainnet HTTP451, Binance FUTURES Testnet metadata HTTP200 (BTC ETH SOL).

## Вывод на текущую дату

**5 найдено, 5 получили экономическое заключение, 0 стратегии доказали стабильную прибыльную повторяемость на всех проверенных рыночных периодах**. Веб-рекламные положительные Freqle результаты нельзя выдавать за независимо проверенные в текущем рынке. Наиболее пригодный для сохранения как **непроверенная** альтернативная реализация — DualTrend, но она не прошла 2024 и имеет мало сделок. Bear недостаточно сделок; Risk S5 убыток и слишком высокое структурное плечо. TrendFollowing и NASOS на 3 majors 2025 отрицательны.

Это НЕ значит, что три механизма универсально убыточны на любых 33 монетах, параметрах и периодах; **запрещено** переоптимизировать их на только что раскрытых 2024/2025/2026. До готовой автономной торговли не дошли. Никаких реальных и существующих PAPER ордеров не изменено.

**Следующий логичный шаг**: возобновить поиск *других, готовых* open-source original futures candidates с настоящим OOS/after-cost, применяя теперь точный одинаковый тест на настоящих архивах; не создавать новую систему или стратегию.
