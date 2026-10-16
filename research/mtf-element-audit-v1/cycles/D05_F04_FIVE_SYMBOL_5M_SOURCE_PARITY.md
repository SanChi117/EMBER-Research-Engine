# D05/F04 — оригинальные Futures 5m пяти монет, 1440 баров, 480 C08 OHLCV-сверок

**Дата:** 2026-10-16. **Узкая приёмка:** 5 original 5m raw Binance USD-M ZIP plus checksum and 480 exact OHLCV C08 15m comparisons. PAPER ONLY; академических VC/торговых сетапов — **0**.

## Источники и исследовательский метод

Урок TDA допускает 5M VC в GREEN/BLUE маршрутах, а первоначальный фиксированный C08 список (315 архивов) содержит только 15m/1d. Поэтому новая аттестация 5m устроена отдельно, **без перезаписи C08**.

Скрипт tests/probe_f04_all_five_5m_futures_c08.py проходит BTCUSDT, ETHUSDT, SOLUSDT, XRPUSDT, BCHUSDT за 2026-10-02. Для каждой монеты через Binance Vision HTTPS TLS проверяется original ZIP и original .CHECKSUM. Валидируются все 288 последовательных 5m свечей, 12 исходных CSV полей, OHLCV и даты. Затем отдельно скачивается original native 15m ZIP из уже закреплённого C08: каждые три 5m сравниваются с одним 15m по точным числовым Decimal O/H/L/C/V и UTC timestamps. Для каждого инструмента **96 из 96** групп совпадают; **480/480 суммарно**.

Исходные 5m ZIP/CSV SHA зафиксированы в отдельном evidence/f04/F04_FIVE_5M_FUTURES_2026-10-02_RECEIPTS.json, Git blob SHA **e5b24eb50c15fcd19fe1069d44e95a0a02edaa1c**. Повторная CI требует точно этот Git blob и вновь скачивает все пять оригиналов, сверяя SHA с сохранённой квитанцией.

## Точные результаты

| Монета | Исходных 5m | OHLCV 3×5m=15m | v05 IMB | v05 1H raid | v05 5m BOS |
|---|---:|---:|---:|---:|---:|
| BTCUSDT | 288 | 96/96 | 60 | 1 | 1 |
| ETHUSDT | 288 | 96/96 | 62 | 0 | 0 |
| SOLUSDT | 288 | 96/96 | 56 | 1 | 0 |
| XRPUSDT | 288 | 96/96 | 59 | 1 | 0 |
| BCHUSDT | 288 | 96/96 | 53 | 2 | 2 |
| **Всего** | **1440** | **480/480** | **290** | **5** | **3** |

Все IMB, raid и BOS здесь являются **геометрическими кандидатами исследовательских примитивов v05**, а не авторскими одобренными сетапами. Количество геометрических кандидатов не равно количеству допустимых позиций.

**Независимые CI:**
- [Run 38873374461](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/38873374461) — **SUCCESS**: первая attestation всех 5 original ZIP и 480/480 parity.
- [Run 38873575189](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/38873575189) — **SUCCESS**: 5 Git-pinned ZIP/CSV receipt pairs подтверждены повторными оригинальными HTTPS-download. 29 прежних v05 + 23 F03 + 18 C09 = **70 технических PASS**.

### SHA новых исходников 5m

| Символ | Original 5m ZIP SHA256 | Original 5m CSV SHA256 |
|---|---|---|
| BTCUSDT | 2a492563746eba6c3689b90c00a081bfce3ceab86a06493e80f22c4d55e8c7ea | 14dc88dd66d78f44b73daa9243d62e35d539ace64d26adb0ba4b32aefb599c73 |
| ETHUSDT | 531c33307bf9a355cc9f1f364c77d394940f0bca68b4e69f3e3dfac771dcc39b | fd31423b1efc2aa3dd5831168a2e34836b1154a2c1d25dbe01ba3a1e13c1827c |
| SOLUSDT | 878c1d9ca3d244e63255fe70ce085c0907be6ec80c7caf98264052aca170fe81 | c915afde158d27eb2d5292e2d0c351d399c029011544b384f590ea478c9acdd3 |
| XRPUSDT | dbad8bb5de24bb132dbc2b2c6883528b9e59c156100e8aeac785c6f4061d64ca | 39713a221c33e1c4ab9be8c62f26a03a602480085e8971c8b3f67b8ba4bea9d1 |
| BCHUSDT | 3dac40988e662c5f7e008236150cd6288e5026f0ec30e2c851915e2fc68b0030 | e09a883ca3f08c9e166cc76eecf07a1450a9446cbf237026007f967582e1c269 |

## Границы утверждений и будущие проверки

1. Источник охватывает **пять монет только за 2026-10-02 UTC**, не все дни/всю историю 5m. Ранее 315 C08 zip/Shards не менялись.
2. Same-host .CHECKSUM и TLS не заменяют независимую криптографическую подпись Binance.
3. v05 использует инженерные предположения pivot 2+2 и raid freshness 24h, до сравнения с учебными авторскими разметками они не утверждены академией.
4. StrongHL, Liquidity, VC, 4H/1H POI и полные TDA GREEN/BLUE всё ещё требуют авторские позитивные/негативные price-примеры и явный полный MTF context. Нет trade READY, никакие заявки не создавались.
5. Не изменены source course-v05, D03, C08, SMOKE, V5/QFVG и торговая инфраструктура.

Следующая задача: независимый авторский golden-аттестат для raid/StrongHL/VC и много-дневная 5m история с правильным as-of; без подмены незаполненных академических частей технической проверкой.
