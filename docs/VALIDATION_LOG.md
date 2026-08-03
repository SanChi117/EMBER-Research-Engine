# EMBER Validation Log

Этот документ является единым журналом проверки проекта EMBER Research Engine.

Здесь сохраняются выполненные шаги, точные команды, наборы данных, фактические результаты, обнаруженные ошибки, исправления и принятые решения. Записи не удаляются задним числом: новые проверки добавляются отдельными блоками.

## Правила ведения журнала

Для каждой новой проверки указываются:

1. дата и время UTC;
2. версия или commit SHA;
3. цель проверки;
4. точная команда;
5. использованные данные;
6. фактический результат;
7. итоговый статус: `PASS`, `FAIL` или `BLOCKED`;
8. найденные проблемы;
9. следующий шаг.

`PASS` означает только прохождение конкретной проверки. Он не является разрешением на live trading.

---

# Сводный статус проекта

Актуально на 2026-08-03 после PR #2.

| Проверка | Статус | Краткий результат |
|---|---|---|
| Установка проекта | PASS | Пакет устанавливается через `pip install -e ".[dev]"` |
| Unit tests | PASS | 14 тестов прошли в GitHub Actions |
| Leakage gate | PASS | Zero-look-ahead тесты проходят |
| Binance public loader, 1000 bars | PASS | По 1000 свечей получено для 6 core symbols |
| Binance paginated loader, 5000 bars | PASS | DOGEUSDT: ровно 5000 свечей 15m |
| Reject diagnostics | PASS | Все основные gates имеют отдельные счётчики |
| Bias comparison | PASS | Baseline и `bull+bear` дали одинаковые 4 сделки |
| Wide diagnostic profile | FAIL | `min_rr=1.2` полностью блокируется обязательным cost gate |
| Mixed synthetic execution | PASS | 5000 mixed-regime свечей обрабатываются полностью |
| Mixed synthetic strategy sanity | FAIL | 3 сделки, все убыточные, kill switch остановил тест |
| Real DOGE 5000-bar baseline | PASS с ограничением | +2.8585%, PF 3.0409, DD 1.4006%, но только 4 сделки |
| Real-data statistical sufficiency | FAIL | 4 сделки недостаточны для вывода об edge |
| WFO | FAIL | Требуется более длинная история и достаточное число сделок |
| Live gate | BLOCKED | Нет WFO PASS, 100 paper trades и 30 дней paper mode |

---

# История проверок

## 2026-08-03 — Импорт EMBER Research Engine 0.2.0

**Цель:** создать отдельный репозиторий и перенести исследовательский engine согласно архитектурному ТЗ.

**Репозиторий:** `SanChi117/EMBER-Research-Engine`

**Основной import commit:**

```text
5784f1e133bc7c909264290161d24522b1ebaa39
```

**Результат:**

- проект размещён в отдельном репозитории;
- структура пакета находится в корне;
- добавлены data engine, features, MTF context, setups, risk engine, exit simulator, portfolio, WFO, reports и virtual paper server;
- добавлены тесты и GitHub Actions для Python 3.10, 3.11 и 3.12;
- live execution отсутствует и заблокирован архитектурой.

**Статус:** `PASS` для создания базового проекта.

---

## 2026-08-03 — Исправление расчёта Profit Factor

**Цель:** убрать искусственный предел PF `99.0`.

**Проблема:**

```python
return 99.0 if gross_profit > 0 else 0.0
return min(99.0, gross_profit / gross_loss)
```

**Исправление:**

```python
if gross_loss == 0:
    return float("inf") if gross_profit > 0 else 0.0
return gross_profit / gross_loss
```

Тест изменён на:

```python
assert profit_factor([1.0, 2.0, 0.5]) == float("inf")
```

**Commit:**

```text
b61ddc946b0d1bd0e096c870f06fc6d80ef56010
```

**Статус:** `PASS`.

---

## 2026-08-03 — Первый Synthetic Sanity Check

**Цель:** проверить, запускается ли полный synthetic pipeline.

**Команда:**

```bash
python scripts/run_demo.py --out-dir results/demo --bars 1000
```

**Первый результат:** выполнение остановилось с ошибкой Polars.

```text
polars.exceptions.DuplicateError:
projections contained duplicate output name 'time'
```

**Причина:** в `WalkForwardValidator` выражения `min(time)` и `max(time)` создавали два столбца с одинаковым именем `time`.

