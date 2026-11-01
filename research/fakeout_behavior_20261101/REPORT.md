# EMBER: ложный пробой / возврат в диапазон — H4 проверка поведения, 01.11.2026

**Статус: BEHAVIOR_ONLY / NOT_VERIFIED / NOT AN ORIGINAL STRATEGY BACKTEST.** Отдельное исследование повторяемого поведения, НЕ модификация системы EMBER или исполнение сделок.

## Замороженная до подсчёта методика
- Binance USD-M futures OHLCV 4h, UTC, только закрытые свечи 2024-02-16 — 2026-10-31. Для STRK и ZK история начинается с доступной даты листинга.
- Основные BTC/ETH/SOL; сравнительные слабые STRK/ZK/LDO (не основание выбора пула).
- Границы: high/low предыдущих 20 завершённых свечей. ATR = средний True Range предыдущих 14 завершённых свечей (без текущей).
- Пробой: high за верхней либо low за нижней границей более 0.1 ATR. Если на закрытии той же 4h свечи цена обратно ВНУТРИ границ = FAKE, направление против пробоя. Если закрытие вне диапазона = TRUE, направление по пробою. Двойные выходы за верх и низ исключены. NEAR-контроль без превышения 0.1 ATR при близости к границе и закрытии внутри.
- Сигнал известен только после закрытия 4h. Вход по OPEN следующей 4h. Симметричные уровни TP +1 ATR и SL -1 ATR от входа; максимум 12 последующих 4h свечей. Если в одной свече задеты TP и SL, статус AMBIGUOUS, а в средней прибыли защитная оценка как LOSS (не притворяться, что известен порядок). По истечении 12 баров выйти по CLOSE последнего бара.
- Отдельный cooldown 12 баров внутри каждого подтипа события; пересечения между подтипами и корреляция монет возможны, поэтому интервалы Wilson только ориентировочные.
- Условные roundtrip costs: BASE 0.20%, STRESS 0.35% цены позиции; не настоящие fees/funding/slippage или orderbook. Возврат по 1ATR фиксированный только для СИММЕТРИЧНОГО измерителя поведения, не предлагаемый TP стратегии.
- Early до 2025-06-01 UTC, late после. Ex-ante trend regime = (close на баре до сигнала - close 80 баров назад) / (предыдущий ATR * sqrt(80)); UP если >1, DOWN если <-1, иначе SIDE. Порог не подбирался под итоги.

