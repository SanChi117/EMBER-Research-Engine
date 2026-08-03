# EMBER Validation Log

Этот документ — постоянный журнал фактической проверки EMBER Research Engine. Здесь сохраняются команды, данные, результаты, ошибки, исправления и решения. Старые неудачные результаты не удаляются.

`PASS` относится только к конкретной проверке и не разрешает live trading.

## Правила записи

Каждая проверка должна содержать дату UTC, commit/PR, точную команду, данные, метрики, статус `PASS | FAIL | BLOCKED`, вывод и следующий шаг.

---

# Текущий статус

Актуально после Portfolio WFO OOS и реализации ТЗ `EMBER Research Engine — Portfolio WFO & Universe Expansion`, версия 1.0.

| Проверка | Статус | Фактический результат |
|---|---|---|
| Установка и CI | PASS | Python 3.10/3.11/3.12, Ruff и leakage tests проходят на последнем завершённом этапе |
| Unit tests | PASS | 22 теста прошли в Portfolio WFO run; новый protocol gate покрыт отдельными тестами |
| Zero look-ahead gate | PASS | Leakage tests проходят |
| Profit Factor | PASS | PF не ограничивается `99.0`; при прибыли без убытков возвращается `inf` |
| Binance loader, 15000 bars | PASS | 6 core symbols и 4 frozen OOS symbols, по 15000 свечей 15m |
| Reject diagnostics | PASS | Основные gates имеют отдельные счётчики |
| Baseline, core 6 | PASS | 6/6 positive, 6/6 PF > 1.5, 74 trades, avg return +8.0522% |
| Structure bias, core 6 | FAIL | 2/6 positive, 0/6 PF > 1.5, avg return -0.8349% |
| High-vol-block, core 6 | PASS | 6/6 positive, 6/6 PF > 1.5, 73 trades, avg return +8.7512%, worst DD 2.4397% |
| Opposite-liquidity, core 6 | PASS с ограничением | 6/6 positive, 5/6 PF > 1.5, avg return +11.5977% |
| Baseline portfolio WFO, core 6 | PASS with warning | avg PF 2.4933, stability 75%, один zero-trade fold |
| High-vol-block portfolio WFO, core 6 | PASS with warning | avg PF 2.7027, stability 75%, один zero-trade fold |
| Opposite-liquidity clean WFO | PENDING | Первый WFO имел universe-selection leakage |
| OOS 4 alts, full period | PASS with warning | 3/4 positive с PF > 1.5, но всего 22 сделки |
| OOS 4 alts, per-symbol WFO | FAIL | Только FET PASS_WITH_WARNING; 7/16 folds без сделок |
| OOS 4 alts, portfolio WFO | FAIL | stability 50%, total test trades 8, folds `0/0/4/4` |
| Universe Expansion 20 | BLOCKED | По ТЗ разрешён только после Portfolio WFO PASS |
| Paper gate | BLOCKED | Нет 100 completed paper trades и 30 дней observation |
| Live gate | BLOCKED | Формальные paper/live условия не выполнены |

Основные документы:

- [`CORE_VALIDATION_15000.md`](CORE_VALIDATION_15000.md)
- [`OUT_OF_SAMPLE_4ALTS.md`](OUT_OF_SAMPLE_4ALTS.md)
- [`PORTFOLIO_WFO_OOS.md`](PORTFOLIO_WFO_OOS.md)

---

# История проверок

## 2026-08-03 — Создание отдельного репозитория

**Репозиторий:** `SanChi117/EMBER-Research-Engine`

**Import commit:**

```text
5784f1e133bc7c909264290161d24522b1ebaa39
```

Проект перенесён в отдельный repository. Live execution отсутствует. Добавлены data engine, features, MTF context, setups, risk, exits, portfolio, WFO, reports, virtual paper server, tests и CI.

**Статус:** `PASS`.

---

## 2026-08-03 — Исправление Profit Factor

**Проблема:** исходный код искусственно ограничивал PF значением `99.0`.

**Исправление:**

```python
if gross_loss == 0:
    return float("inf") if gross_profit > 0 else 0.0
return gross_profit / gross_loss
```

**Commit:**

```text
b61ddc946b0d1bd0e096c870f06fc6d80ef56010
```

**Статус:** `PASS`.

---

## 2026-08-03 — Первый synthetic запуск и WFO bug

**Команда:**

```bash
python scripts/run_demo.py --out-dir results/demo --bars 1000
```

**Ошибка:**

```text
polars.exceptions.DuplicateError:
projections contained duplicate output name 'time'
```

Причина: `min(time)` и `max(time)` получили одинаковое имя. Добавлены aliases и regression test.

**Commits:**

