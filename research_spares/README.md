# EMBER / SMOKE Spare Parts — подключаемая библиотека v0.3.0

**Статус:** исходный код + тесты + прямые входы в Binance USD-M **READ-ONLY**, без торгового исполнения. Отдельная исследовательская ветка; никаких изменений существующих стратегий, PAPER-планировщиков и биржевого аккаунта.

## Что реально реализовано

- **37/37** существующих ID Z01–Z38 (кроме ранее реализованного в SMOKE Z12) по-прежнему импортируются через `invoke('Zxx', args)`.
- **34 дополнительных операций** (`Zxx.some_name` и `Z00.bundle`): реальная загрузка Binance USD-M klines, mark-price, funding, OI и taker-buy volume; расчёт маржи на заданных ступенях, отдельная модель границы maintenance, двухногий журнал, защита портфельного риска, незатираемый SQLite risk latch, учет порядка реальных fill events, потоковые признаки, техническая диагностика, импорт сигналов внешних исполнителей.
- `run_binance_usdm()` — **единый вход** от REST фьючерсов к вычисляемым признакам; возвращает `SOURCE_COMPLETE` или `PARTIAL_SOURCE` с точной причиной нехватки данных. Публичный REST может быть недоступен по географическим причинам и OI имеет ограниченное окно хранения.
- `run_on_candles()` — универсальная подача `Polars.DataFrame`, `Polars.LazyFrame`, `pandas`, списка строк EMBER/SMOKE; контроль таймфрейма, UTC, symbol, closed candle.
- `SQLiteResearchLedger` — сохраняет только подтверждённые *переданные* события, не считает свечное касание гарантированным fill. Risk halt не сбрасывается при рестарте.
- Все интерфейсы автономные и могут быть подключены выборочно Python-импортом; никаких API-ключей, POST, real/live/paper orders, планировщиков и автоматических изменений стратегии.

## Установка — один раз

Из корня EMBER **на ветке `research/spares-library-core-20261101`**:

```bash
python -m pip install -e ./research_spares
python -m pytest research_spares/tests -q
python -m ember_spares.examples
ember-spares list
```

Или без переключения ветки:

```bash
python -m pip install 'git+https://github.com/SanChi117/EMBER-Research-Engine.git@research/spares-library-core-20261101#subdirectory=research_spares'
```

## Одной командой — реальные публичные данные Binance USDT-M

```python
from ember_spares import run_binance_usdm

r = run_binance_usdm(
    symbol='SOLUSDT', interval='15m',
    start_ms=1735689600000, end_ms=1736035200000,
    decision_at=1736035200,  # UTC seconds; никакой будущей свечи
    funding_lag_ms=1000, oi_lag_ms=1000,  # гипотезы задержки, фиксировать в эксперименте
    oi_period='15m',
)
print(r['status'], r['missing'])
print(r['features']['Z22'])  # taker-buy pressure из того же фьючерсного OHLCV
```

**Важно:** `decision_at` — UTC секунды; `start_ms/end_ms` — UTC миллисекунды. OI endpoint сохраняет только ограниченную историю; `PARTIAL_SOURCE` не означает, что можно подставить Spot. Исторические depth/queue публичным REST не восстанавливаются.

## По ID из единой функции, без переписывания интерфейса

```python
from ember_spares import invoke

result = invoke('Z32.scan_source', {'code':'x.shift(-1)'})
assert result == ['NEGATIVE_SHIFT']

risk = invoke('Z07.correlated_gate', {
  'existing':[],
  'new':{'strategy':'A','symbol':'SOLUSDT','direction':'long',
         'stop_risk_usdt':10.,'notional_usdt':500.},
  'max_stop_risk':100.,'max_gross_notional':10000.,
  'max_strategy_stop_risk':40.,'max_symbol_notional':2000.,
})
assert risk['allow']
```

Дополнительные готовые вызовы: `Z02.liquidation_boundary`, `Z03.depth`, `Z05.cash_ledger`, `Z09.bracket_uncertainty`, `Z14.compression`, `Z17.failure_exit`, `Z20.funding`, `Z21.oi`, `Z22.taker_series`, `Z24.basket`, `Z25.pair_diagnostics`, `Z26.dislocation`, `Z28.dual_entry`, `Z30.bootstrap`, `Z31.regimes`, `Z34.impact_envelope`, `Z37.with_addons`, `Z38.parity_exports` и другие через `ember-spares list`.

## Исполнение денег: жёсткая граница ответственности

- **Работает:** расчёт по предоставленным price/mark/funding/OI/fee/margin-ступеням, cash ledger, примерная maintenance-граница, лимиты риска, подтверждённые/частичные order receipts, бюджет двух ног, временна́я причинность, сохранение risk latch в SQLite.
- **Нельзя обещать:** точную биржевую ликвидацию (cross, ADL, точные обновляемые tiers и прочие нюансы), реконструкцию исторической очереди заявок по OHLCV, реальный fill без подтверждённого исполнения, исходный 1:1 результат чужой стратегии без её original runtime и версии, положительную доходность.
- Для неопределённой свечи стоп/цель возвращается `AMBIGUOUS`; для исторического отсутствия OI/depth — `BLOCKED_DATA`, а не выдуманная цена сделки. Это корректно работающий отказ, а не ошибочный сигнал.

## Где хранится документация

- [READY_TO_USE.md](READY_TO_USE.md) — устоявшийся `invoke` + импорт OHLCV.
- [COMPONENT_STATUS.md](COMPONENT_STATUS.md) — что конкретно вычисляется в каждом Z-ID, и что является требованием внешних данных или биржевого режима.
- [PROVENANCE.md](PROVENANCE.md) — отличия собственных референсных реализаций от первоисточников (отдельное юридическое и поведенческое подтверждение).
- [SPARE_PARTS_LIBRARY_20261101.md](../SPARE_PARTS_LIBRARY_20261101.md) — полный каталог источников и стратегия→деталь.

**Важно:** ни один из 76 оригиналов не получил статуса проверенной прибыльной Binance USD-M стратегии только от установки данной библиотеки.
