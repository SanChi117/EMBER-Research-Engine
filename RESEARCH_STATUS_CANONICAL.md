> **⛔ ПОЛЬЗОВАТЕЛЬСКИЙ RESET — ПАУЗА ВСЕГО ПОИСКА ГОТОВЫХ СТРАТЕГИЙ (01.11.2026).** Отсечка: 30.10.2026 22:04 UTC = 31.10.2026 00:04 Europe/Kyiv, обсуждение «а не проще взять уже готовую?». Никаких новых проверок, CI-направлений, бэктестов, внедрения PAPER или адаптаций **до новой команды пользователя**. Старые статусы ниже — сохранённая история, **не список заданий к выполнению**.
>
> **ЕДИНСТВЕННАЯ ВЫДАЧА ПО ВСЕМ КАНДИДАТАМ:** [76/76 отсортированы от перспективных до мусора + 18 других источников + 3 veto](STRATEGY_SEARCH_ALL_CANDIDATES_RANKED_20261101.md) · [те же 76 в CSV](STRATEGY_SEARCH_ALL_CANDIDATES_RANKED_20261101.csv). Исторические результаты и original-source SHA сохранены; ни одна торговая стратегия не VERIFIED.
>
> **ОТКЛЮЧЕНИЯ:** GitHub исследовательские ветки `research/a188...`—`research/a247...` (56 веток) проверены и branch-specific workflow для соответствующего исследовательского цикла удалены с сохранением Git history; отдельно `research/reboot-inventory-evidence-first-20261030` отключено 12 source-search/reset workflow. Отдельно отключены два A188 workflow с нетипичным именем. Старый GitHub `ci.yml` общего движка `main` НЕ отключался (он предшествовал переходу). GitHub Actions уже запущенные до удаления могут закончиться; нельзя выдавать их за новые исследования. ChatGPT Automations: **отдельных активных задач поиска стратегий нет**, существующие пять PAPER/market задач предшествуют этой отсечке и не затрагивались.

---

# EMBER — ЕДИНСТВЕННАЯ АКТУАЛЬНАЯ СВОДКА И ОЧИСТКА ХРОНОЛОГИИ
**Контроль: 2026-11-01, исправление путаницы после A249.**

> **ВАЖНО: АВАРИЙНАЯ КОРРЕКЦИЯ ЗАПИСЕЙ АССИСТЕНТА.** В предыдущих ответах и многочисленных файлах перепутаны «CI SUCCESS», фактический успешный бэктест, экономический PASS, аудит исходника и авторский результат. Избыточные checkpoint-файлы создали ложное впечатление линейного завершения проверки всех стратегий. **Ни один из них не является текущей основной сводкой.** Это ошибка организации и трактовки работы ассистентом, не изменение требований пользователя.

## Куда смотреть, а куда НЕ смотреть