```text
c62d9b95f1a4281ac2c03215ae603a4dfc23c4e4
d5d387f9de2d0185675c2b3005f845d6b0bdecba
```

**Статус:** bug `FIXED`.

---

## 2026-08-03 — Старый synthetic sanity result

```text
Return: +84.3983%
PF: inf
DD: 0.0000%
Trades: 46
Win rate: 100%
WFO: FAIL
```

Pipeline работал, но synthetic был искусственно идеальным. 1000 свечей 15m дают около 10.4 дня и недостаточны для 30-дневного train window.

**Статус:** execution `PASS`, realism `FAIL`, WFO `FAIL`.

---

## 2026-08-03 — Первые реальные данные, 1000 свечей

**Symbols:** `INJUSDT, TONUSDT, DOGEUSDT, ARBUSDT, NEARUSDT, OPUSDT`.

| Symbol | Trades | Return | PF | DD | Win rate |
|---|---:|---:|---:|---:|---:|
| INJUSDT | 0 | 0.0000% | 0.0 | 0.0000% | 0% |
| TONUSDT | 1 | -1.1910% | 0.0 | 1.1910% | 0% |
| DOGEUSDT | 0 | 0.0000% | 0.0 | 0.0000% | 0% |
| ARBUSDT | 0 | 0.0000% | 0.0 | 0.0000% | 0% |
| NEARUSDT | 2 | -2.8383% | 0.0 | 2.8383% | 0% |
| OPUSDT | 1 | -1.4867% | 0.0 | 1.4867% | 0% |

Всего: 4 сделки, 0 прибыльных, 3 symbols без сделок.

**Статус:** `FAIL`; выборка также слишком короткая.

---

## 2026-08-03 12:18 UTC — Reject diagnostics и mixed synthetic

**PR #2 merge commit:**

```text
95852800f3247cedb7192784bda25890543def38
```

Добавлены counters:

```text
bars_seen, neutral_context, direction_reject, regime_reject,
no_setup, setup_blocked, confidence_low, volume_low,
candidate_passed, risk_none, rr_low, cost_gate,
quality_reject, structure_reject, no_future,
overlap_reject, portfolio_reject, halted, executed
```

Mixed-regime synthetic, 5000 свечей:

```text
neutral_context: 1008
no_setup: 3637
candidate_passed: 288
executed: 3
Return: -3.9040%
PF: 0.0
DD: 3.9040%
Win rate: 0%
WFO: FAIL
```

После трёх последовательных убытков сработал kill switch.

**Статус:** diagnostics `PASS`, strategy sanity `FAIL`.

---

## 2026-08-03 12:18 UTC — DOGEUSDT, 5000 реальных свечей

**Команда:**

```bash
python scripts/fetch_binance.py \
  --symbols DOGEUSDT \
  --interval 15m \
  --limit 5000 \
  --out-dir data
```

### Baseline

```text
EMA20 threshold: +/-2%
allowed_direction_contexts: down
neutral_context: 3644
candidate_passed: 6
executed: 4
Return: +2.858547%
PF: 3.040922
DD: 1.400590%
Win rate: 75%
```

### Both directions

Разрешение `bull + bear` дало те же 4 сделки и метрики. Direction filter не был главным bottleneck.

### Wide profile

```text
min_confidence: 20
min_volume_ratio: 0.5
min_rr: 1.2
candidate_passed: 6
cost_gate: 6
executed: 0
```

При текущих costs RR 1.2 имел отрицательный net edge.

**Статус:** baseline положительный, но 4 сделки статистически недостаточны.

---

## 2026-08-03 13:10 UTC — HTF bias experiment

**PR #3 merge commit:**

```text
38af783230fff80695519ba4e1b9b3290f2a49d5
```

| Profile | Neutral | Candidates | Trades | Return | PF | DD |
|---|---:|---:|---:|---:|---:|---:|
| baseline EMA20 +/-2% | 3644 | 6 | 4 | +2.8585% | 3.0409 | 1.4006% |
| both-directions | 3644 | 6 | 4 | +2.8585% | 3.0409 | 1.4006% |
| EMA20 +/-0.5% | 1141 | 27 | 9 | -1.5454% | 0.7951 | 4.1552% |
| EMA50 +/-2% | 2716 | 14 | 8 | -0.0461% | 1.0061 | 4.1552% |
| structure bias | 1948 | 26 | 6 | +1.3879% | 1.5001 | 2.7171% |

Neutral band ограничивал частоту, но его ослабление ухудшило edge. Structure bias не дал достаточной выборки.

**Решение:** EMA20 `+/-2%` baseline не менять; alternatives остаются research-only.

