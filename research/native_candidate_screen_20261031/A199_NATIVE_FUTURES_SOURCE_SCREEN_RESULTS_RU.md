# A199 — результаты исходных Futures-стратегий Freqtrade, нативная проверка

Дата 31 октября 2026. Только research; не активировано ни одного PAPER/REAL ордера. Методология до результатов [A199_ORIGINAL_FUTURES_SOURCE_PREREGISTERED_RU.md](A199_ORIGINAL_FUTURES_SOURCE_PREREGISTERED_RU.md), каталог [A199_SOURCE_CANDIDATES_SHORTLIST_RU.md](A199_SOURCE_CANDIDATES_SHORTLIST_RU.md).

## A199a: точный исходник FAdxSmaStrategy (1H), Freqtrade 2026.4 — полный машинный результат

- Источник `freqtrade/freqtrade-strategies` pinned commit `f3340ce11f5bdf62f598522e64d1f5638eaa13f5`, blob `3bb13caf079e8360a959c3ad4dd2b2507f3045c0`.
- Фактически **8 Freqtrade native trade ZIP**: 4 BTC/ETH/SOL/LINK x2 комиссии, 141 день 13 мая–30 сентября 2026, реальные Binance Vision USD-M 1h + 5m detail, 1h mark и реальные settled funding, $100 stake / $1000 isolated pair wallet, no fake exchange fills (native Freqtrade candle model only).
- GitHub Actions [run #41152472760](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41152472760) **SUCCESS**, [artifact 13023278793](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41152472760/artifacts/13023278793) `sha256:29da1eeb1bd52c8f820c4c1e402a30d7d067d4ea000252adbb507eacbe289eab`. Имеются отдельные native ZIP по каждой паре+комиссии; native парсер проверил сумму фактических сделок с отчётом Freqtrade.

| Pair | N native | Комиссия 0.05% за сторону net% / PF / DD% | Комиссия 0.125% за сторону net% / PF / DD% | Доля top3 в gross winners при 0.05% |
|---|---:|---|---|---:|
| BTC | 4 | −0.120979% / 0.17422 / 0.12612% | −0.165836% / 0.08728 / 0.16584% | 100% |
| ETH | 6 | −0.750933% / 0.04526 / 0.75093% | −0.840406% / 0.02404 / 0.84041% | 100% |
| SOL | 4 | −0.383959% / 0 / 0.38396% | −0.443427% / 0 / 0.44343% | нет прибыльных сделок |
| LINK | 9 | **+0.336837%** / 1.37798 / 0.88979% | **+0.217082%** / 1.22466 / 0.96509% | **98.191%** |

Совокупно **23 native Freqtrade сделки на 4 отдельных wallets за 141 день ≈ 0.163/day**, не портфельная оценка, никакие проценты не суммируются. **Предварительный gate = FAIL 0 из 4**: требовались >=2/4 с N>=35, net>0 обе комиссии, PF>=1.2, DD<15%, top3 <60% gross winners; сама частота не достигла минимального 1/день для четырёх пар. Рост плеча проблему редкости/низкого математического ожидания не исправит.

## A199b: исходник FReinforcedStrategy (5m) и точная совместимость

- Original `FReinforcedStrategy.py` blob `11bfdde9fcecf772a2d223c88b9ee62bfd8737d3`, commit такой же. 5m EMA8/21 крест и 1h SMA50 trend, ADX exit, long+short, stoploss -5%.
- Первичная попытка native Freqtrade==2026.4 BLOCKED **до любой сделки**, поскольку три `IntParameter` объявлены в оригинале **без обязательного явного space**, и движок возвращает `Cannot determine parameter space for adx_period`. Это реальная техническая несовместимость опубликованного старого примера с выбранной версией Freqtrade, **не отрицательная доходность**.
- Подготовлено `a199_freinforced_metadata_compat_only.py`: проверяет оригинальный blob и создаёт отдельную исследовательскую копию с **тремя изменениями только `space='buy'` metadata**, все периодные значения, веса, stop/exit/ROI сигналы — без изменений. В будущих цифрах **обязательно маркировать «original logic, metadata patched»**, нельзя называть «source-byte-identical Freqtrade».
- Программа теста по-прежнему тот же нативный Freqtrade, реальные данные, 4 pairs×2 fees. Пока нет 8 actual successful native receipts, **результат этой ветви PENDING/TECHNICALLY BLOCKED**. Никакой доходности не придумывать.

## Проблема цели
Официальный `freqtrade/freqtrade-strategies` — репозиторий примеров, а не гарантированно прибыльных систем. Бессмысленно выбирать красивую лучшую монету из четырёх после уже просмотренной истории; требуется новая цена/режим, проверка смещения и stress расходов. Даже положительные 2026 исторические прогоны — screening, не untouched future OOS.

**Реальные сделки / SMOKE / планировщики: НЕ МЕНЯЛИСЬ.**