1. **Правила, которые сохраняются:** [RESEARCH_MANDATE_LOCKED.md](RESEARCH_MANDATE_LOCKED.md) и [issue #9](https://github.com/SanChi117/EMBER-Research-Engine/issues/9). Только Binance USD-M Futures; оригиналы, не самодельные «готовые системы»; честная причинность, расходы, риск, независимая OOS/PAPER проверка.
2. **Единственный указатель на факты и незакрытые вопросы — ЭТОТ ФАЙЛ.** Сводки A225–A249, `RESEARCH_A231_REEVALUATION_QUEUE.md`, ранние shortlists, branch reports и `README.md` могут быть только **архивными снимками**; не интерпретировать отдельно как текущее разрешение к торговле или финальную оценку кандидата.
3. **Реестр охвата, не таблица прибыльных стратегий:** A234 [74 записи/варианта](https://github.com/SanChi117/EMBER-Research-Engine/blob/research/a234-all-promising-candidates-review/research/all_candidates_a234/registry.json) + A236 [2 добавленных варианта R075/R076](https://github.com/SanChi117/EMBER-Research-Engine/blob/research/a236-unclassified-source-triage-20261031/research/all_candidates_a234/A236_QUEUE_EXTENSION.json) = **76 учётных записей, НЕ 76 независимых систем или проведённых проверок**. Актуальный достоверный реестр статусов всех 76 карточек в main НЕ собран; нельзя объявить охват завершённым.
4. **USER VETO без изменений:** [RESEARCH_USER_VETO_A220.md](RESEARCH_USER_VETO_A220.md), A214–A216 запрещены. Действующие PAPER-планировщики и любые биржевые ордера НЕ менялись в этом цикле очистки.

## Критическая найденная ошибка A245

[GitHub Actions run 41245981488](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41245981488) завершён с 2/2 `CI SUCCESS`, но это **НЕ 36/36 экономических прогонов**:

| Группа | Подготовлено | Нативных экономических результатов | BLOCKED runtime | Доказательство |
|---|---:|---:|---:|---|
| A: MTF_Hybrid, FailureToReturn, FVGChannel | 18 | **18** | 0 | [18 записей и SHA artifacts](https://github.com/SanChi117/EMBER-Research-Engine/blob/research/a245-six-unreviewed-originals-batch-20261031/research/a245_other_originals/A245_GROUP_A_VERIFIED_NATIVE_METRICS.json) |
| B: VolatilitySystem, FAdxSma, FReinforced | 18 | **12** | **6** | [фактические 18 записей, из них 6 BLOCKED](https://github.com/SanChi117/EMBER-Research-Engine/blob/research/a245-six-unreviewed-originals-batch-20261031/research/a245_other_originals/A245_GROUP_B_FINAL_FACTUAL_STATUS.json) |
| **ВСЕГО** | **36** | **30** | **6** | `SUCCESS` CI не означает `PASS` торговли |

**Причина 6 BLOCKED:** точный оригинальный `FReinforcedStrategy` не может быть запущен в Freqtrade 2026.9: `Cannot determine parameter space for adx_period`. Все шесть сценариев **не имеют PnL**, это НЕ 0%, не убыточность и не 6 выполненных backtests. Артефакты группа A ID 13058698873 SHA256 `7c6717d0207085083f89af0104674eb602e9dcab6c4aceafe6a3c9cea0b32eae`; группа B ID 13059429478 SHA256 `ebbc148173aaefecdebd9628ef73ed22f0f0544a0b9cc5d5e60b8192d7b47471`.

**Только контрольный 3-парный BTC/ETH/SOL счёт** $1000, ставка $100, max3, исходники SHA фиксированы; каждый период reset, комиссии BASE 0.05% и STRESS 0.11% на сторону. **НЕ оригинальная авторская конфигурация счёта**, не настоящий ликвидационный и orderbook/fill replay, не нетронутый OOS.

STRESS модельное NET % счёта:

| Стратегия | 2024 | 2025 | янв.–май 2026 | Правильный статус |
|---|---:|---:|---:|---|
| R027 MTF_Hybrid | −34.47 | −10.63 | −10.10 | NEGATIVE_CONTROLLED_SCREEN |
| R028 FVGChannel | −23.70 | −19.43 | −18.24 | NEGATIVE_CONTROLLED_FUTURES_TRANSFER (не исходный авторский USD-M профиль) |
| R029 FailureToReturn | +0.39 | +0.41 | +0.41 | LOW_POWER_POSITIVE_SCREEN: только 24,12,6 сделок; не прибыльная подтверждённая |
| R030 VolatilitySystem | **+15.63** | **+16.17** | **+2.24** | POSITIVE_CONTROLLED_SCREEN, **ОПАСНЫЙ source stop -100% и DCA/2×**, нет проверки реальных ликвидаций |
| R012 FAdxSma | +1.04 | −3.54 | −0.69 | MIXED / NEGATIVE_STRESS_2_OF_3 |
| R013 FReinforced | — | — | — | **BLOCKED 6/6, НЕТ РЕЗУЛЬТАТОВ** |

**Эти положительные числа не разрешают PAPER и не доказывают стратегию.**

## Явно отделённые типы более ранней работы

- **Нативное экономическое исследование, но не доказательство доходности и не полное исполнение:** A235 (исправление таймфреймов), [A237 TrendFollowing авторский общий счёт](https://github.com/SanChi117/EMBER-Research-Engine/blob/research/a237-trendfollowing-author-account-20261031/research/A237_AUTHOR_RESULTS_RU.md), [A238 Risk_Stair_S5 5× авторский счёт](https://github.com/SanChi117/EMBER-Research-Engine/blob/research/a238-risk-stair-author-account-20261031/research/A238_RISK_AUTHOR_RESULTS_RU.md), [A240 Double MA BTC+ETH один общий счёт](https://github.com/SanChi117/EMBER-Research-Engine/blob/research/a240-doublema-one-wallet-native-20261101/research/A240_AUTHOR_ONE_WALLET_RESULTS_RU.md), A245. Оригинальный счёт A240 показал отрицательную STRESS 2026; A233 4 отдельных $10k кошелька нельзя подменять A240 общим BTC/ETH.
- **Аудит исходников, НЕ новый экономический тест:** [A241 BearRegime](https://github.com/SanChi117/EMBER-Research-Engine/blob/research/a241-bearregime-author-evidence-audit-20261031/research/A241_BEARREGIME_AUTHOR_PORTFOLIO_EVIDENCE_RU.md); [A242 Winner15m source config](https://github.com/SanChi117/EMBER-Research-Engine/blob/research/a242-winner15m-original-config-recovery-20261031/research/A242_WINNER15M_ORIGINAL_BACKTEST_CONFIG_RU.md); [A246 7 других источников](https://github.com/SanChi117/EMBER-Research-Engine/blob/research/a246-other-promising-source-rechecks-20261031/research/A246_OTHER_SEVEN_SOURCE_REVALUATION_RU.md). Авторские ROI и CSV не равны independently verified after-cost portfolio.
- **Задания/пререгистрации без экономического завершения:** [A247 четыре других исходника](https://github.com/SanChi117/EMBER-Research-Engine/blob/research/a247-other-four-original-extended-regimes-20261031/research/a247_other_four/PREREG_RU.md): файлы планирования и source pins есть, **рабочего отчёта 24 native runs нет**. Не считать проверенными. A243 Winner15m CI `SUCCESS`, но результат не переносить в текущую сводку без trade PnL/evidence отдельной проверки.
- **Устаревший/методически неполный предшественник:** A228–A230 подменяли авторские таймфреймы конфигом 1h, их проценты не являются author native baseline. A231 и A239–A249 — пересекающиеся промежуточные снимки, в них устаревшие статусы `in progress`, неполные universe и разная экономическая модель.
- **Старые отрицательные тесты не стираются:** A203 dip_catcher, A198 SOL V9 proxy, A191 SingleB Binance ETH, и прочие имеют конкретные исторические границы. Разные модели/пары/авторские счета нельзя суммировать либо сравнивать как идентичные.

## Что считать НЕ выполненным

- **76 записей не прошли полную переоценку** и не объединены в законченный оригинальный source/market/funding/fill/OOS реестр.
- **0 VERIFIED_FUTURES_CANDIDATE**. Некоторые контролируемые тесты положительные; ни один не удовлетворяет полному требованию ликвидации, исполнения, исходного портфеля и независимого forward.
- Ведение нового отдельного `RESEARCH_PROGRESS_A###` на каждый шаг **прекратить**: это главный источник беспорядка. Все дальнейшие уточнения текущего состояния должны идти в этот указатель с датой, ссылаясь на старые доказательства и не переписывая их.

## Метки для любых старых записей

- `ARCHIVE_SNAPSHOT_SUPERSEDED`: исторический файл и статус конкретного момента, **не текущая точка входа**.
- `AUTHOR_RESULT_ONLY`: число опубликовано автором и не подтверждено нашим исполнителем.
- `SOURCE_AUDIT_ONLY`: прочитан оригинал / SHA, экономических результатов нет.
- `CONTROLLED_NATIVE_SCREEN`: подлинный Freqtrade тест в ограниченном контрольном универсуме, **не авторский общий портфель**.
- `AUTHOR_ACCOUNT_BACKTEST_UNVERIFIED_EXECUTION`: восстановлен авторский счёт, но исполнение и OOS не доказаны.
- `BLOCKED_RUNTIME`: не было валидного вычисления PnL.
- `VERIFIED_FUTURES_CANDIDATE`: сейчас **ни одного**.

**Это файловая очистка индекса и исправление ошибочных записей, а НЕ удаление Git commit history, SHA-доказательств и торговых журналов.** Git историю нельзя «подчистить» обычной пометкой, и принудительное переписывание истории опасно для восстановления ошибок. Мандат и пользовательские запреты неизменны.

## ВАЖНО: автоматический повтор CI от правки документации — ещё одна ошибка

У исследовательских веток A245 и A243 в GitHub Actions настроен `on.push` на весь каталог документов. **Редактирование моих собственных архивных пометок повторно запустило дорогие тестовые workflow**, которые не являются новыми независимыми гипотезами или результатами. Повторные run ID **не считать новыми верификациями** и не добавлять в статистику 76 кандидатов. A245: [все runs ветки](https://github.com/SanChi117/EMBER-Research-Engine/actions/workflows/ember-a245-six-other-originals.yml); A243: [runs исходного Winner15m workflow](https://github.com/SanChi117/EMBER-Research-Engine/actions/workflows/ember-a243-winner15m-original-native.yml).

**Исправить триггеры пока не удалось:** попытка технически ограничить push-запуски была заблокирована доступными средствами записи. Поэтому файлы этих веток больше не редактировать только ради пометок. Для отмены уже автоматически стартовавших лишних CI используется интерфейс GitHub Actions: открыть лишний run → `Cancel workflow`; для запрета новых — `Disable workflow`, если доступно владельцу. Не отменять старые доказательные успешные runs/артефакты, не трогать PAPER automation.
