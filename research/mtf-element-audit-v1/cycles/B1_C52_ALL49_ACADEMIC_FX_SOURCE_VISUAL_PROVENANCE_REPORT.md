# B1/C52 — Прочитаны все 49 настоящих графических исходников академии; обнаружены оригинальные EUR/USD/FX публикации

Дата: 2026-10-24; GitHub branch `research/academic-engine-recovery-20261015`. **PAPER ONLY / NOT_TRADE_READY / 0 сделок / 0 реальных ордеров / 0 PnL.** C52 — SOURCE-ONLY восстановление визуальных правил/поставщиков котировок; не новая стратегия и не подтверждённое авторское торговое событие.

## 1. Предшественник и метод

Независимо принят A121 = **121/121** связанных записей SHA (tip `5052650462e22657e9db85ddfc2c539a74e628d4eef3cb413a5b868d6262949b`, [CI 40096680485](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40096680485) PASS 3/3 Python), C51 подлинный владельческий Drive инвентарь **49 разных PNG IDs** в семи папках, из них 6 были фактически просмотрены. В C52 дополнительно получены байты и **реально визуально исследованы все остальные 43 PNG** из аутентифицированного Google Drive. Проверен источник графики, а не подставлены «учебные сигналы».

Владелец сохраняет графику на Google Drive. Содержимое 49 PNG **НЕ копируется в публичный GitHub**. В репозитории только точный источник ID/ссылка, консервативная визуальная классификация и, для восьми реально идентифицированных рыночных диаграмм, реальные размеры/разрешение/SHA256 просмотренных PNG. Все 49 PNG были реально скачаны в текущем исследовательском исполнении: **14 135 731 байт** суммарно. SHA256 агрегат `842232ca132f836edafbeaac41403d251b0c36449fb17768921ff8b39a7ce696` вычислен по лексикографически отсортированным именам файлов, конкатенация `UTF8 filename + NUL + sha256 raw bytes hex + LF`. Это **локальное свидетельство о просмотренных владельческих бинарных материалах, а не SHA, независимый от владельческого доступа**: GitHub Actions не умеет читать его приватные Drive PNG. Не объявлять этот агрегат независимо проверенным CI.

## 2. Полный результат 49 исходных иллюстраций

| Консервативный класс после фактического чтения | Число |
|---|---:|
| Полные market-style чарты с читаемыми TradingView symbol/provider/timeframe/publication headers | **8** |
| Обрезанные свечные учебные рыночные иллюстрации с зонами, НО без надёжно читаемого поставщика/таймфрейма | **19** |
| Явные концептуальные иллюстрации/правила POI, FVG, OB, RB, SNR, MTF entry | **8** |
| Скриншоты рабочего стола, содержащие мелкие вложенные изображения уроков, НЕ исходные full-size chart goldens | **14** |
| **Проверено/просмотрено всего** | **49** |

Точная запись для каждого source ID: `evidence/c52/C52_ALL_49_AUTHENTIC_OWNER_COURSE_VISUAL_CLASSIFICATION_AND_8_FX_HEADERS.json`. Исходный метод `d05/c52_full_course_visual_49_source_inspection.py`. **0 course author-verified negative/positive raw-candle golden**.

## 3. Основное новое открытие: академические примеры EUR/USD с 2024/2025 TradingView

При увеличении оригинального разрешения, а не маленьких превью, **8** PNG имеют настоящие различимые TradingView заголовки:

