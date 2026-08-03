# EMBER Validation Log

Этот документ — постоянный журнал фактической проверки EMBER Research Engine. Здесь сохраняются команды, данные, результаты, ошибки, исправления и решения. Старые неудачные результаты не удаляются.

`PASS` относится только к конкретной проверке и не разрешает live trading.

## Правила записи

Каждая проверка должна содержать дату UTC, commit/PR, точную команду, данные, метрики, статус `PASS | FAIL | BLOCKED`, вывод и следующий шаг.

---

# Текущий статус

Актуально на 2026-08-03 после six-symbol 15000-bar validation PR #4.

| Проверка | Статус | Фактический результат |
|---|---|---|
| Установка и CI | PASS на последнем завершённом run | Python 3.10/3.11/3.12, Ruff и тесты ранее прошли; latest PR checks ожидаются |
| Unit tests | PASS | 18 тестов прошли в complete core-validation run |
| Zero look-ahead gate | PASS | Leakage tests проходят |
| Profit Factor | PASS | PF не ограничивается значением `99.0`; без убытков возвращается `inf` |
| Binance loader, 15000 bars | PASS | 6 core symbols, по 15000 свечей 15m |
| Reject diagnostics | PASS | Основные gates имеют отдельные счётчики |
| Baseline, 6 symbols | PASS | 6/6 positive, 6/6 PF > 1.5, 74 trades, avg return +8.0522% |
| Structure bias, 6 symbols | FAIL | 2/6 positive, 0/6 PF > 1.5, avg return -0.8349% |
| High-vol block, 6 symbols | PASS | 6/6 positive, 6/6 PF > 1.5, avg return +8.7512%, worst DD 2.4397% |
| Opposite-liquidity, 6 symbols | PASS с ограничением | 6/6 positive, 5/6 PF > 1.5, avg return +11.5977% |
| Baseline WFO | PASS with warning | avg PF 2.4933, stability 75%, one zero-trade fold |
| High-vol-block WFO | PASS with warning | avg PF 2.7027, stability 75%, one zero-trade fold |
| Opposite-liquidity clean WFO | PENDING | Первый WFO имел universe-selection leakage |
| Paper/live gate | BLOCKED | Нет 100 paper trades и 30 дней paper observation |

Полная таблица текущего этапа: [`CORE_VALIDATION_15000.md`](CORE_VALIDATION_15000.md).

---

# История проверок

## 2026-08-03 — Создание отдельного репозитория

**Репозиторий:** `SanChi117/EMBER-Research-Engine`

**Import commit:**

```text
5784f1e133bc7c909264290161d24522b1ebaa39
```

Проект перенесён в отдельный репозиторий. Live execution отсутствует. Добавлены data engine, features, MTF context, setups, risk, exits, portfolio, WFO, reports, virtual paper server, тесты и CI.

**Статус:** `PASS`.

---

## 2026-08-03 — Исправление Profit Factor

**Проблема:** код из Smoke искусственно ограничивал PF значением `99.0`.

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

Причина: `min(time)` и `max(time)` получили одинаковое имя столбца. Добавлены aliases и regression test.

**Commits:**

```text
c62d9b95f1a4281ac2c03215ae603a4dfc23c4e4
d5d387f9de2d0185675c2b3005f845d6b0bdecba
```

**Статус:** bug `FIXED`.

---

## 2026-08-03 — Старый synthetic sanity result

После исправления pipeline выдал:

```text
Return: +84.3983%
PF: inf
DD: 0.0000%
Trades: 46
Win rate: 100%
WFO: FAIL
```

Вывод: pipeline работал, но synthetic был искусственно идеальным и не проверял проигрыши. 1000 свечей 15m дают около 10.4 дня — недостаточно для 30-дневного train window.

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

Новый mixed-regime synthetic на 5000 свечей:

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

```text
DOGEUSDT: 5000 rows -> data/DOGEUSDT_15m_5000.csv
```

5000 свечей 15m — примерно 52 дня.

### Baseline

```text
EMA20 threshold: +/-2%
allowed_direction_contexts: down
bars_seen: 4940
neutral_context: 3644
direction_reject: 336
no_setup: 952
candidate_passed: 6
executed: 4
Return: +2.858547%
PF: 3.040922
DD: 1.400590%
Win rate: 75%
```

### Both directions

Разрешение `bull + bear` дало те же 4 сделки и те же метрики. Direction filter не был главным bottleneck: отклонённые по направлению бары перешли в `no_setup`.

### Wide profile

```text
min_confidence: 20
min_volume_ratio: 0.5
min_rr: 1.2
atr_stop_multiplier: 1.0
candidate_passed: 6
cost_gate: 6
executed: 0
```

При текущих costs RR 1.2 имеет отрицательный net edge:

```text
(1.2 - 1.0) * 0.01 - 0.0024 = -0.0004
```

**Статус:** baseline положительный, но 4 сделки статистически недостаточны.

---

## 2026-08-03 13:10 UTC — HTF bias experiment

**PR:** `#3 Compare EMA and structural HTF bias modes`

**Проверенный head commit:**

```text
b58d2d3a3cdc47766233114f30547131a1c4fe34
```

**Цель:** проверить утверждение, что EMA20 с neutral band +/-2% является главным ограничителем частоты.

В production baseline ничего не менялось. Добавлены исследовательские параметры:

```python
htf_bias_mode: Literal["ema", "structure"] = "ema"
htf_ema_period: int = 20
htf_ema_threshold_pct: float = 2.0
```

**Команда:**

```bash
python scripts/run_diagnostics.py \
  data/DOGEUSDT_15m_5000.csv \
  --out-dir results/doge_diagnostics
```

### Сводная таблица