**Исправление:** столбцам присвоены разные aliases, добавлен regression test.

**Commits:**

```text
c62d9b95f1a4281ac2c03215ae603a4dfc23c4e4
d5d387f9de2d0185675c2b3005f845d6b0bdecba
```

**Статус первого запуска:** `FAIL`.

**Статус после исправления:** pipeline запускается.

---

## 2026-08-03 — Повторный старый Synthetic Sanity Check

**Команда:**

```bash
python scripts/run_demo.py --out-dir results/demo --bars 1000
```

**Фактический результат:**

```text
Total Return: +84.3983%
Profit Factor: inf
Max Drawdown: 0.0000%
Win Rate: 100.0000%
Average Trade: 1.3392 R
Number of Trades: 46
Final Equity: 18439.8349
WFO: FAIL
```

**Вывод:** технически pipeline работал, но synthetic dataset был слишком идеализирован. Результат нельзя было использовать как доказательство качества стратегии.

**Причина WFO FAIL:** 1000 свечей 15m охватывают примерно 10.4 дня, а train window требует 30 дней.

**Статус:** pipeline `PASS`, realism `FAIL`, WFO `FAIL`.

---

## 2026-08-03 — Загрузка 1000 реальных свечей Binance для 6 symbols

**Параметры:**

```text
Interval: 15m
Limit: 1000 bars per symbol
Symbols: INJUSDT, TONUSDT, DOGEUSDT, ARBUSDT, NEARUSDT, OPUSDT
```

**Результат загрузки:**

| Symbol | Rows |
|---|---:|
| INJUSDT | 1000 |
| TONUSDT | 1000 |
| DOGEUSDT | 1000 |
| ARBUSDT | 1000 |
| NEARUSDT | 1000 |
| OPUSDT | 1000 |

**Статус:** `PASS`.

---

## 2026-08-03 — Первые backtests на 1000 реальных свечах

**Конфигурация:** baseline `EmberConfig()` без ручной оптимизации.

| Symbol | Trades | Return | PF | Max DD | Win Rate |
|---|---:|---:|---:|---:|---:|
| INJUSDT | 0 | 0.0000% | 0.0 | 0.0000% | 0.0% |
| TONUSDT | 1 | -1.1910% | 0.0 | 1.1910% | 0.0% |
| DOGEUSDT | 0 | 0.0000% | 0.0 | 0.0000% | 0.0% |
| ARBUSDT | 0 | 0.0000% | 0.0 | 0.0000% | 0.0% |
| NEARUSDT | 2 | -2.8383% | 0.0 | 2.8383% | 0.0% |
| OPUSDT | 1 | -1.4867% | 0.0 | 1.4867% | 0.0% |

**Сводка:** 4 сделки, 0 прибыльных, 3 symbols без сделок.

**Статус:** `FAIL`.

---

## 2026-08-03 12:18 UTC — Добавление reject diagnostics

**PR:** `#2 Add diagnostics, 5000-bar Binance fetch, and mixed synthetic sanity`

**Проверенный head commit:**

```text
4fdbcf20416da29d0c4c4915f52afca807153856
```

**Добавленные счётчики:**

```text
bars_seen
neutral_context
direction_reject
regime_reject
no_setup
setup_blocked
confidence_low
volume_low
candidate_passed
risk_none
rr_low
cost_gate
quality_reject
structure_reject
no_future
overlap_reject
portfolio_reject
halted
executed
```

Setup detector и risk engine теперь возвращают стабильную причину отказа. Счётчики сохраняются в `Backtester.last_diagnostics` и могут печататься через `diagnostics=True`.

**Проверка:**

```bash
pytest tests/ -v
```

**Результат:**

```text
14 passed, 1 warning
```

**Статус:** `PASS`.

---

## 2026-08-03 12:18 UTC — Новый mixed-regime synthetic, 5000 bars

**Команда:**

```bash
python scripts/run_demo.py --demo --bars 5000 --wfo --out-dir results/demo
```

**Данные:** детерминированные режимы `trend_up`, `trend_down`, `range`, `high_vol`, seed `42`, намеренно добавленные adverse reversals.

**Reject diagnostics:**

```text
bars_seen: 4940
neutral_context: 1008
direction_reject: 0
regime_reject: 0
no_setup: 3637
setup_blocked: 0
confidence_low: 0
volume_low: 7
candidate_passed: 288
risk_none: 0
rr_low: 0
cost_gate: 0
quality_reject: 46
structure_reject: 86
no_future: 0
overlap_reject: 1
portfolio_reject: 0
halted: 1
executed: 3
```

