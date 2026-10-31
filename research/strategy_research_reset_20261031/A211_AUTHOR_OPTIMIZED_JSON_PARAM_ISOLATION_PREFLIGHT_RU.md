# A211 — pre-PnL корректировка runner после первого технического отказа

GitHub Actions run [41205507487](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41205507487) **FAIL ДО загрузки исторических свечей и ДО какого-либо PnL**. Причина `AUTHOR_OPTIMIZED_PARAM_JSON_COULD_OVERRIDE_DEFAULTS`.

Оригинальный репозиторий `Kureshi25/cryptobot@c8ffbaabee9f63630e179c698c53df4916b93f8e` действительно содержит побочный файл `user_data/strategies/TrendFutures.json` git-blob `d9793456adc34cf51eb9c16a4a8ccdb3f84e6bfc`. Этот JSON от 2026-08-25 задаёт ранее оптимизированные автором параметры `entry_lookback=18`, `exit_lookback=16`, `atr_stop_mult=9.5` в отличие от **исходных дефолтов в `TrendFutures.py`**: `20/10/3.0` и `lev=1`.

## Выбор сделан ДО просмотра PnL

Сохраняем контракт А211: `original Python strategy unchanged` и **source defaults 20/10/3.0**. Для точного отделения от оптимизированного JSON в CI копируем исходный `TrendFutures.py` в **изолированную временную папку** с точной byte SHA `2e6b83ba128373655090ca4827d8c7954ffaedfd`, используем чистый `--userdir` без JSON и `--strategy-path` на изолированный исходник. Оригинальный репозиторий и исходный сигнал не изменяем.

Если Freqtrade всё равно загрузит оптимизированные параметры — FAIL. Лог обязан вывести фактические `entry_lookback=20`, `exit_lookback=10`, `atr_stop_mult=3.0`, `lev=1.0`. Никаких гипероптимизаций. **Не использовать авторский JSON 18/16/9.5 в этом цикле**, даже если он даст лучший результат. Это альтернативный ранее подобранный автором вариант, отдельный кандидат, а не параллельная возможность выбрать победителя задним числом.

Предыдущий исходный запуск — ошибка подготовки, **не финансовое поражение**. Количество проверенных оригинальных бэктестов пока 0. Existing PAPER/SMOKE and live positions unchanged.
