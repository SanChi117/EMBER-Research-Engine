# ISO01 + ISO02: рабочий изолированный research-контур Ember

**Статус: PAPER ONLY · NOT_TRADE_READY.** Рабочим здесь назван воспроизводимый контур `восприятие → идентификация → состояние → связи → сценарии наблюдения`. Это не завершение авторской семантики, не торговое решение, не backtest и не разрешение исполнения.

## Изоляция и маршруты

Ветка: `research/ember-integrated-working-20261025`.

База: `46a57eaa38c1e6f03cabf8b6d3be8d1a69f311cf`.

- Route A остаётся `C57 / A_4H_TRIGGER_15M_VC`.
- Route B остаётся общим `C58 / B_4H_VC_1H_IDM`.
- Наш Route C перенесён в `ISO01`; старое пересечение имени C58 не используется.
- `ISO02` только читает frozen-результаты и не объединяет parent-объекты разных маршрутов.
- Общие journal, map, handoff, accepted evidence и другие ветки не изменялись. PR и merge не создавались.

## Что работает

1. SHA-256 и schema проверяются до разбора каждого из трёх входов.
2. ISO01 заново строится из полного frozen C56, а не принимается как доверенный промежуточный JSON.
3. Создаются стабильно идентифицированные parent/child-объекты с `known_at_ms`, source status и `ADAPTED_ENGINE`.
4. Связи проверяются на dangling references, дубликаты, route/symbol mismatch и временной контракт.
5. Для Route A/C последующий child обязан быть строго позже parent knowledge.
6. Для Route B `PREKNOWN_AT_CONTACT` означает известность не позднее 3m contact, а не обязательно раньше 4H source.
7. Каждый parent получает ровно один сценарий наблюдения. Right censorship отделена от отсутствия в полном источнике.
8. Все авторские решения остаются `UNKNOWN`/`NEEDS_SOURCE`; entry, stop, target, orders, fills, trades и PnL заблокированы.

## Полный frozen replay

- 2 052 объекта: Route A 277, Route B 182, Route C 1 593.
- 1 204 внутримаршрутные связи; перекрёстных связей 0.
- 848 сценариев: Route A 153, Route B 153, Route C 542.
- Route A: 124 технические последовательности, 23 отсутствия в полном frozen source, 6 right-censored UNKNOWN.
- Route B: 29 parent с preknown unswept child-кандидатами; 124 без такого наблюдаемого кандидата или без contact.
- Route C: 509 BOTH, 30 ONLY_3M, 3 ONLY_5M.
- Canonical graph: 2 415 236 байт.
- SHA-256: `86bb21675c9dd179b7f153b61a2fcf01c049dfc843b95c1ecc87ac3dc9afc8eb`.

## Проверка

- ISO01: 40 tests на каждой версии Python.
- ISO02: 46 positive/negative/adversarial tests на каждой версии Python.
- Всего: 86/86 PASS на Python 3.10.22, 3.11.2 и 3.12.12.
- Полный replay выполнен на всех трёх версиях; graph bytes и SHA-256 совпали.
- Повтор внутри replay также побайтово совпал.

Запуск из `research/mtf-element-audit-v1`:

```bash
python3 -m unittest discover -s d05 -p 'test_iso0*.py'
python3 tests/probe_iso02_integrated_perception_graph.py /tmp/ember-iso02-graph.json
```

Внешняя сеть для replay не нужна. Исходные 45/60 ZIP заново не скачивались: это проверка pinned frozen evidence, а не новая независимая аттестация первичных рыночных данных.

## Что остаётся закрытым

`AUTHOR_TYPED_POI_AND_VALID_TEST`, авторский VC, IDM/StrongHL/ahead, timestamped BOS, FTA/session/structural stop и авторские entry/goldens имеют состояние `NEEDS_SOURCE`. Execution/PAPER OOS/performance — `NOT_STARTED`.

Следовательно, semantic gate E не объявлен пройденным. F/G backtest, H Trade Plan, live и любые выводы о прибыли остаются запрещены. Следующий допустимый шаг — предоставить авторские источники/goldens и отдельно аттестовать семантику; только после этого проектировать decision layer и paper gate.
