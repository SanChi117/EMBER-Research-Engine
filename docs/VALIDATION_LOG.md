# EMBER Validation Log

Этот документ — постоянный журнал фактической проверки EMBER Research Engine. Здесь сохраняются команды, данные, результаты, ошибки, исправления и решения. Старые неудачные результаты не удаляются.

`PASS` относится только к конкретной проверке и не разрешает live trading.

## Правила записи

Каждая проверка должна содержать дату UTC, commit/PR, точную команду, данные, метрики, статус `PASS | FAIL | BLOCKED`, вывод и следующий шаг.

---

# Текущий статус

Актуально на 2026-08-03 после HTF bias experiment PR #3.

| Проверка | Статус | Фактический результат |
|---|---|---|
| Установка и CI | PASS | Python 3.10/3.11/3.12, Ruff и тесты проходят |
| Unit tests | PASS | 17 тестов прошли в validation workflow |
| Zero look-ahead gate | PASS | Leakage tests проходят |
| Profit Factor | PASS | PF не ограничивается значением `99.0`; без убытков возвращается `inf` |
| Binance loader, 1000 bars | PASS | 6 core symbols загружены |
| Paginated Binance loader | PASS | DOGEUSDT: 5000 свечей 15m |
| Reject diagnostics | PASS | Основные gates имеют отдельные счётчики |
| Baseline DOGE 5000 | PASS с ограничением | 4 сделки, +2.8585%, PF 3.0409, DD 1.4006% |
| EMA threshold 0.5% | FAIL | 9 сделок, -1.5454%, PF 0.7951 |
| EMA50 | FAIL | 8 сделок, -0.0461%, PF 1.0061 |
| Structure bias | PASS с ограничением | 6 сделок, +1.3879%, PF 1.5001, но статистики мало |
| Mixed synthetic strategy sanity | FAIL | 3 сделки, все убыточные, kill switch сработал |
| WFO | FAIL | Нет достаточной истории и числа сделок |
| Paper/live gate | BLOCKED | Нет WFO PASS, 100 paper trades и 30 дней paper mode |

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

# Проверка двух замечаний к спецификации

## `blocked_volatility_regimes`

В предоставленном архитектурном PDF указано, что candidate должен быть отклонён, если его regime входит в `blocked_volatility_regimes`, но конкретный default в блоке `EmberConfig` не задан.

Текущий runtime regime называется `high_vol`. Значение `("high",)` не сработает, потому что `ContextBuilder` преобразует feature value `high` в context value `high_vol`.

Текущий default `()` не подтверждён и не опровергнут ТЗ; это явное исследовательское решение, которое нужно проверять отдельным profile. Без отдельного теста default не изменён.

## `tp_mode`

ТЗ описывает поведение при `tp_mode == "opposite_htf_liquidity"`, но не задаёт это значение как default в блоке `EmberConfig`. Поэтому текущий `fixed_rr` не является доказанным нарушением ТЗ.

Менять TP mode вместе с bias нельзя: это смешает две причины изменения результата. Нужен отдельный A/B test после bias study.

---

# Следующие обязательные шаги

1. Скачать 15000 свечей 15m для всех 6 core symbols.
2. Сравнить минимум `baseline` и `structure-bias` на каждом symbol.
3. Сохранить таблицу Trades, Return, PF, DD, Win Rate, neutral ratio и candidates.
4. Не принимать решение по bias, пока нет минимум 3 положительных symbols и достаточного числа сделок.
5. Отдельно проверить `blocked_volatility_regimes=("high_vol",)`.
6. Отдельно проверить `tp_mode="opposite_htf_liquidity"`.
7. Только после multi-symbol результата запускать purged WFO.

Ориентир по длине истории:

```text
90 дней 15m: 8640 bars
156 дней 15m: 15000 bars
180 дней 15m: 17280 bars
```

---

# Повторяемые команды

```bash
# Скачать около 156 дней по всем core symbols
python scripts/fetch_binance.py \
  --symbols INJUSDT,TONUSDT,DOGEUSDT,ARBUSDT,NEARUSDT,OPUSDT \
  --interval 15m \
  --limit 15000 \
  --out-dir data

# Baseline
python scripts/run_backtest.py \
  data/DOGEUSDT_15m_15000.csv \
  --profile baseline \
  --diagnostics \
  --out-dir results/DOGEUSDT_baseline

# Structure bias
python scripts/run_backtest.py \
  data/DOGEUSDT_15m_15000.csv \
  --profile structure-bias \
  --diagnostics \
  --out-dir results/DOGEUSDT_structure_bias

# Все research profiles на одном symbol
python scripts/run_diagnostics.py \
  data/DOGEUSDT_15m_15000.csv \
  --out-dir results/DOGEUSDT_diagnostics
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
