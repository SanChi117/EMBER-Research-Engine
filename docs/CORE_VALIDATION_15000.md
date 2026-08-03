# EMBER Core 15000-Bar Validation

Дата: 2026-08-03 UTC

## Scope

- Symbols: `INJUSDT, TONUSDT, DOGEUSDT, ARBUSDT, NEARUSDT, OPUSDT`
- Interval: `15m`
- Bars per symbol: `15000` — примерно 156 дней
- Profiles: `baseline`, `structure-bias`, `high-vol-block`, `opposite-liquidity`
- Data source: Binance public klines; API keys не использовались

## Reproducibility

- PR: `#4`
- Complete run: `30823347050`
- Artifact: `8860720831`
- Tests: `18 passed, 1 warning`

Workflow был отмечен как `failure` только потому, что отсутствовал родительский каталог для `tee`:

```text
tee: results/core_validation_stdout.txt: No such file or directory
```

Python-run завершился полностью, все 90 000 свечей были загружены, backtests и WFO были рассчитаны, artifact был успешно сохранён. Ошибка workflow исправлена добавлением `mkdir -p results`.

## Per-symbol results

| Symbol | Profile | Neutral | Candidates | Trades | Return | PF | DD | Win rate |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| INJUSDT | baseline | 47.95% | 15 | 11 | +6.0043% | 2.3049 | 1.5000% | 63.64% |
| INJUSDT | structure-bias | 45.31% | 110 | 6 | +0.3964% | 1.1164 | 2.4659% | 50.00% |
| INJUSDT | high-vol-block | 47.95% | 15 | 11 | +6.0043% | 2.3049 | 1.5000% | 63.64% |
| INJUSDT | opposite-liquidity | 47.95% | 15 | 11 | +12.9669% | 3.7421 | 2.7945% | 63.64% |
| TONUSDT | baseline | 57.48% | 24 | 12 | +7.7666% | 2.5681 | 3.6017% | 66.67% |
| TONUSDT | structure-bias | 47.74% | 79 | 6 | -2.9012% | 0.3749 | 3.1318% | 33.33% |
| TONUSDT | high-vol-block | 57.48% | 23 | 11 | +9.0656% | 3.4040 | 2.4397% | 72.73% |
| TONUSDT | opposite-liquidity | 57.48% | 24 | 7 | +7.4238% | 2.9168 | 3.7949% | 57.14% |
| DOGEUSDT | baseline | 69.90% | 21 | 13 | +10.2218% | 3.3625 | 1.5000% | 76.92% |
| DOGEUSDT | structure-bias | 37.67% | 95 | 10 | -0.0626% | 1.0050 | 2.8781% | 50.00% |
| DOGEUSDT | high-vol-block | 69.90% | 20 | 13 | +13.1166% | 5.2932 | 1.5000% | 84.62% |
| DOGEUSDT | opposite-liquidity | 69.90% | 21 | 12 | +11.0732% | 2.8913 | 1.5000% | 66.67% |
| ARBUSDT | baseline | 52.12% | 17 | 10 | +7.4464% | 3.1365 | 1.4086% | 70.00% |
| ARBUSDT | structure-bias | 43.17% | 99 | 4 | -2.2204% | 0.4187 | 3.7517% | 25.00% |
| ARBUSDT | high-vol-block | 52.12% | 17 | 10 | +7.4464% | 3.1365 | 1.4086% | 70.00% |
| ARBUSDT | opposite-liquidity | 52.12% | 17 | 10 | +2.2336% | 1.3813 | 2.8979% | 50.00% |
| NEARUSDT | baseline | 46.69% | 23 | 13 | +8.8512% | 2.6944 | 2.3035% | 69.23% |
| NEARUSDT | structure-bias | 37.59% | 118 | 8 | +0.7553% | 1.1903 | 3.0471% | 50.00% |
| NEARUSDT | high-vol-block | 46.69% | 23 | 13 | +8.8512% | 2.6944 | 2.3035% | 69.23% |
| NEARUSDT | opposite-liquidity | 46.69% | 23 | 13 | +18.6550% | 4.4470 | 2.3035% | 69.23% |
| OPUSDT | baseline | 47.10% | 33 | 15 | +8.0230% | 2.1885 | 1.4867% | 66.67% |
| OPUSDT | structure-bias | 43.24% | 103 | 5 | -0.9769% | 0.7710 | 4.0059% | 40.00% |
| OPUSDT | high-vol-block | 47.10% | 33 | 15 | +8.0230% | 2.1885 | 1.4867% | 66.67% |
| OPUSDT | opposite-liquidity | 47.10% | 33 | 15 | +17.2340% | 3.4548 | 1.4867% | 66.67% |