| Profile | Neutral | Candidates | Trades | Return | PF | DD | Win rate |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline, EMA20 +/-2%, down | 3644 | 6 | 4 | +2.8585% | 3.0409 | 1.4006% | 75.0% |
| both-directions | 3644 | 6 | 4 | +2.8585% | 3.0409 | 1.4006% | 75.0% |
| EMA20 +/-0.5% | 1141 | 27 | 9 | -1.5454% | 0.7951 | 4.1552% | 44.4% |
| EMA50 +/-2% | 2716 | 14 | 8 | -0.0461% | 1.0061 | 4.1552% | 50.0% |
| structure bias | 1948 | 26 | 6 | +1.3879% | 1.5001 | 2.7171% | 50.0% |

### Вывод

1. Neutral band действительно сильно ограничивает частоту.
2. Быстрое сужение порога до `0.5%` уменьшило neutral с 73.8% до 23.1%, но ухудшило результат до PF `0.7951`.
3. EMA50 уменьшила neutral до 55.0% и дала 8 сделок, но результат около нуля.
4. Structure bias уменьшил neutral до 39.4%, увеличил candidates с 6 до 26, но исполнил только 6 сделок, а не ожидаемые 15–20.
5. Structure bias сохранил положительный результат и PF чуть выше 1.5, но выборка из 6 сделок недостаточна.
6. Baseline остался лучшим по метрикам, но также статистически ненадёжен.
7. Автоматически заменять baseline на structure bias нельзя. Оба режима должны пройти multi-symbol test на 90–180 днях.

**Решение:** оставить EMA20 +/-2% production baseline неизменным. Structure bias и EMA variants доступны только как research profiles.

**Tests:**

```text
17 passed, 1 warning
```

**Validation workflow:** `PASS`.

---

## 2026-08-03 15:04 UTC — Six-symbol 15000-bar validation

**PR:** `#4 Run 15000-bar validation across all core symbols`

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

Получено ровно `15000` свечей для каждого из шести symbols, всего `90000` свечей. Tests перед запуском:

```text
18 passed, 1 warning
```

Workflow получил технический `failure` из-за отсутствующего каталога для `tee`, но Python-run завершился, сводки и artifact были сохранены. Workflow исправлен.

### Aggregate results

| Profile | Positive symbols | PF > 1.5 | Trades | Average return | Worst DD |
|---|---:|---:|---:|---:|---:|
| baseline | 6/6 | 6/6 | 74 | +8.0522% | 3.6017% |
| structure-bias | 2/6 | 0/6 | 39 | -0.8349% | 4.0059% |
| high-vol-block | 6/6 | 6/6 | 73 | +8.7512% | 2.4397% |
| opposite-liquidity | 6/6 | 5/6 | 68 | +11.5977% | 3.7949% |

### Решения

- `structure-bias` отклонён как baseline replacement: снижение neutral не сохранило edge.
- EMA20 `+/-2%` baseline подтвердился на 6/6 symbols и остаётся control profile.
- `high-vol-block` является сильнейшим robustness candidate: выше return/PF и ниже worst DD без существенного снижения частоты.
- `opposite-liquidity` дал максимальный средний return, но ARBUSDT PF равен `1.3813`; default не изменён.

### WFO

Baseline и high-vol-block были проверены на неизменном universe из всех шести symbols:

```text
baseline: PASS, avg return 7.5725%, avg PF 2.4933, worst DD 2.9775%, stability 75%
high-vol-block: PASS, avg return 7.9156%, avg PF 2.7027, worst DD 2.9775%, stability 75%
```

Оба результата содержат один fold без сделок. Формальный статус — `PASS`, исследовательский статус — `PASS with warning`.

Первый opposite-liquidity WFO исключил ARBUSDT после просмотра full-period metrics. Этот результат считается contaminated и не используется для принятия решения. Добавлен fixed-universe runner, который не меняет symbol universe на основании будущих/full-sample результатов.

**Статус:** multi-symbol backtest `PASS`; baseline/high-vol WFO `PASS with warning`; opposite-liquidity clean WFO `PENDING`; paper/live `BLOCKED`.

Полные per-symbol результаты: [`CORE_VALIDATION_15000.md`](CORE_VALIDATION_15000.md).

---

# Следующие обязательные шаги

1. Завершить clean fixed-universe WFO для `opposite-liquidity` на всех шести symbols.
2. Не менять research default по результату одной выбранной истории: провести untouched holdout или параллельный paper comparison.
3. Использовать `baseline` как control, а `high-vol-block` как основной candidate в paper research.
4. Накопить минимум 100 завершённых paper trades и 30 календарных дней.
5. Сравнить paper metrics с backtest в пределах `+/-10%`.

---

# Повторяемые команды

```bash
# Полная six-symbol проверка
python scripts/run_core_validation.py \
  --symbols INJUSDT,TONUSDT,DOGEUSDT,ARBUSDT,NEARUSDT,OPUSDT \
  --profiles baseline,structure-bias,high-vol-block,opposite-liquidity \
  --interval 15m \
  --bars 15000 \
  --data-dir data/core_validation \
  --out-dir results/core_validation

# Fixed-universe WFO
python scripts/run_fixed_wfo.py \
  --data-dir data/core_validation \
  --out-dir results/fixed_wfo \
  --symbols INJUSDT,TONUSDT,DOGEUSDT,ARBUSDT,NEARUSDT,OPUSDT \
  --profiles baseline,high-vol-block,opposite-liquidity \
  --interval 15m \
  --bars 15000
```

---

# Live gate

Live trading остаётся запрещённым до выполнения всех условий:

```text
WFO PASS
100 completed paper trades
30 calendar days paper observation
paper metrics within +/-10% of backtest
all leakage tests PASS
```