## Исходные данные, воспроизведение
Реальный Binance endpoint /fapi/v1/klines, по 4 страницы до 1500 свечей на пару; запрос startTime=1708041600000 плюс каждые 1500 четырёхчасовых свечей. Документация: https://developers.binance.info/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data.
Шесть файлов data/*.csv хранят исходные OHLCV с Git blob SHA. events.csv хранит все найденные события и результаты; reproduce.js — фактически исполненная логика на тех же свечах (запуск: node research/fakeout_behavior_20261101/reproduce.js).
Сверены оригинальные исходники P07 PullbackRetest blob 4b04c1834bbf0a3e69d9e67542aea204718550c8 и P06 FailureToReturn blob 6e80c0b96754c21744726120b6904f940621ec01: это ПРОДОЛЖЕНИЕ ПОСЛЕ РЕТЕСТА, а не данная модель возврата. Поэтому результаты ниже не относятся к их оригинальным стратегиям.

## Полная статистика: количество, исходы, доля побед, % изменения цены и расходы
```json
{
  "quality": {
    "BTCUSDT": {
      "bars": 5934,
      "first": 1708041600000,
      "last": 1793476800000,
      "gaps": 0,
      "ohlcInvalid": 0,
      "gitBlobSha": "0e6816010cab6d216f175bcd394c67c965dd2768"
    },
    "ETHUSDT": {
      "bars": 5934,
      "first": 1708041600000,
      "last": 1793476800000,
      "gaps": 0,
      "ohlcInvalid": 0,
      "gitBlobSha": "c53e1888bac32f94c28579e9accedf0bcb2f085c"
    },
    "SOLUSDT": {
      "bars": 5934,
      "first": 1708041600000,
      "last": 1793476800000,
      "gaps": 0,
      "ohlcInvalid": 0,
      "gitBlobSha": "c5e6312f6eed3efb8e9ae0157aeaca9949275907"
    },
    "STRKUSDT": {
      "bars": 5906,
      "first": 1708444800000,
      "last": 1793476800000,
      "gaps": 0,
      "ohlcInvalid": 0,
      "gitBlobSha": "4b59ea3822c3fc35cdaa5281c86bcac6082efd19"
    },
    "ZKUSDT": {
      "bars": 5200,
      "first": 1718611200000,
      "last": 1793476800000,
      "gaps": 0,
      "ohlcInvalid": 0,
      "gitBlobSha": "f3abc719da884d12fa7c9e7f33d9a7fb6494c36f"
    },
    "LDOUSDT": {
      "bars": 5934,
      "first": 1708041600000,
      "last": 1793476800000,
      "gaps": 0,
      "ohlcInvalid": 0,
      "gitBlobSha": "ccf83350600c57a878b2d04c72c0c59882fe6b39"
    }
  },
  "reject": {
    "BTCUSDT": {
      "gap": 0,
      "doubleSweep": 2
    },
    "ETHUSDT": {
      "gap": 0,
      "doubleSweep": 0
    },
    "SOLUSDT": {
      "gap": 0,
      "doubleSweep": 2
    },
    "STRKUSDT": {
      "gap": 0,
      "doubleSweep": 0
    },
    "ZKUSDT": {
      "gap": 0,
      "doubleSweep": 2
    },
    "LDOUSDT": {
      "gap": 0,
      "doubleSweep": 1
    }
  },
  "families": {
    "fake": {
      "all": {
        "n": 1522,
        "win": 745,
        "loss": 715,
        "amb": 23,
        "timeout": 39,
        "winPctResolved": 51.03,
        "wilson95": [
          48.5,
          53.6
        ],
        "meanGrossPct": 0.0262,
        "meanBasePct": -0.1738,
        "meanStressPct": -0.3238
      },
      "main": {
        "n": 777,
        "win": 384,
        "loss": 358,
        "amb": 11,
        "timeout": 24,
        "winPctResolved": 51.75,
        "wilson95": [
          48.2,
          55.3
        ],
        "meanGrossPct": 0.1038,
        "meanBasePct": -0.0962,
        "meanStressPct": -0.2462
      },
      "weak": {
        "n": 745,
        "win": 361,
        "loss": 357,
        "amb": 12,
        "timeout": 15,
        "winPctResolved": 50.28,
        "wilson95": [
          46.6,
          53.9
        ],
        "meanGrossPct": -0.0548,
        "meanBasePct": -0.2548,
        "meanStressPct": -0.4048
      },
      "early": {
        "n": 719,
        "win": 364,
        "loss": 327,
        "amb": 11,
        "timeout": 17,
        "winPctResolved": 52.68,
        "wilson95": [
          49,
          56.4
        ],
        "meanGrossPct": 0.0802,
        "meanBasePct": -0.1198,
        "meanStressPct": -0.2698
      },
      "late": {
        "n": 803,
        "win": 381,
        "loss": 388,
        "amb": 12,
        "timeout": 22,
        "winPctResolved": 49.54,
        "wilson95": [
          46,
          53.1
        ],
        "meanGrossPct": -0.0222,
        "meanBasePct": -0.2222,
        "meanStressPct": -0.3722
      },
      "mainEarly": {
        "n": 378,
        "win": 197,
        "loss": 166,
        "amb": 5,
        "timeout": 10,
        "winPctResolved": 54.27,
        "wilson95": [
          49.1,
          59.3
        ],
        "meanGrossPct": 0.1684,
        "meanBasePct": -0.0316,
        "meanStressPct": -0.1816
      },
      "mainLate": {
        "n": 399,
        "win": 187,
        "loss": 192,
        "amb": 6,
        "timeout": 14,
        "winPctResolved": 49.34,
        "wilson95": [
          44.3,
          54.4
        ],
        "meanGrossPct": 0.0427,
        "meanBasePct": -0.1573,
        "meanStressPct": -0.3073
      },
      "weakEarly": {
        "n": 341,
        "win": 167,
        "loss": 161,
        "amb": 6,
        "timeout": 7,
        "winPctResolved": 50.91,
        "wilson95": [
          45.5,
          56.3
        ],
        "meanGrossPct": -0.0175,
        "meanBasePct": -0.2175,
        "meanStressPct": -0.3675
      },
      "weakLate": {
        "n": 404,
        "win": 194,
        "loss": 196,
        "amb": 6,
        "timeout": 8,
        "winPctResolved": 49.74,
        "wilson95": [
          44.8,
          54.7
        ],
        "meanGrossPct": -0.0863,
        "meanBasePct": -0.2863,
        "meanStressPct": -0.4363
      },
      "bySymbol": {
        "BTCUSDT": {
          "n": 264,
          "win": 113,
          "loss": 130,
          "amb": 7,
          "timeout": 14,
          "winPctResolved": 46.5,
          "wilson95": [
            40.3,
            52.8
          ],
          "meanGrossPct": -0.042,
          "meanBasePct": -0.242,
          "meanStressPct": -0.392
        },
        "ETHUSDT": {
          "n": 258,
          "win": 141,
          "loss": 107,
          "amb": 3,
          "timeout": 7,
          "winPctResolved": 56.85,
          "wilson95": [
            50.6,
            62.9
          ],
          "meanGrossPct": 0.2943,
          "meanBasePct": 0.0943,
          "meanStressPct": -0.0557
        },
        "SOLUSDT": {
          "n": 255,
          "win": 130,
          "loss": 121,
          "amb": 1,
          "timeout": 3,
          "winPctResolved": 51.79,
          "wilson95": [
            45.6,
            57.9
          ],
          "meanGrossPct": 0.0621,
          "meanBasePct": -0.1379,
          "meanStressPct": -0.2879
        },
        "STRKUSDT": {
          "n": 270,
          "win": 132,
          "loss": 128,
          "amb": 5,
          "timeout": 5,
          "winPctResolved": 50.77,
          "wilson95": [
            44.7,
            56.8
          ],
          "meanGrossPct": -0.0584,
          "meanBasePct": -0.2584,
          "meanStressPct": -0.4084
        },
        "ZKUSDT": {
          "n": 217,
          "win": 95,
          "loss": 113,
          "amb": 4,
          "timeout": 5,
          "winPctResolved": 45.67,
          "wilson95": [
            39,
            52.5
          ],
          "meanGrossPct": -0.2941,
          "meanBasePct": -0.4941,
          "meanStressPct": -0.6441
        },
        "LDOUSDT": {
          "n": 258,
          "win": 134,
          "loss": 116,
          "amb": 3,
          "timeout": 5,
          "winPctResolved": 53.6,
          "wilson95": [
            47.4,
            59.7
          ],
          "meanGrossPct": 0.1502,
          "meanBasePct": -0.0498,
          "meanStressPct": -0.1998
        }
      },
      "byRegime": {
        "UP": {
          "n": 70,
          "win": 44,
          "loss": 25,
          "amb": 1,
          "timeout": 0,
          "winPctResolved": 63.77,
          "wilson95": [
            52,
            74.1
          ],
          "meanGrossPct": 0.5825,
          "meanBasePct": 0.3825,
          "meanStressPct": 0.2325
        },
        "DOWN": {
          "n": 130,
          "win": 77,
          "loss": 50,
          "amb": 1,
          "timeout": 2,
          "winPctResolved": 60.63,
          "wilson95": [
            51.9,
            68.7
          ],
          "meanGrossPct": 0.4867,
          "meanBasePct": 0.2867,
          "meanStressPct": 0.1367
        },
        "SIDE": {
          "n": 1322,
          "win": 624,
          "loss": 640,
          "amb": 21,
          "timeout": 37,
          "winPctResolved": 49.37,
          "wilson95": [
            46.6,
            52.1
          ],
          "meanGrossPct": -0.0486,
          "meanBasePct": -0.2486,
          "meanStressPct": -0.3986
        }
      }
    },
    "true": {
      "all": {
        "n": 1407,
        "win": 697,
        "loss": 652,
        "amb": 35,
        "timeout": 23,
        "winPctResolved": 51.67,
        "wilson95": [
          49,
          54.3
        ],
        "meanGrossPct": 0.0189,
        "meanBasePct": -0.1811,
        "meanStressPct": -0.3311
      },
      "main": {
        "n": 720,
        "win": 340,
        "loss": 343,
        "amb": 22,
        "timeout": 15,
        "winPctResolved": 49.78,
        "wilson95": [
          46,
          53.5
        ],
        "meanGrossPct": -0.0775,
        "meanBasePct": -0.2775,
        "meanStressPct": -0.4275
      },
      "weak": {
        "n": 687,
        "win": 357,
        "loss": 309,
        "amb": 13,
        "timeout": 8,
        "winPctResolved": 53.6,
        "wilson95": [
          49.8,
          57.4
        ],
        "meanGrossPct": 0.12,
        "meanBasePct": -0.08,
        "meanStressPct": -0.23
      },
      "early": {
        "n": 647,
        "win": 330,
        "loss": 294,
        "amb": 12,
        "timeout": 11,
        "winPctResolved": 52.88,
        "wilson95": [
          49,
          56.8
        ],
        "meanGrossPct": 0.0042,
        "meanBasePct": -0.1958,
        "meanStressPct": -0.3458
      },
      "late": {
        "n": 760,
        "win": 367,
        "loss": 358,
        "amb": 23,
        "timeout": 12,
        "winPctResolved": 50.62,
        "wilson95": [
          47,
          54.2
        ],
        "meanGrossPct": 0.0314,
        "meanBasePct": -0.1686,
        "meanStressPct": -0.3186
      },
      "mainEarly": {
        "n": 333,
        "win": 166,
        "loss": 151,
        "amb": 9,
        "timeout": 7,
        "winPctResolved": 52.37,
        "wilson95": [
          46.9,
          57.8
        ],
        "meanGrossPct": -0.0461,
        "meanBasePct": -0.2461,
        "meanStressPct": -0.3961
      },
      "mainLate": {
        "n": 387,
        "win": 174,
        "loss": 192,
        "amb": 13,
        "timeout": 8,
        "winPctResolved": 47.54,
        "wilson95": [
          42.5,
          52.7
        ],
        "meanGrossPct": -0.1046,
        "meanBasePct": -0.3046,
        "meanStressPct": -0.4546
      },
      "weakEarly": {
        "n": 314,
        "win": 164,
        "loss": 143,
        "amb": 3,
        "timeout": 4,
        "winPctResolved": 53.42,
        "wilson95": [
          47.8,
          58.9
        ],
        "meanGrossPct": 0.0575,
        "meanBasePct": -0.1425,
        "meanStressPct": -0.2925
      },
      "weakLate": {
        "n": 373,
        "win": 193,
        "loss": 166,
        "amb": 10,
        "timeout": 4,
        "winPctResolved": 53.76,
        "wilson95": [
          48.6,
          58.9
        ],
        "meanGrossPct": 0.1725,
        "meanBasePct": -0.0275,
        "meanStressPct": -0.1775
      },
      "bySymbol": {
        "BTCUSDT": {
          "n": 238,
          "win": 113,
          "loss": 105,
          "amb": 12,
          "timeout": 8,
          "winPctResolved": 51.83,
          "wilson95": [
            45.2,
            58.4
          ],
          "meanGrossPct": -0.0087,
          "meanBasePct": -0.2087,
          "meanStressPct": -0.3587
        },
        "ETHUSDT": {
          "n": 236,
          "win": 109,
          "loss": 116,
          "amb": 6,
          "timeout": 5,
          "winPctResolved": 48.44,
          "wilson95": [
            42,
            54.9
          ],
          "meanGrossPct": -0.1035,
          "meanBasePct": -0.3035,
          "meanStressPct": -0.4535
        },
        "SOLUSDT": {
          "n": 246,
          "win": 118,
          "loss": 122,
          "amb": 4,
          "timeout": 2,
          "winPctResolved": 49.17,
          "wilson95": [
            42.9,
            55.5
          ],
          "meanGrossPct": -0.1193,
          "meanBasePct": -0.3193,
          "meanStressPct": -0.4693
        },
        "STRKUSDT": {
          "n": 244,
          "win": 117,
          "loss": 124,
          "amb": 2,
          "timeout": 1,
          "winPctResolved": 48.55,
          "wilson95": [
            42.3,
            54.8
          ],
          "meanGrossPct": -0.1667,
          "meanBasePct": -0.3667,
          "meanStressPct": -0.5167
        },
        "ZKUSDT": {
          "n": 192,
          "win": 106,
          "loss": 77,
          "amb": 7,
          "timeout": 2,
          "winPctResolved": 57.92,
          "wilson95": [
            50.7,
            64.8
          ],
          "meanGrossPct": 0.3235,
          "meanBasePct": 0.1235,
          "meanStressPct": -0.0265
        },
        "LDOUSDT": {
          "n": 251,
          "win": 134,
          "loss": 108,
          "amb": 4,
          "timeout": 5,
          "winPctResolved": 55.37,
          "wilson95": [
            49.1,
            61.5
          ],
          "meanGrossPct": 0.2429,
          "meanBasePct": 0.0429,
          "meanStressPct": -0.1071
        }
      },
      "byRegime": {
        "UP": {
          "n": 51,
          "win": 27,
          "loss": 22,
          "amb": 2,
          "timeout": 0,
          "winPctResolved": 55.1,
          "wilson95": [
            41.3,
            68.1
          ],
          "meanGrossPct": 0.084,
          "meanBasePct": -0.116,
          "meanStressPct": -0.266
        },
        "DOWN": {
          "n": 119,
          "win": 59,
          "loss": 59,
          "amb": 1,
          "timeout": 0,
          "winPctResolved": 50,
          "wilson95": [
            41.1,
            58.9
          ],
          "meanGrossPct": 0.1015,
          "meanBasePct": -0.0985,
          "meanStressPct": -0.2485
        },
        "SIDE": {
          "n": 1237,
          "win": 611,
          "loss": 571,
          "amb": 32,
          "timeout": 23,
          "winPctResolved": 51.69,
          "wilson95": [
            48.8,
            54.5
          ],
          "meanGrossPct": 0.0083,
          "meanBasePct": -0.1917,
          "meanStressPct": -0.3417
        }
      }
    },
    "near": {
      "all": {
        "n": 1219,
        "win": 571,
        "loss": 584,
        "amb": 21,
        "timeout": 43,
        "winPctResolved": 49.44,
        "wilson95": [
          46.6,
          52.3
        ],
        "meanGrossPct": -0.0151,
        "meanBasePct": -0.2151,
        "meanStressPct": -0.3651
      },
      "main": {
        "n": 559,
        "win": 268,
        "loss": 259,
        "amb": 10,
        "timeout": 22,
        "winPctResolved": 50.85,
        "wilson95": [
          46.6,
          55.1
        ],
        "meanGrossPct": 0.0608,
        "meanBasePct": -0.1392,
        "meanStressPct": -0.2892
      },
      "weak": {
        "n": 660,
        "win": 303,
        "loss": 325,
        "amb": 11,
        "timeout": 21,
        "winPctResolved": 48.25,
        "wilson95": [
          44.4,
          52.2
        ],
        "meanGrossPct": -0.0793,
        "meanBasePct": -0.2793,
        "meanStressPct": -0.4293
      },
      "early": {
        "n": 576,
        "win": 261,
        "loss": 282,
        "amb": 8,
        "timeout": 25,
        "winPctResolved": 48.07,
        "wilson95": [
          43.9,
          52.3
        ],
        "meanGrossPct": -0.0848,
        "meanBasePct": -0.2848,
        "meanStressPct": -0.4348
      },
      "late": {
        "n": 643,
        "win": 310,
        "loss": 302,
        "amb": 13,
        "timeout": 18,
        "winPctResolved": 50.65,
        "wilson95": [
          46.7,
          54.6
        ],
        "meanGrossPct": 0.0474,
        "meanBasePct": -0.1526,
        "meanStressPct": -0.3026
      },
      "mainEarly": {
        "n": 276,
        "win": 128,
        "loss": 129,
        "amb": 4,
        "timeout": 15,
        "winPctResolved": 49.81,
        "wilson95": [
          43.7,
          55.9
        ],
        "meanGrossPct": 0.0228,
        "meanBasePct": -0.1772,
        "meanStressPct": -0.3272
      },
      "mainLate": {
        "n": 283,
        "win": 140,
        "loss": 130,
        "amb": 6,
        "timeout": 7,
        "winPctResolved": 51.85,
        "wilson95": [
          45.9,
          57.7
        ],
        "meanGrossPct": 0.0978,
        "meanBasePct": -0.1022,
        "meanStressPct": -0.2522
      },
      "weakEarly": {
        "n": 300,
        "win": 133,
        "loss": 153,
        "amb": 4,
        "timeout": 10,
        "winPctResolved": 46.5,
        "wilson95": [
          40.8,
          52.3
        ],
        "meanGrossPct": -0.1838,
        "meanBasePct": -0.3838,
        "meanStressPct": -0.5338
      },
      "weakLate": {
        "n": 360,
        "win": 170,
        "loss": 172,
        "amb": 7,
        "timeout": 11,
        "winPctResolved": 49.71,
        "wilson95": [
          44.4,
          55
        ],
        "meanGrossPct": 0.0078,
        "meanBasePct": -0.1922,
        "meanStressPct": -0.3422
      },
      "bySymbol": {
        "BTCUSDT": {
          "n": 192,
          "win": 84,
          "loss": 94,
          "amb": 8,
          "timeout": 6,
          "winPctResolved": 47.19,
          "wilson95": [
            40,
            54.5
          ],
          "meanGrossPct": -0.1171,
          "meanBasePct": -0.3171,
          "meanStressPct": -0.4671
        },
        "ETHUSDT": {
          "n": 158,
          "win": 79,
          "loss": 72,
          "amb": 1,
          "timeout": 6,
          "winPctResolved": 52.32,
          "wilson95": [
            44.4,
            60.1
          ],
          "meanGrossPct": 0.0941,
          "meanBasePct": -0.1059,
          "meanStressPct": -0.2559
        },
        "SOLUSDT": {
          "n": 209,
          "win": 105,
          "loss": 93,
          "amb": 1,
          "timeout": 10,
          "winPctResolved": 53.03,
          "wilson95": [
            46.1,
            59.9
          ],
          "meanGrossPct": 0.199,
          "meanBasePct": -0.001,
          "meanStressPct": -0.151
        },
        "STRKUSDT": {
          "n": 231,
          "win": 105,
          "loss": 111,
          "amb": 6,
          "timeout": 9,
          "winPctResolved": 48.61,
          "wilson95": [
            42,
            55.2
          ],
          "meanGrossPct": -0.0352,
          "meanBasePct": -0.2352,
          "meanStressPct": -0.3852
        },
        "ZKUSDT": {
          "n": 191,
          "win": 84,
          "loss": 98,
          "amb": 4,
          "timeout": 5,
          "winPctResolved": 46.15,
          "wilson95": [
            39.1,
            53.4
          ],
          "meanGrossPct": -0.2337,
          "meanBasePct": -0.4337,
          "meanStressPct": -0.5837
        },
        "LDOUSDT": {
          "n": 238,
          "win": 114,
          "loss": 116,
          "amb": 1,
          "timeout": 7,
          "winPctResolved": 49.57,
          "wilson95": [
            43.2,
            56
          ],
          "meanGrossPct": 0.0018,
          "meanBasePct": -0.1982,
          "meanStressPct": -0.3482
        }
      },
      "byRegime": {
        "UP": {
          "n": 30,
          "win": 10,
          "loss": 18,
          "amb": 2,
          "timeout": 0,
          "winPctResolved": 35.71,
          "wilson95": [
            20.7,
            54.2
          ],
          "meanGrossPct": -0.5754,
          "meanBasePct": -0.7754,
          "meanStressPct": -0.9254
        },
        "DOWN": {
          "n": 95,
          "win": 47,
          "loss": 47,
          "amb": 1,
          "timeout": 0,
          "winPctResolved": 50,
          "wilson95": [
            40.1,
            59.9
          ],
          "meanGrossPct": -0.1014,
          "meanBasePct": -0.3014,
          "meanStressPct": -0.4514
        },
        "SIDE": {
          "n": 1094,
          "win": 514,
          "loss": 519,
          "amb": 18,
          "timeout": 43,
          "winPctResolved": 49.76,
          "wilson95": [
            46.7,
            52.8
          ],
          "meanGrossPct": 0.0078,
          "meanBasePct": -0.1922,
          "meanStressPct": -0.3422
        }
      }
    }
  }
}
```

## Ограничения
Это НЕ доказательство чистой прибыльности: нет точных funding, mark, gap/slippage, биржевого fill и ликвидаций, экономического портфеля, нативного исходника данного reversal-механизма, неиспользованного OOS или проспективного PAPER. Calendar years здесь вспомогательная нарезка, режимы определены до сигнала. Нельзя оптимизировать пороги на изученной истории.
Существующий locked mandate, canonical registry, PAPER/SMOKE и живые ордера не изменялись.