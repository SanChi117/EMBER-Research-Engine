# A191 — независимый нативный OOS SingleB_FixedRR, Binance USD-M ETHUSDT 5m

## Зачем
Проверить реальную экономическую устойчивость публичного `liu57liu456/backtest-autopsy` `SingleB_FixedRR` без переписывания сигнала, подбора параметров или фиктивных свечей. Не повторять авторскую рекламу 14 008 сделок и +$8 814 как независимый факт.

## Воспроизводимость
- Оригинал: https://github.com/liu57liu456/backtest-autopsy/blob/39e640bf304dfe1edceec74668d8beded39482d5/strategy/SingleB_FixedRR.py
- SHA upstream `39e640bf304dfe1edceec74668d8beded39482d5`, Git blob `9544d6ea47c9905fed86e62c85cf6aca48c0c8c5` (проверен в CI).
- Класс: `SingleB_FixedRR`, 5m, momentum MOM(14), long при MOM>0, short при MOM<0, UTC-период weekday 06:00–23:59, stop-loss −1.5% и take-profit +1.5%, без дополнительной оптимизации.
- Движок **настоящий Freqtrade==2026.4**, запуск исходного файла `/tmp/a191-source/user_data/strategies/SingleB_FixedRR.py`.
- Рыночные данные: **26 496** настоящих непрерывных Binance USD-M ETHUSDT 5m свечей Binance Vision за 2026-07-01→2026-10-01, включая июль для прогрева. Mark-price 1h и **276** settled funding events из прежнего реестра A187; source SHA256 и ZIP SHA сохранены в полном артефакте CI.
- Зафиксированный `post-publication OOS`: **[2026-08-01, 2026-10-01) UTC** (авторский код закреплён 11.07.2026).
- Конфиг автора: кошелёк 5000 USDT, stake500, isolated, max3. Изменения конфигурации — Binance вместо OKX, только ETH вместо десяти пар, безопасное отсутствие ключей, 1× Freqtrade default. **Это иной рынок/универсум, чем авторские OKX 10 монет.**
- Подлинный [GitHub Actions run 41142627798](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41142627798) **SUCCESS**; [ZIP двух нативных бэктестов, полный trade list, source manifest, логи](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41142627798/artifacts/13020156070), GitHub archive sha256 `87966fbae1181f5b3d56ea21344c0eec8d48d5ec29b60744c2850f9127b01ca7`.
- Ни одного реального ордера, ключа биржи, тюнинга на OOS, изменения SMOKE.

## Извлечено напрямую из результатов нативного Freqtrade (не авторские числа)

| Метрика | fee=0.0005/сторона | fee=0.00125/сторона |
|---|---:|---:|
| Суммарная комиссия round trip | 10 bps | 25 bps |
| Закрытых сделок | 126 | 115 |
| Win-rate | 53.175% | 53.043% |
| LONG / SHORT | 77 / 49 | 69 / 46 |
| Профит от 5000 USD | **+24.6363 USD** | **−20.8819 USD** |
| Доходность стартового кошелька | **+0.4927%** | **−0.4176%** |
| Profit Factor | **1.0524** | **0.9556** |
| Max drawdown wallet | 0.9273% | 1.1997% |
| Три наиболее прибыльных трейда как доля итога | 91.36% | статистика доли неприменима (итог отрицателен) |
| funding fees по закрытым сделкам (знак как записан Freqtrade) | −0.21193 USD | +0.21218 USD |

Число сделок **изменилось** при повышении комиссии, значит эндогенное исполнение/выходы и последующая доступность входов зависят от `fee`. Высокая комиссия вызывает не только арифметическое ухудшение чистой прибыли. Сценарии не идентичны по входам и выходам, и их нельзя трактовать как простой fixed-price overlay.

## Решение
**`A191_NATIVE_ETH_OOS_ECONOMIC_FAIL` для данного рынка/периода/параметров.** PF1.052 близок к случайному; при 25bps roundtrip PF0.956 и net −0.418%; топ-3 выигрыша несут 91.36% положительной прибыли базовой модели. Полный независимый 10-coin replication ещё не проводился, поэтому нельзя математически утверждать, что стратегия неизбежно убыточна на всех монетах. Но при предварительном screening `SingleB_FixedRR` не заслуживает продвижения в PAPER как прибыльный резерв.

Не выполнено/не моделируется:
- настоящие bid/ask и очередь лимиток, intrabar 1m detail, проскальзывание, latency/maker queue;
- 실제 Binance тех. метаданные (использован зафиксированный статический контракт Binance для безопасного offline-run), актуальные tiered margin/liquidation;
- несколько независимых OOS-окон и cross-asset валидация, устойчивость режимов; lookahead/recursive-analysis, статистическая неопределённость;
- portfolio-level статистика 10 монет OKX не сравнима напрямую с single-pair ETH Binance.

## Статус
`TECHNICAL_PASS_NATIVE_2_FEES`, `ECONOMIC_FAIL_SCREEN`, `NO_LIVE`, `DO_NOT_PROMOTE_SINGLEB_TO_PRIMARY_OR_PAPER`.

A190 отдельно подтвердил, что полный класс MsSupportResistanceV1 автором удержан как проприетарный: использовать публичную MIT-библиотеку `market_structure` допустимо для **новой независимой** стратегии, но не выдавать её за оригинальную.