**Tests:** `17 passed, 1 warning`.

**Статус:** experiment `PASS`, replacement decision `REJECTED`.

---

## 2026-08-03 15:04 UTC — Core Validation 15000 Bars

**PR #4 merge commit:**

```text
ef08886f4251b3eb741965d01691cad768fbbde9
```

**Complete run:** `30823347050`  
**Artifact:** `8860720831`

**Команда:**

```bash
python scripts/run_core_validation.py \
  --symbols INJUSDT,TONUSDT,DOGEUSDT,ARBUSDT,NEARUSDT,OPUSDT \
  --profiles baseline,structure-bias,high-vol-block,opposite-liquidity \
  --interval 15m \
  --bars 15000 \
  --data-dir data/core_validation \
  --out-dir results/core_validation
```

| Profile | Positive symbols | PF > 1.5 | Trades | Avg return | Worst DD |
|---|---:|---:|---:|---:|---:|
| baseline | 6/6 | 6/6 | 74 | +8.0522% | 3.6017% |
| structure-bias | 2/6 | 0/6 | 39 | -0.8349% | 4.0059% |
| high-vol-block | 6/6 | 6/6 | 73 | +8.7512% | 2.4397% |
| opposite-liquidity | 6/6 | 5/6 | 68 | +11.5977% | 3.7949% |

Fixed-universe WFO:

```text
baseline: PASS, avg return 7.5725%, avg PF 2.4933, worst DD 2.9775%, stability 75%
high-vol-block: PASS, avg return 7.9156%, avg PF 2.7027, worst DD 2.9775%, stability 75%
```

Оба результата имеют один zero-trade fold, поэтому исследовательский статус — `PASS with warning`.

Первый opposite-liquidity WFO исключил ARBUSDT после просмотра full-period metrics и считается contaminated.

**Статус:** core backtest `PASS`; baseline/high-vol WFO `PASS with warning`; clean opposite WFO `PENDING`; paper/live `BLOCKED`.

**Документ:** [`CORE_VALIDATION_15000.md`](CORE_VALIDATION_15000.md).

---

## 2026-08-03 — Out-of-Sample 4 Alts

**PR #5 merge commit:**

```text
a9643475d0d92b803881597d1ade64d4beaa8296
```

**Run:** `30842493927`  
**Artifact:** `8867628034`

**Команда:**

```bash
python scripts/run_oos_validation.py \
  --symbols PEPEUSDT,FETUSDT,WIFUSDT,SUIUSDT \
  --interval 15m \
  --bars 15000 \
  --data-dir data/oos_4alts \
  --out-dir results/oos_4alts
```

| Symbol | Trades | Return | PF | DD | Per-symbol WFO |
|---|---:|---:|---:|---:|---|
| PEPEUSDT | 2 | -0.7258% | 0.4354 | 1.2731% | FAIL |
| FETUSDT | 5 | +5.0364% | 4.7226 | 1.3356% | PASS_WITH_WARNING |
| WIFUSDT | 7 | +2.5706% | 1.7209 | 2.3623% | FAIL |
| SUIUSDT | 8 | +5.8600% | 2.9848 | 2.8903% | FAIL |

Full-period criterion: `PASS 3/4`, но всего 22 completed trades. Только FET прошёл individual WFO с предупреждением; 7/16 folds имели zero trades.

**Статус:** `PASS with warning`; statistical confidence `LOW`; portfolio WFO required; live `BLOCKED`.

**Документ:** [`OUT_OF_SAMPLE_4ALTS.md`](OUT_OF_SAMPLE_4ALTS.md).

---

## 2026-08-03 — Portfolio WFO OOS

**PR #6 merge commit:**

```text
3fbc6301d365e32716afa4b378ab3bbed014d885
```

**Workflow run:** `30847701247`  
**Artifact:** `8869390031`  
**Artifact SHA-256:** `eac603f9d2e2677adef0dab60f374cfa9773b0fc52dd9e0b5ae2091b7f2f5803`

**Canonical command:**

```bash
python scripts/run_portfolio_wfo.py \
  --data-dir frozen_oos/data/oos_4alts \
  --symbols PEPEUSDT,FETUSDT,WIFUSDT,SUIUSDT \
  --profile high-vol-block \
  --interval 15m \
  --bars 15000 \
  --initial-equity 10000 \
  --out-dir results/portfolio_wfo_oos \
  --report-path docs/PORTFOLIO_WFO_OOS.md
```

| Fold | Return | PF | DD | Trades |
|---:|---:|---:|---:|---:|
| 1 | 0.0000% | 0.0000 | 0.0000% | 0 |
| 2 | 0.0000% | 0.0000 | 0.0000% | 0 |
| 3 | +0.6424% | 1.2750 | 2.4592% | 4 |
| 4 | +6.1017% | `inf` | 0.0000% | 4 |

