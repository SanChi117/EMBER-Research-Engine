# B1/C71 — первое ЗАКРЫТОЕ 15m VC-source или 1H BOS-source после фактического первого 3m касания

Дата UTC: 25 октября 2026; repo `SanChi117/EMBER-Research-Engine`, ветка `research/academic-engine-recovery-20261015`. **Криптовалютные данные Binance USD-M; PAPER ONLY; NOT_TRADE_READY; 0 ордеров.**

## 1. Исходная академия — не подменять геометрией

Оригинальные файлы пользователя из Google Drive прочитаны напрямую:

- `2. Entry by IMB & SNR.txt` — ID `1hkKKwy60-VIoqEsVYAq12mnPZA7ySXFQ`. При **действительном тесте 4H POI** допустима **1H Trigger** по SSL, BSL либо правильному IMB и **только затем** вход через **15m VC IMB/SNR**. При отсутствии 1H Trigger: **1H VC IMB/SNR/RB** формирует новую 1H POI, требуется **действительный тест этой 1H POI**, далее 15m Trigger SSL/BSL/IMB и **5m VC**, либо при отсутствии trigger **15m VC IMB/SNR**. Автор отдельно: если на 4H происходит Liquidity Raid, **1H Trigger считается отсутствующим**, ожидается 1H VC. Нельзя смешивать эти ветки. Вложенная 1H IMB внутри 4H IMB не автоматически trigger. Не всякая VC является входом: только IMB или SNR в соответствующей ветке.
- `Strong High & Low.txt` — ID `1lvPRbhfM6ZjfW7UP-30y9uND1R6VC13t`. StrongHL образуется от **контакта с liquidity ИЛИ inefficiency**, **ЗАТЕМ** подтверждения движения через настоящую **VC POI или BOS** на том же/младшем TF. Голые границы wick, 3m, 15m gaps или source fractal-BOS — **не сертифицированный StrongHL**.

Принципиальное ограничение: нет **авторски размеченных** crypto Binance `symbol + UTC + original OHLCV ZIP SHA + positive/negative VALID POI test, VC/BOS/StrongHL`. Видео/графики курса описывают логику; мы **не присваиваем** найденным исходным криптосвечам степень достоверности преподавателя.

## 2. Сделано в C71

- [x] Новый модуль `d05/c71_post_contact_closed_15m_vc_1h_bos_semantic_gate.py`. Строго принимает только C67 Route A source fork, C69 точный native15m preknown raid/POI wick и C70 **физически первую** signed native3m свечу. **Повторно сам пересчитывает C70 из original SHA native3m и full 15m Decimal 5-to-1 OHLCV**, сверяет ВСЕ поля frozen source receipt — нельзя внедрить поддельные ID, цену, час подтверждения, 1H Trigger/POI и перескочить к «VC».
- [x] Ворота времени: (gate = \max(\mathrm{first\ original\ 3m\ wick\ close},\mathrm{source\ 1h\ full\ close})). Первая реально закрытая 3m свеча выдает координату касания, но **не даёт знания о 1H рейде до закрытия всей часовой свечи**. **Весь** паттерн будущего 15m или 1H подтверждения обязан **НАЧАТЬСЯ после ворот**, не только закончиться после ворот. Учитывается лишь закрытый native15m SNR/IMB source candidate либо original closed 1H source fractal BOS. No lookahead, mixed TF chronology, first ANY: противоположная сторона, совпадения времени и нескольких source-паттернов сохраняются, не выбирается удобный поздний сигнал. Окно 24h и правоцензура.
- [x] Две ветви: C67 `TRIGGER` source 1H RAID → первое 15m IMB/SNR source событие, но **не author VC**; C67 `NEW_1H_VC_POI` → C69/C70 технический FIRST native 15m/3m wick POI source retest → первое 15m source событие, однако по данным исходных свечей **невозможно** определить, реальный ли это owner 15m Trigger→5m VC или owner 15m VC; статус `TRIGGER_VS_VC_UNRESOLVED`. Если сначала source BOS, он не заменяет нужную по Route A реальную VC. Route B IDM и Route C raid→BOS не подключены; author POI, VC, BOS, StrongHL, stops = false.
- [x] `d05/test_c71_post_contact_closed_15m_vc_1h_bos_semantic_gate.py`: **30 негативных сценариев × Python3.10/3.11/3.12**: first source candidate opposite, two sides same time, two kinds same time, native15m vs source1H BOS tie, owner proof forgery, original source3m SHA-price proof recomputed, delayed versus premature 1H close, right-censor, no follow, parent no contact, Route B/C isolation, absent 5m VC. [CI 40225011430](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40225011430) **SUCCESS 3/3**.
- [x] Полный `tests/probe_c71_original45zip_after_first3m_contact_vc_bos.py`: оригинальные **45 SHA-verified signed ZIP Binance USD-M** BTC/ETH/SOL/XRP/BCH за **Sep 01–Oct 02 2026**. Всего **76800 оригинальных native3m**, **15360 оригинальных native15m**, **160 native1d**, **3840 закрытых derived1h**. Каждая из **153** ранее frozen C46 4H source parent заново исследована, пересчитаны и независимо сравнены старые неизменённые C46/C60/C62/C63/C66/C67/C68/C69/C70 SHA/rawID/price исходники. Первый реальный [CI 40225168132](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40225168132) **SUCCESS 5/5**; **второе независимое скачивание ВСЕХ 45 ZIP** с побайтным сопоставлением полной C71 JSON [CI 40225345999](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40225345999) **SUCCESS 4/4**, 30×3 тестов вновь прошло. Полный frozen source `evidence/c71/C71_ORIGINAL45ZIP_3M_CONTACT_THEN_FIRST_ANY_15M_VC_OR_1H_BOS_SOURCE.json` **264632 bytes**, SHA256 `b02777bc871e6471d349989179da3452df6a185c4db805cf5b6071e5a377b253`, Git blob `ef05ecdcfb31e59dec79d10eb5d3dc40b3c3af97`; отдельный witness `evidence/c71/C71_INDEPENDENT_ORIGINAL45ZIP_POST3M_15M_VC_1H_BOS_WITNESS_20261025.json`.