**Метрики:**

```text
Return: -3.9040%
PF: 0.0000
DD: 3.9040%
Trades: 3
Win rate: 0.0000%
WFO: FAIL
```

**Интерпретация:**

- synthetic больше не выдаёт фальшивые 100% win rate и PF `inf`;
- текущая стратегия не прошла mixed-regime sanity check;
- после трёх убыточных сделок сработал обязательный kill switch;
- генератор содержит смешанные рыночные режимы, однако при текущих filters стратегия успела исполнить только три проигрышных входа.

**Статус:** execution `PASS`, strategy sanity `FAIL`, WFO `FAIL`.

---

## 2026-08-03 12:18 UTC — Загрузка 5000 свечей DOGEUSDT

**Команда:**

```bash
python scripts/fetch_binance.py \
  --symbols DOGEUSDT \
  --interval 15m \
  --limit 5000 \
  --out-dir data
```

**Результат:**

```text
DOGEUSDT: 5000 rows -> data/DOGEUSDT_15m_5000.csv
```

Загрузчик использует пагинацию `endTime`; API key не требуется.

**Важно:** 5000 свечей 15m — это около 52 дней, а не 90 дней. Этого достаточно для первичной диагностики, но мало для надёжного multi-fold WFO с 30-дневным train window.

**Статус:** `PASS`.

---

## 2026-08-03 12:18 UTC — Сравнение bias и wide profile на DOGEUSDT

**Команда:**

```bash
python scripts/run_diagnostics.py \
  data/DOGEUSDT_15m_5000.csv \
  --out-dir results/doge_diagnostics
```

### Профиль `baseline`

Конфигурация сохраняет требование архитектурного ТЗ:

```python
allowed_direction_contexts = ("down",)
min_confidence = 43.0
min_volume_ratio = 0.70
min_rr = 1.8
atr_stop_multiplier = 1.5
```

**Reject diagnostics:**

```text
bars_seen: 4940
neutral_context: 3644
direction_reject: 336
no_setup: 952
volume_low: 2
candidate_passed: 6
quality_reject: 1
overlap_reject: 1
executed: 4
```

Остальные counters: `0`.

**Метрики:**

```text
Return: +2.858547%
PF: 3.040922336505632
DD: 1.400590%
Trades: 4
Win rate: 75.000000%
```

**Статус:** технически `PASS`, статистическая достаточность `FAIL` из-за четырёх сделок.

### Профиль `both-directions`

```python
allowed_direction_contexts = ("bull", "bear")
```

**Reject diagnostics:**

```text
bars_seen: 4940
neutral_context: 3644
direction_reject: 0
no_setup: 1286
volume_low: 4
candidate_passed: 6
quality_reject: 1
overlap_reject: 1
executed: 4
```

**Метрики:** полностью совпали с baseline.

```text
Return: +2.858547%
PF: 3.040922336505632
DD: 1.400590%
Trades: 4
Win rate: 75.000000%
```

**Вывод по bias:** `down`-only не является главным bottleneck на этой выборке. Разрешение `bull+bear` не добавило ни одной исполненной сделки. 336 direction rejects перешли в `no_setup`, потому что на этих барах detector всё равно не сформировал валидный setup.

**Статус:** `PASS` как диагностический эксперимент; production default не изменён.

### Профиль `wide`

```python
allowed_direction_contexts = ("bull", "bear")
min_confidence = 20.0
min_volume_ratio = 0.5
min_rr = 1.2
atr_stop_multiplier = 1.0
```

**Reject diagnostics:**

```text
bars_seen: 4940
neutral_context: 3644
no_setup: 1286
volume_low: 4
candidate_passed: 6
cost_gate: 6
executed: 0
```

**Метрики:**

```text
Return: 0.000000%
PF: 0.0
DD: 0.000000%
Trades: 0
```

**Причина:** профиль `min_rr=1.2` несовместим с обязательным cost gate при текущих параметрах.

```text
risk_fraction = 0.01
round_trip_cost = 0.0024
net_edge = (1.2 - 1.0) * 0.01 - 0.0024
net_edge = -0.0004
```

Для положительного `net_edge` RR должен быть строго выше `1.24`. Cost gate отключать нельзя, поскольку он является обязательным требованием архитектуры.

