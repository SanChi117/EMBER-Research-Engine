# EMBER Validation Log

Этот документ является единым журналом проверки проекта EMBER Research Engine.

Здесь должны сохраняться все выполненные шаги, команды, наборы данных, результаты, найденные ошибки, исправления и итоговые решения. Записи не удаляются задним числом: новые проверки добавляются ниже отдельными блоками.

## Правила ведения журнала

Для каждой новой проверки обязательно указывать:

1. дату и время UTC;
2. версию или commit SHA;
3. цель проверки;
4. точную команду;
5. использованные данные;
6. фактический результат;
7. итоговый статус: `PASS`, `FAIL` или `BLOCKED`;
8. найденные проблемы;
9. следующий шаг.

`PASS` означает только прохождение конкретной проверки. Он не является разрешением на live trading.

---

# Сводный статус проекта

Актуально на 2026-08-03.

| Проверка | Статус | Краткий результат |
|---|---|---|
| Установка проекта | PASS | Пакет устанавливается через `pip install -e ".[dev]"` |
| Unit tests | PASS | Полный набор тестов проходит в GitHub Actions |
| Leakage gate | PASS | Тесты zero-look-ahead проходят |
| Binance public loader | PASS | По 1000 свечей получено для 6 core symbols |
| Synthetic pipeline execution | PASS | Backtest и отчёты запускаются после исправления WFO |
| Synthetic realism | FAIL | 46 сделок, 100% win rate, PF `inf`; сценарий слишком идеализирован |
| Synthetic WFO | FAIL | 1000 свечей 15m недостаточно для 30-дневного train window |
| Real-data strategy sanity | FAIL | Всего 4 сделки на 6 символах, все убыточные |
| Live gate | BLOCKED | Нет 100 paper trades, 30 дней paper mode и WFO PASS |

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

## 2026-08-03 — Повторный Synthetic Sanity Check

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

**Ожидаемый ориентир sanity check:**

```text
Return: +30..60%
PF: 1.5..3.0
DD: < 5%
Trades: 15..30
```

**Вывод:**

- технически synthetic pipeline работает;
- значения не являются реалистичными;
- 46 сделок, 100% win rate и PF `inf` показывают, что synthetic dataset слишком идеализирован;
- этот результат нельзя использовать как доказательство качества стратегии.

**Причина WFO FAIL:**

1000 свечей 15m охватывают примерно 10.4 дня. Конфигурация WFO требует 30 дней только для train window, поэтому полноценные folds не сформировались.

**Статус:**

- Pipeline execution: `PASS`;
- Synthetic realism: `FAIL`;
- WFO: `FAIL`.

---

## 2026-08-03 — Загрузка реальных данных Binance

**Цель:** проверить публичный Binance loader и получить реальные данные для первых backtests.

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

## 2026-08-03 — Первые backtests на реальных данных

**Цель:** проверить, находит ли текущая стратегия сделки и имеет ли положительную базовую статистику.

**Конфигурация:** baseline `EmberConfig()` без ручной оптимизации.

**Результаты:**

| Symbol | Trades | Return | PF | Max DD | Win Rate |
|---|---:|---:|---:|---:|---:|
| INJUSDT | 0 | 0.0000% | 0.0 | 0.0000% | 0.0% |
| TONUSDT | 1 | -1.1910% | 0.0 | 1.1910% | 0.0% |
| DOGEUSDT | 0 | 0.0000% | 0.0 | 0.0000% | 0.0% |
| ARBUSDT | 0 | 0.0000% | 0.0 | 0.0000% | 0.0% |
| NEARUSDT | 2 | -2.8383% | 0.0 | 2.8383% | 0.0% |
| OPUSDT | 1 | -1.4867% | 0.0 | 1.4867% | 0.0% |

**Сводка:**

```text
Всего символов: 6
Всего сделок: 4
Прибыльных сделок: 0
Символов без сделок: 3
Общий качественный вывод: стратегия sanity check не прошла
```

**Интерпретация:**

- engine и data pipeline технически работают;
- текущие setup filters создают слишком мало входов;
- найденные входы не показали положительного edge;
- 1000 свечей на символ недостаточно для серьёзного исследования, но достаточно, чтобы зафиксировать проблему частоты и качества входов;
- оптимизация параметров без диагностики причин отбраковки будет слепой подгонкой.

**Статус:** `FAIL`.

---

# Найденные проблемы

## P0 — WFO projection name collision

**Статус:** исправлено.

**Описание:** `min(time)` и `max(time)` создавали одинаковое имя столбца.

## P1 — Synthetic dataset слишком идеален

**Статус:** открыто.

**Признаки:**

- 100% win rate;
- PF `inf`;
- 0% drawdown;
- 46 сделок вместо ожидаемых 15–30.

**Риск:** synthetic demo проверяет только связность pipeline, но не устойчивость логики к проигрышам, drawdown и смешанным режимам.

## P1 — Недостаточная частота реальных сделок

**Статус:** открыто.

**Признаки:** 4 сделки на 6000 входных свечей по 6 символам.

**Неизвестно:** какой именно gate чаще всего отклоняет кандидатов.

## P1 — Отрицательный результат всех реальных сделок

**Статус:** открыто.

**Признаки:** 0 прибыльных сделок из 4, PF 0.0.

**Ограничение:** выборка слишком мала для статистического вывода, но недостаточна для продолжения к paper mode.

## P1 — Недостаточно данных для WFO

**Статус:** открыто.

**Признаки:** 1000 свечей 15m дают около 10.4 дня при train window 30 дней.

---

# Следующие обязательные шаги

## Шаг 4 — Диагностические счётчики фильтров

Добавить в исследовательский pipeline счётчики:

```text
bars_seen
neutral_context_rejects
direction_rejects
regime_rejects
no_impulse_rejects
location_rejects
rejection_candle_rejects
volume_rejects
confidence_rejects
risk_rejects
quality_gate_rejects
structure_gate_rejects
no_future_exit_rejects
executed_trades
```

**Цель:** точно определить, где исчезают сделки.

**Статус:** `PENDING`.

## Шаг 5 — Более длинная реальная история

Скачать минимум 5000–10000 свечей 15m на каждый core symbol или получить эквивалентную локальную историю.

**Цель:** сформировать достаточную выборку для частоты входов, режимов рынка и WFO.

**Статус:** `PENDING`.

## Шаг 6 — Диагностический backtest до оптимизации

Для каждого символа сохранить:

- количество bars;
- количество setup candidates;
- причины отклонения;
- executed trades;
- gross PF;
- net PF после costs;
- return;
- max drawdown;
- win rate;
- average R;
- распределение по setup type и regime.

**Статус:** `PENDING`.

## Шаг 7 — Исправление synthetic dataset

Synthetic должен содержать:

- выигрышные и проигрышные сделки;
- trend, range и high-vol режимы;
- неоднозначные свечи;
- realistic costs;
- ненулевой drawdown;
- PF в конечном диапазоне;
- достаточную длительность для WFO folds.

**Статус:** `PENDING`.

## Шаг 8 — Purged WFO на достаточной истории

Критерии PASS остаются неизменными:

```text
stability_score >= 70%
avg_pf >= 1.5
worst_dd < 10%
avg_return > 0
```

**Статус:** `BLOCKED` до выполнения шагов 4–7.

## Шаг 9 — Paper mode

Разрешается только после приемлемого real-data backtest и WFO PASS.

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