| Учебная картинка с оригинального Drive | Инструмент, источник, TF | Дата/время **ПУБЛИКАЦИИ** TradingView |
|---|---|---|
| [Untitled (41).png](https://drive.google.com/file/d/153eXt9lGrrhRumOfFsLQryS-3FBBX8Vl/view) | EURUSD OANDA 4H | 2024-05-26 13:08 UTC+02 |
| [Untitled (42).png](https://drive.google.com/file/d/1HuwTCxVYvm_YSmaPpZ2RxD7PA9UuzwtC/view) | EURUSD OANDA 1H | 2024-05-26 13:09 UTC+02 |
| [Untitled (43).png](https://drive.google.com/file/d/1obj4bBVqplvrL2E_iNHXOHoOaDhj5gKx/view) | EURUSD OANDA 15M | 2024-05-26 13:10 UTC+02 |
| [Untitled (44).png](https://drive.google.com/file/d/1OeV2mNl-nlbvGNPPJYiFVtDSnB3lFCC3/view) | EURUSD OANDA 4H | 2024-05-26 13:26 UTC+02 |
| [Untitled (45).png](https://drive.google.com/file/d/1tJW5eTs2TRK2mYTOgQxPJtcnSz41-DIP/view) | EURUSD OANDA 1H | 2024-05-26 13:27 UTC+02 |
| [image (4).png](https://drive.google.com/file/d/1F0LLCklPaPNCBWHwVpsKUPqp1hdsh35p/view) | EURUSD SAXO 4H | 2025-01-07 19:48 UTC+01 |
| [image (5).png](https://drive.google.com/file/d/1JlQcYmNst3GEp4ohLArGVL9eqJi8i2-b/view) | EURUSD SAXO 4H | 2025-01-07 19:49 UTC+01 |
| [image (3).png](https://drive.google.com/file/d/1b78gDdyIZO21QWoKKRUK47PbYyq35U3C/view) | EURUSD OANDA 4H | 2025-01-20 14:25 UTC+02 |

**Существенно**: На некоторых оригинальных изображениях есть «published on TradingView.com» — это **время публикации / экспорта картинки**, оно НЕ доказывает, что показанная свеча относится к этому дню, или что автор открыл сделку в этот момент. Уточнение из реального источника **опровергает предположение, что все учебные картинки относятся к 2023 и/или представлены исходными Binance USD-M crypto 2026**. Следовательно не соединять их с ранее замороженными 2026 BTC/ETH/SOL/XRP/BCH источниками. Для авторской replay проверки нужен исторический **EUR/USD именно поставщика OANDA либо SAXO**, с исходной датой свечи, оригинальным TF и точным рыночным источником. Такой набор НЕ извлечён, chart-golden count = 0.

Пять OANDA EUR/USD графиков, опубликованных 26 мая 2024 года, покрывают **4H→1H→15M**, могут образовать последовательность учебного route A, но **не доказано**, что каждый относится к тем же историческим свечам и что на 15M существует правильный author entry VC. Без raw bar identity + validated POI first-test+1H trigger, StrongHL и 4H FTA нельзя превратить их в positive entry golden.

## 4. Правила, которые можно доказать текстом на картинках без подмены фактами о рынке

- `Untitled (39).png` из Entry Model Logic явно фиксирует **две отдельные цепочки**: `4H POI [IMB,RB,SNR] → 1H Trigger [Liquidity or IMB] → 15M Entry VC [IMB,SNR]` и `1H POI [IMB,RB,SNR] → 15M Trigger [Liquidity or IMB] → 5M Entry VC [IMB,SNR]`. Это визуальное подтверждение описания C45 (условные маршруты академии), а **не** право исполнять сделку или менять выбранное пользователем 15m подтверждение.
- `Slide 16_9 - 492.png` наглядно отмечает `OB - Order Block`; `Slide 16_9 - 502.png` — `RB - Rejection Block` с отличием. `fvg.png` помечает `IMB - Imbalance / FVG - Fair Value Gap`; `image (1).png` — `SNR - Support & Resistance`. Они показывают, что нельзя автоматически объединить POI/OB/RB/SNR/IMB в один универсальный wick-gap механизм.
- `image (2).png` демонстрирует на концептуальном свечном примере SSL raid / SNR и реакцию как структурное понятие. Это **не доказательство** наличия в архиве курса авторских raw trade entries/STOP/TP.

## 5. Реализована fail-closed защита

`d05/c52_full_course_visual_49_source_inspection.py` хранит 8 проверенных Drive source IDs + реальный SHA оригинальных бинарных файлов + legible forex provider / TF / *publication timestamp*, 8 концептуальных image IDs и остальные исходные C51 exact source IDs. На выходе все **49** `CourseFigure` помечены inspected, но `original_market_bar_timestamp=None`, `original_author_annotated_trade_golden=False`, `independently_valid_market_source_raw_bar=False`, `orders=trades=()`, `readiness=NOT_TRADE_READY`.

`d05/test_c52_full_course_visual_49_source_inspection.py`: **43/43** теста × Python 3.10, 3.11, 3.12. Отрицательные тесты пытаются подменить EURUSD OANDA/SAXO на Binance2026, заявить авторскую сделку/ретроспективную 2023 candle дату, переименовать публикацию в время торговой свечи, создать фиктивное исполнение ордера, потерять один из 49 source IDs или выдать изображение за авторскую метку. Первый CI [40100024944](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40100024944) FAILED на Python syntax в многострочном if; исправлена только группировка выражения. Второй [40100103354](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40100103354) **SUCCESS 3/3**. Первое оригинальное frozen artifact CI [40100253564](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40100253564) failed только из-за Python tuple vs JSON list в **проверке** после записи (аналогичный прошлому C48 случай), нормализована сериализация в assert, **логика и восемь header claims не менялись**. Последующий полный CI [40100339396](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40100339396) **SUCCESS**; frozen JSON **52,913 байт**, Git blob `4a06ac1e1ed846f3c23adb4dba7d6f56b6afba67`, SHA256 `734fe20d117efc7b805ef407ca06ec20af663a0458732a2f4d49c2dbcbd814ec`.

## 6. Ограничения и следующий шаг

**C52 завершает фактический просмотр 49 PNG**, но не «восстанавливает» прибыльную торговую стратегию. Следующий C53 должен искать именно соответствующие **исторические OANDA EURUSD 2024/2025 (15M/1H/4H) и SAXO EURUSD 4H**, выяснить точные интервалы реальных свечей и проверить совпадение видимых OHLC/указанных уровней без подбора; параллельно создать авторские source-matched отрицательные примеры. Прежде любого course-golden требовать независимый источник провайдера и исходный chart-to-candle-id reconciliation. Если невозможно доказать, отмечать UNKNOWN / unresolved и развивать только техническую source-only модель, не подменяя авторское описание. Никаких real orders, fills or returns. **PAPER ONLY / NOT_TRADE_READY**.