**Статус:** `FAIL`, но причина точно определена: `cost_gate`.

---

# Текущие выводы

1. Главный фильтр на DOGEUSDT — `neutral_context`: 3644 из 4940 анализируемых баров.
2. Второй главный источник отказов — отсутствие базового setup после разрешённого контекста.
3. `down`-only не объясняет низкую частоту: `bull+bear` оставил те же 4 сделки.
4. Ослабление `min_confidence` не помогло, потому что кандидаты и раньше не отбраковывались по confidence.
5. Ослабление `min_volume_ratio` почти не влияет: volume gate отклоняет единицы баров.
6. `min_rr=1.2` нельзя использовать с текущими costs: все кандидаты блокируются cost gate.
7. Baseline результат на 5000 DOGE bars положительный, но 4 сделки не доказывают наличие устойчивого edge.
8. Mixed synthetic выявил три последовательных убытка и корректную работу kill switch.

---

# Найденные проблемы

## P0 — WFO projection name collision

**Статус:** исправлено.

## P1 — Недостаточная доля направленного HTF context

**Статус:** открыто.

**Признак:** `neutral_context=3644` из `4940` DOGE bars.

## P1 — Низкая частота setup candidates

**Статус:** открыто.

**Признак:** только 6 candidates прошли setup gates на 5000 DOGE bars.

## P1 — Wide RR конфликтует с costs

**Статус:** причина найдена.

**Признак:** 6 из 6 candidates отклонены `cost_gate` при `min_rr=1.2`.

## P1 — Недостаточная статистическая выборка

**Статус:** открыто.

**Признак:** 4 исполненные сделки на 5000 DOGE bars.

## P1 — Mixed synthetic strategy failure

**Статус:** открыто.

**Признак:** 3 сделки, 0 wins, return `-3.9040%`, затем kill switch.

---

# Следующие обязательные шаги

## Шаг 4 — Диагностические счётчики фильтров

**Статус:** `DONE`.

## Шаг 5 — Более длинная реальная история

DOGEUSDT 5000 bars загружены.

**Статус:** `PARTIAL` — для полноценного WFO нужны 90–180 дней, то есть примерно 8640–17280 свечей 15m на symbol.

## Шаг 6 — Диагностический backtest до оптимизации

Baseline, both-directions и wide профили выполнены на DOGEUSDT.

**Статус:** `PARTIAL` — требуется повторить минимум на всех 6 core symbols и сохранить распределение по setup type/regime.

## Шаг 7 — Исправление synthetic dataset

Mixed-regime generator добавлен, детерминирован и покрыт тестом.

**Статус:** `PARTIAL` — генератор больше не идеален, но текущая стратегия исполняет на нём только три проигрышные сделки. Нужна дальнейшая калибровка generator sanity contract без подгонки под прибыль.

## Шаг 8 — Purged WFO на достаточной истории

Критерии PASS неизменны:

```text
stability_score >= 70%
avg_pf >= 1.5
worst_dd < 10%
avg_return > 0
```

**Статус:** `BLOCKED` до получения 90–180 дней данных и достаточного количества сделок.

## Шаг 9 — Paper mode

Минимальный live gate:

```text
100 completed paper trades
30 calendar days
paper metrics within +/-10% of backtest
WFO PASS
all leakage tests PASS
```

**Статус:** `BLOCKED`.

---

# Повторяемые команды

```bash
# Mixed synthetic sanity
python scripts/run_demo.py --demo --bars 5000 --wfo --out-dir results/demo

# 5000 public Binance bars
python scripts/fetch_binance.py \
  --symbols DOGEUSDT \
  --interval 15m \
  --limit 5000 \
  --out-dir data

# Сравнение baseline, both-directions и wide
python scripts/run_diagnostics.py \
  data/DOGEUSDT_15m_5000.csv \
  --out-dir results/doge_diagnostics

# Один профиль с подробными counters
python scripts/run_backtest.py \
  data/DOGEUSDT_15m_5000.csv \
  --profile baseline \
  --diagnostics \
  --out-dir results/doge_baseline
```

---

# Шаблон новой записи

```markdown
## YYYY-MM-DD — Название проверки

**Commit:** `<sha>`

**Цель:**

**Команда:**

```bash
...
```

**Данные:**

**Результат:**

```text
...
```

**Статус:** `PASS | FAIL | BLOCKED`

**Найденные проблемы:**

**Следующий шаг:**
```
