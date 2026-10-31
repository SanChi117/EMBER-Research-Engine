# A220 — пользовательское исключение из поиска (31.10.2026)

**Цель `RESEARCH_MANDATE_LOCKED.md` НЕ изменяется: найти несколько независимо проверенных стратегий Binance USDT-M Futures разных механизмов.**

Пользователь прямо запретил дальнейшие тесты трёх новых оригиналов A220. **Оставить `USER_REJECTED_PRE_BACKTEST`**, а не `ECONOMIC_FAIL`: полного независимого бэктеста и проверки прибыльности по ним не было.

| Источник | Статус | Слова пользователя |
|---|---|---|
| `AbdullaE100/perp-quant-lab` | `DO_NOT_TEST / DO_NOT_REQUEUE` | «собирает мусор на графике» |
| `OctopusTakopi/funding-rate-alpha` | `DO_NOT_TEST / DO_NOT_REQUEUE` | «ломается как только есть хоть малейшая аномалия» |
| `agarwalchirag535-lab/smallcap-pump-reversal` | `DO_NOT_TEST / DO_NOT_REQUEUE` | «смысл отдавать рынку памп и забирать не гарантированный дамп, сомнительно» |

Полный аудит и машинная запись — [A220 в исследовательской ветке](https://github.com/SanChi117/EMBER-Research-Engine/blob/research/a220-independent-usdm-futures-original-candidates-20261031/research/a220_original_futures_candidates/A220_USER_REJECTION_FINAL_RU.md). Пользовательское вето не доказательство отсутствия edge у всего класса стратегий. Запрещено вновь предлагать **эти исходники** без нового указания пользователя. Никаких реальных/PAPER изменений.