## Aggregate

| Profile | Positive symbols | PF > 1.5 | Trades | Average return | Worst DD |
|---|---:|---:|---:|---:|---:|
| baseline | 6/6 | 6/6 | 74 | +8.0522% | 3.6017% |
| structure-bias | 2/6 | 0/6 | 39 | -0.8349% | 4.0059% |
| high-vol-block | 6/6 | 6/6 | 73 | +8.7512% | 2.4397% |
| opposite-liquidity | 6/6 | 5/6 | 68 | +11.5977% | 3.7949% |

## Decisions

1. `structure-bias` отклонён как замена baseline. Он уменьшил neutral и сформировал значительно больше candidates, но дал только 2/6 положительных symbols, 0/6 с PF выше 1.5 и отрицательный средний return.
2. Исходный EMA20 `+/-2%` baseline дал положительный результат и PF выше 1.5 на всех шести symbols. Он остаётся контрольным профилем.
3. `high-vol-block` — сильнейший robustness candidate: 6/6 положительных symbols, 6/6 PF выше 1.5, выше средний return, ниже worst DD и почти такое же количество сделок.
4. `opposite-liquidity` дал максимальный средний return, но ARBUSDT получил PF `1.3813`. Этот TP-mode нельзя назначать default без чистой fixed-universe проверки и paper observation.

## WFO

### Baseline — fixed six-symbol universe

```text
Status: PASS
Folds: 4
Average return: +7.5725%
Average PF: 2.4933
Worst DD: 2.9775%
Stability: 75%
Zero-trade folds: 1
```

### High-vol-block — fixed six-symbol universe

```text
Status: PASS
Folds: 4
Average return: +7.9156%
Average PF: 2.7027
Worst DD: 2.9775%
Stability: 75%
Zero-trade folds: 1
```

Формальные критерии архитектуры пройдены, однако один из четырёх folds не содержит сделок. Поэтому WFO фиксируется как `PASS with warning`, а не как достаточное доказательство live-readiness.

### Opposite-liquidity

Первый расчёт исключил ARBUSDT после просмотра full-period metrics. Это universe-selection leakage, поэтому тот WFO-результат не принимается как чистое доказательство. Для повторяемой проверки добавлен `scripts/run_fixed_wfo.py`, который всегда использует заранее объявленные шесть symbols.

## Methodological limits

- Выбор лучшего профиля сделан на той же 15000-bar истории, поэтому существует meta-selection risk.
- Один WFO fold без сделок снижает силу доказательства стабильности.
- Backtest не заменяет paper observation.
- `high-vol-block` и `opposite-liquidity` должны пройти paper comparison либо untouched holdout прежде, чем их можно будет назначить production research defaults.

## Reproducible commands

```bash
python scripts/run_core_validation.py \
  --symbols INJUSDT,TONUSDT,DOGEUSDT,ARBUSDT,NEARUSDT,OPUSDT \
  --profiles baseline,structure-bias,high-vol-block,opposite-liquidity \
  --interval 15m \
  --bars 15000 \
  --data-dir data/core_validation \
  --out-dir results/core_validation
```

Fixed-universe WFO на уже сохранённых datasets:

```bash
python scripts/run_fixed_wfo.py \
  --data-dir data/core_validation \
  --out-dir results/fixed_wfo \
  --symbols INJUSDT,TONUSDT,DOGEUSDT,ARBUSDT,NEARUSDT,OPUSDT \
  --profiles baseline,high-vol-block,opposite-liquidity \
  --interval 15m \
  --bars 15000
```

## Current gate

```text
Backtest multi-symbol: PASS
Baseline WFO: PASS with warning
High-vol-block WFO: PASS with warning
Opposite-liquidity clean WFO: PENDING
Paper gate: BLOCKED
Live gate: BLOCKED
```

До live необходимы:

```text
100 completed paper trades
30 calendar days paper observation
paper metrics within +/-10% of backtest
all leakage tests PASS
```