```text
Avg Return: +1.6860%
Avg PF: inf
Worst DD: 2.4592%
Stability: 50.00%
Total completed test trades: 8
Zero-trade folds: 2/4
Status: FAIL
```

Полный protocol gate требует одновременно stability `>=70%`, avg PF `>=1.5`, worst DD `<10%`, avg return `>0%` и total trades `>=20`. Проверка провалила stability и minimum trade count.

Оценка `0.14 × 4 = 0.56 trades/day` была двойным подсчётом уже объединённого портфеля. Фактическая full-period density: `22 / 156.24 = 0.141 portfolio trades/day`; ожидаемая плотность 25-дневного fold — около 3.5 trades, что соответствует `0/0/4/4`.

PEPE нельзя удалить задним числом: это universe-selection leakage.

**Статус:** Portfolio WFO `FAIL`; Universe Expansion 20 `BLOCKED`; paper/live `BLOCKED`.

**Документ:** [`PORTFOLIO_WFO_OOS.md`](PORTFOLIO_WFO_OOS.md).

---

## 2026-08-04 — Реализация ТЗ Portfolio WFO & Universe Expansion v1.0

Добавлены и приведены к именам из ТЗ:

```text
scripts/run_portfolio_wfo.py
docs/PORTFOLIO_WFO_OOS.md
docs/PORTFOLIO_WFO_OOS.json
tests/test_portfolio_wfo.py
```

Runner:

- загружает ровно четыре frozen CSV;
- проверяет `15000` строк и symbol column каждого файла;
- объединяет данные в один multi-symbol Polars DataFrame;
- использует один `WalkForwardValidator` для portfolio mode;
- фиксирует 4 folds, 30-day lookback и 3-bar embargo;
- применяет дополнительный protocol gate `total_trades >= 20`;
- выдаёт понятную ошибку без traceback для ожидаемых input failures;
- сохраняет Markdown и JSON;
- имеет `if __name__ == "__main__"` guard и type hints.

Workflow повторно скачивает неизменный OOS artifact, запускает canonical runner и сравнивает с сохранённым factual JSON.

Universe Expansion scripts/data не создавались и test не запускался, потому что условие ТЗ `Portfolio WFO = PASS` не выполнено.

**Статус:** Task 1 `COMPLETE / FAIL result`; Task 2 `COMPLETE`; Task 3 `BLOCKED BY SPEC`.

---

# Следующие обязательные шаги

1. Не запускать Universe Expansion 20 по текущему ТЗ: prerequisite Portfolio WFO PASS не выполнен.
2. Не исключать PEPE и не менять `min_confidence`, `min_rr` или setup detector по просмотренному OOS результату.
3. Любую новую universe-selection hypothesis заранее зафиксировать и проверять на новом непересекающемся периоде или новом predeclared universe.
4. Завершить clean fixed-universe WFO для `opposite-liquidity` на всех шести core symbols как отдельную незавершённую проверку.
5. Не включать paper/live до выполнения формальных gates.

---

# Повторяемые команды

```bash
# Core six-symbol validation
python scripts/run_core_validation.py \
  --symbols INJUSDT,TONUSDT,DOGEUSDT,ARBUSDT,NEARUSDT,OPUSDT \
  --profiles baseline,structure-bias,high-vol-block,opposite-liquidity \
  --interval 15m \
  --bars 15000 \
  --data-dir data/core_validation \
  --out-dir results/core_validation

# Core fixed-universe WFO
python scripts/run_fixed_wfo.py \
  --data-dir data/core_validation \
  --out-dir results/fixed_wfo \
  --symbols INJUSDT,TONUSDT,DOGEUSDT,ARBUSDT,NEARUSDT,OPUSDT \
  --profiles baseline,high-vol-block,opposite-liquidity \
  --interval 15m \
  --bars 15000

# Canonical OOS portfolio WFO
python scripts/run_portfolio_wfo.py \
  --data-dir frozen_oos/data/oos_4alts \
  --symbols PEPEUSDT,FETUSDT,WIFUSDT,SUIUSDT \
  --profile high-vol-block \
  --interval 15m \
  --bars 15000 \
  --initial-equity 10000 \
  --out-dir results/portfolio_wfo_oos \
  --report-path docs/PORTFOLIO_WFO_OOS.md
```

---

# Live gate

Live trading остаётся запрещённым до выполнения всех условий:

```text
relevant WFO PASS
100 completed paper trades
30 calendar days paper observation
paper metrics within +/-10% of backtest
all leakage tests PASS
```
