# A236-C — найден точный Risk_Stair_S5 в авторском запуске (source audit, not economics)

Исходный pinned source `linhuang1212-coder/crypto-quant-trading` commit `63c012a0329a280f99fe57896456d4b9363c9c71`.

1. `user_data/scripts/risk_experiment_manifest.json`, Git blob `b07d45fe9485a0e71af6ff26f8cfd66af793f587` содержит **Risk_Stair_S5**, `group=stair_exit`, `mid=20b/-0.06,late=40b/-0.04,lev=5.0`.
2. `user_data/scripts/run_risk_experiments.ps1`, Git blob `6e35055ecf8aa7e7ee247ddf5ac5f9b9a0d10c93`, строки 1–28, читает этот manifest и вызывает для каждого `--strategy $strategy`, `--config /freqtrade/user_data/config_backtest.json`, `--timerange 20200101-20260401`, `--starting-balance 1000`.
3. `user_data/config_backtest.json`, Git blob `ee0f8c8a4c1ad827a38109c7872c1f09ac7383f3`: `stake_amount=unlimited`, `max_open_trades=4`, genuine futures 4 pairs BTC/ETH/SOL/**ADA**, isolated.
4. **Ограничение полного исходного паритета:** в PowerShell script strategy-path `/freqtrade/user_data/strategies/experiments`, тогда как pinned S5 источник лежит в `user_data/strategies/risk_exp/Risk_Stair_S5.py` blob `9b6ba1f5466727da1e9446f4e283b1c555fca59b`. Исследовательская версия могла размещаться в другой папке во время запуска, но сам факт рабочего CLI pipeline требует дополнительного источникового свидетельства. Не утверждать, что уже воспроизведено.

Следующий надлежащий эксперимент Risk S5: controlled native 15m, **четыре пары**, funding и mark mainnet, отдельный общий счёт 1000 USDT, `stake_amount=unlimited`, `max_open_trades=4`, подтверждённые protections/callbacks, полные сделки, source-config SHA. Не запускать тот же 3-парный A235 и не выдавать Freqle 33-парные results за автора. Никаких реальных ордеров.

VERIFIED=0. Это **существенное сокращение source/config неопределённости R004**, не пересчёт экономики.
