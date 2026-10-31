# A229 — до получения данных: независимые хронологические режимы для 3 положительных оригиналов

Дата 31.10.2026. Пользователь поручил проверить пять существующих авторских стратегий. В A228 native Freqtrade Binance Futures 2025 база/стресс выдержали только три: DualTrendCompressionRestartShortV1Strategy, BearRegimeShortV1, Risk_Stair_S5 (без оптимизации). Два экономически отрицательны, их не пересоздавать. Пять original Git blob SHA и source pin остаются прежними как в research/a228_five_original/PREREG_FIVE_FROZEN_NATIVE_REPLAY_RU.md.

Цель только ВНЕВЫБОРОЧНАЯ проверка на **других периодах**, без адаптации параметров и исходников: независимый **2024 Jan–Dec**, независимый **2026 Jan–May**. Ранее проверенный 2025 Jan–Dec не изменять. Июнь 2026 исключён из-за 8h mark archive missing 3 full 8h rows, и 1h mark missing 24 rows (одни сутки). Никаких выдуманных mark.

Официальные исторические Binance mainnet USDT-M Futures BTC/ETH/SOL 5m OHLCV плюс actual fundingRate 8h и official markPriceKlines 8h, genuine archive SHA receipts. Использовать только полностью замкнутые UTC диапазоны и Nov/Dec 2023 market warmup для 2024. Справочник фьючерсных контрактов исключительно из публичного официального Binance FUTURES TESTNET потому что GitHub IP получает mainnet HTTP451; эту неточность не скрывать. Никаких real trade API, credentials, PAPER изменений.

Движок native Freqtrade 2026.9, оригинал автора без малейших правок; исходные short/long, stop, trailing, leverage; stake $100, wallet $1000, max 3 concurrent, isolated. Комиссия база 0.05% *на сторону*, стресс 0.11% *на сторону*; это только proxy торговых расходов, не симулятор orderbook/margin tiers; stop fills OHLC, реальный slippage не проверен. Записывать return / max DD / количество / PF и journal по каждому периоду и режиму; при runtime/data blocking статус BLOCKED, не нулевой PnL. Разные рыночные годы test без parameter sweep.

Заранее заданный критерий **предварительной устойчивости**: позитивный after-cost stress 2024, 2025 и 2026 Jan–May при приемлемом риске, без mark liquidation unresolved для high leverage. Успех OHLC не равен VERIFIED; 5× плечо с маржей подвергнуть дополнительной верификации до торговой рекомендации.

Ни один новый торговый механизм не создаётся. Мандат main/RESEARCH_MANDATE_LOCKED.md и veto A220 неизменны.