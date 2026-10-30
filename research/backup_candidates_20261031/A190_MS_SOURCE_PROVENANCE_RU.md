# A190 — форензика исходника MsSupportResistanceV1 (31.10.2026)

## Исходные свидетельства
- [GitHub fortunato/pymarket-structure](https://github.com/fortunato/pymarket-structure) содержит код библиотеки `market_structure`, `src/market_structure/freqtrade.py` и 15 JSON trade receipts, плюс 4h OHLCV по пяти парам (BTC/ETH/SOL/XRP/LTC).
- Головной commit источника при A189 `3502b8ec96959ad47a9b63ae7474c17c7a2dbff7`.
- [Авторский commit 82abf74f2338c79423c3a7406e995e97bcf93566](https://github.com/fortunato/pymarket-structure/commit/82abf74f2338c79423c3a7406e995e97bcf93566) отказывается публиковать торговую стратегию: "Remove strategy source code from public repository. Strategy implementations are proprietary." Коммит изменил README.md и refs/freqtrade/README.md, удалив подробности (72 строки удалений).
- Прямая проверка дерева **main** и дерева родителя removal `50ddc745428006884778a2032b6f405b4b87f9d2`: исходные классы `MsSupportResistanceV1` / `MsFilterV6` в публичных .py файлах не обнаружены. Поиск GitHub для `class MsSupportResistanceV1` не предоставил подлинного свободно доступного класса.
- Доказательства 404 сделок и их PnL сохранены в нашем отчёте A189; оттуда **невозможно** доказать исходные правила входа, геометрию SL/TP и lookahead или запускать точный оригинальный Freqtrade class.

## Вердикт
`AUTHOR_PROPRIETARY_SOURCE_WITHHELD`, `ORIGINAL_NATIVE_REPLAY_BLOCKED`.

Не изобретать правила за автора и не выдавать реконструкцию за оригинал. Не публиковать чужой закрытый код как часть EMBER. Можно отдельно, как **собственную независимую гипотезу**, разработать S/R стратегии на открытой MIT-библиотеке, но только с новой системой доказательств, новыми OOS периодами и статусом не эквивалентным авторским +70.32%.

A190 закрывается фактом недоступности исходника и сохранением Market Structure как **библиотеки для нашей собственной независимой стратегии**, а не готовой стратегии `MsSupportResistanceV1`.

Реальных ордеров не размещали, SMOKE не меняли.
