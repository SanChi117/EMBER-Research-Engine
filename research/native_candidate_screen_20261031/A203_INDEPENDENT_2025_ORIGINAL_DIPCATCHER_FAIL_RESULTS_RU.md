# A203 — независимый holdout оригинальной стратегии dip_catcher (2025 May–Sep): ECONOMIC FAIL 0/4, full evidence

Дата 31.10.2026. **RESEARCH/PAPER ONLY** — ни новая стратегия, ни сделки, ни планы SMOKE не запускались.

## Исходник и чёткий независимый период

- Same byte-original as A202: `viktors1982/trading@e572140b1b8cb550cb244c67d363087b81bd4ab8` `freqtrade/strategies/dip_catcher.py` blob `76ab2b3f91dc7beaa0be8021a245caa2b3f4186f`, Freqtrade `2026.4`; original stoploss **-8% цены**, decreasing ROI 3%→2%→1%, 5m, LONG+SHORT, 1×, no DCA.
- Frozen prereg `A203_DIPCATCHER_2025_FROZEN_HOLDOUT_PREREG_RU.md` committed BEFORE data. Compare original A202 May–Sep2026 economic PASS3/4, speed/risk FAIL.
- **A203 true independent historic source:** 2025-05-13–2025-09-30 UTC (141d evaluation), May1–Sep30 source full 153d Binance Futures USD-M. Four separate $1000 wallets, proposed $100 nominal stake, single position per symbol, 5bps and 12.5bps fee each fill. Binance monthly **80 source ZIP receipts** (4 coins × 5 months × 4 kinds klines5m / klines1h / mark1h / fundingRate). Each source ZIP SHA256 and CSV SHA256 recorded, no synthetic candles, exact 44,064 continuous 5m and 3,672 continuous 1h/mark per symbol; 459 settled genuine funding receipts per symbol, hourly zeros otherwise. Manifest `A203_2025_SOURCE_SHA_MANIFEST.json`.
- GitHub Actions [run 41157269206](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41157269206): **SUCCESS**, 8 original native Freqtrade ZIP trade archives, SHA256 cross-check and PREDECLARED gate. Artifact ID **13026131241**, outside ZIP independently downloaded and SHA256 `c075e454965b54901c82c17392dbe9d7892e4649fb44d9d9ffd313200c09747c`, matches artifact GitHub digest. **Independent re-open of all eight inner ZIPs**, all numbers of trade rows, sum of per-trade absolute PnLs, individual SHA, leverage=1× independently verified PASS.

## Два уровня расходов, четыре отдельные кошелька

| Пара | N BASE / STRESS | net BASE wallet | PF BASE | net STRESS wallet | PF STRESS | Economic pair PASS |
|---|---:|---:|---:|---:|---:|---|
| BTC | 40 / 36 | **−4.181634%** | 0.45151 | **−4.720316%** | 0.38670 | NO |
| ETH | 176 / 158 | +0.547937% | 1.03097 | **−2.409953%** | 0.86670 | NO |
| SOL | 216 / 197 | +3.280288% | 1.17558 | **−0.328066%** | 0.98350 | NO |
| LINK | 239 / 221 | **−0.401393%** | 0.98451 | **−3.789315%** | 0.85625 | NO |

**ECONOMIC PASS 0/4.** Gate requires >=2 symbols simultaneously at both fees N>=35, net>0, PF>=1.20, walletDD<15%, top3 winners<60%. Original code not retuned, no best-case selection. 2025 benchmark source unseen in A202, after Freqle original 2022–2024 period, but not actual forward-live as of Oct2026.

## Принудительная постоянная экспозиция на другой истории — подтверждена

Для BASE 2025 по четырём отдельным кошелькам 671 closed trades/141d = **4.76 закрытий/сутки**; STRESS 612/141=**4.34/сутки**. Но это **не** 4–5 независимых A+ signals/day.

Независимая временная sweep-проверка всех `open_date, close_date` trade ZIP:
- Все **4 из 4 позиции открыты одновременно 98.24% времени BASE** (98.33% STRESS). Слоты постоянно заняты.
- Каждый из **667/667** последовательных BASE повторных входов открывался <=5 минут после предыдущего выхода на том же символе; STRESS **608/608** повторных входов <=5 минут. Механизм почти постоянно пытается быть в рынке.
- Median/p90 BASE HOLD по BTC **18.33h/289.17h**, ETH **4.92h/54.29h**, SOL **5.67h/46.63h**, LINK **3.5h/43.43h**. Speed gate FAIL 0/4 (p90>24h).
- Риск SL 8% цены, а не 8% от депозита. Не допускает «взять» 20–30× без ликвидаций/неприемлемой просадки.

## Прямое сравнение A202 против A203, фиксированные params

| Пара | A202 BASE net wallet (2026) | A203 BASE net wallet (2025) | OOS conclusion |
|---|---:|---:|---|
| BTC | +2.108% | **−4.182%** | sign flip |
| ETH | +6.432% | +0.548% | near flat, stress negative |
| SOL | +3.863% | +3.280% | stress PF<1.2 both years |
| LINK | +5.760% | **−0.401%** | sign flip |

**A203 = economic FAIL 0/4; speed FAIL 0/4; risk FAIL; execution approval FALSE.**

Это фактическая фальсификация экономической переносимости A202 на другую ранее неиспользованную для этого кандидата 141-дневную историческую выборку. Гораздо показательнее, что A203 с **более высокой частотой (~4.76 закрытых/сутки) оказался убыточным по большинству пар**, в отличие от A202 c меньшей частотой (~3.33/сутки) и положительным результатом.

## Вывод без подгонки

- `dip_catcher` не считать доказанной прибыльной системой. Не «исправлять» его стоп и не переносить только благополучные результаты A202; архивировать и сохранять полезную инфраструктуру (SHA Binance source, original Freqtrade native harness, audit trades, fee stress, occupancy).
- Для следующего кандидата заранее требовать **реальный causal event-entry**, ограничение долгого удержания, без автоматического ре-энтри через 5m после каждого выхода, разумную близость SL относительно TP и risk cap.
- Не продолжать тесты на повторно использованных May–Sep2026 как «OOS». Желательны независимый диапазон/последовательный настоящей forward PAPER без ретюнинга.
- Никаких новых реальных или виртуальных ордеров, изменений существующих расписаний/SMOKE.