## 3. Исходные результаты: 153 технических контекста 4H, не независимые сделки

| Первый post-contact технический source-статус | Наблюдений |
|---|---:|
| Нет однозначной C69/C70 first3m liquidity/POI source ветви | **95** |
| Первое подтверждающее событие идёт в **противоположную сторону** | **32** |
| Первый 15m source IMB после закрытого 1H Trigger-raid, совпадает направление | **8** |
| Первый 15m source SNR после 1H Trigger-raid, совпадает направление | **3** |
| Первый 15m source IMB после предлагаемой NEW 1H POI, но Trigger vs VC не доказано | **6** |
| Первый 15m source SNR после NEW 1H POI, Trigger vs VC не доказано | **6** |
| Два типа 15m source одновременно, нельзя произвольно выбрать | **2** |
| Нет дальнейшего source события до конца выборки (правоцензура) | **1** |
| **Всего** | **153** |

В этом 32-дневном original crypto периоде не обнаружены категории, где первым событием оказался source 1H BOS (отлично от утверждения, что BOS «никогда не бывает»); все остальные zero status сохранены явно в frozen JSON. **23** aligned 15m source confirmations — технические наблюдения, не verified volume confirmation, не сделки, не оценка winrate. На текущих криптосвечах **0 реальных авторских goldens**, **0 авторски подтверждённых** 4H/1H first VALID POI test, 1H Trigger, 15m/5m VC, BOS, StrongHL, FTA/SL/TP.

## 4. Контрпроверка и коррекция

В первом прогоне негативных тестов [CI 40224890006](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40224890006) поймана ошибка: actual original3m close не обязан лежать на 15m сетке; **нужно проверять native3m** и затем фильтровать только более поздние 15m паттерны. Исправлена проверка в C71. В следующем [CI 40224949606](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40224949606) отрицательные случаи BOS были искусственно созданы **до** actual source3m contact, поэтому корректно отвергались алгоритмом; обновлены **синтетические** события, исходные цены не менялись. Итог [CI 40225011430](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40225011430) и два полных original45 ZIP успешны.

## 5. Что дальше C72 (не сделано)

Интерпретация `source VC / actual POI first VALID test` требует действительно **author labelled** crypto positive+negative goldens. C72 логично расширить **только research** схему подтверждения на реальный native5m source для ветки NEW 1H POI→15m Trigger→5m VC, отделив 5m VC от 15m VC, найти условия инвалидации, подтверждения StrongHL/структурного SL и `FTA`, но **не придумывать**, будто техническая геометрия автоматически доказывает соответствие академии. Затем OOS PAPER c комиссиями, проскальзыванием, SL-first intrabar и без lookahead — до интеграции в SMOKE.

### A141 SHA приемка

После двойного оригинального ZIP и 30×3: заморозить ровно **шесть SHA evidence**: C71 module, C71 30 tests, C71 fresh original45 probe, полный 264632-byte JSON, independent witness, **этот report**. Старый SHA journal `A140/140 f799fa6b65ae8044971fa95e355fca9c8e228e2dbf90cd3108081b39ab6d21bb`; append A141 **один раз**; независимый SHA check 141/141 × Python3.10/3.11/3.12, все старые Git SHA неизменны. После заморозки не редактировать шесть evidence-файлов, обновлять только handoff/map.

**PAPER ONLY | NOT_TRADE_READY | orders=0 | fills=0 | trades=0 | PnL отсутствует.**
