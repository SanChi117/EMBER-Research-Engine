# EMBER — Cross-symbol holdout 2026-11-01

**STATUS: EXPLORATORY CROSS-SYMBOL HOLDOUT ONLY. NOT NATIVE P06/P07. NOT VERIFIED.**
After examining the first six symbols, a prospective diagnostic was frozen for additional unseen symbol identities: does the already-defined ex-ante UP/DOWN regime (absolute trendScore>1) distinguish fakeout outcomes? This is not an untouched time OOS because the dates overlap, and the subgroup was selected after looking at the original six pairs.
No threshold, lookback, TP/SL horizon, ambiguity rule or fee model changed. Exact `analyze()` function identical to first experiment. Original first pass methodology and WARNINGS remain authoritative; do not optimize on these outcomes.

## Predeclared 5 new symbol names
BNBUSDT, XRPUSDT, LINKUSDT (stronger liquid comparators), OPUSDT, ARBUSDT (alt comparators). USD-M futures 4h, 2024-02-16 to 2026-10-31 UTC.
Historical data are five holdout_data/*.csv stored as immutable Git blob SHA, with event-level result in holdout_events.csv and executable holdout_reproduce.js.

## Quality and holdout results (indicative notional %; baseline costs 0.20%, stress costs 0.35%)
```json
{
  "quality": {
    "BNBUSDT": {
      "bars": 5934,
      "first": 1708041600000,
      "last": 1793476800000,
      "gaps": 0,
      "invalid": 0,
      "blob": "aa9494a30ef87cfbc9f4eee7bff03bda50707985"
    },
    "XRPUSDT": {
      "bars": 5934,
      "first": 1708041600000,
      "last": 1793476800000,
      "gaps": 0,
      "invalid": 0,
      "blob": "8fcb2c3509a585fd53107d14f104dd84bf20d6e9"
    },
    "LINKUSDT": {
      "bars": 5934,
      "first": 1708041600000,
      "last": 1793476800000,
      "gaps": 0,
      "invalid": 0,
      "blob": "87784bac63543f924faf00f2f8e87b94f7a800bb"
    },
    "OPUSDT": {
      "bars": 5934,
      "first": 1708041600000,
      "last": 1793476800000,
      "gaps": 0,
      "invalid": 0,
      "blob": "e6c3ce4505711103f731ba2bf0d4435026416091"
    },
    "ARBUSDT": {
      "bars": 5934,
      "first": 1708041600000,
      "last": 1793476800000,
      "gaps": 0,
      "invalid": 0,
      "blob": "0e70e28bf1de694578cc47def1116740b0afa4d0"
    }
  },
  "groups": {
    "fake": {
      "all": {
        "n": 1229,
        "win": 556,
        "loss": 638,
        "amb": 11,
        "timeout": 24,
        "winPctResolved": 46.57,
        "wilson95": [
          43.8,
          49.4
        ],
        "meanGrossPct": -0.163,
        "meanBasePct": -0.363,
        "meanStressPct": -0.513
      },
      "strong": {
        "n": 136,
        "win": 69,
        "loss": 63,
        "amb": 2,
        "timeout": 2,
        "winPctResolved": 52.27,
        "wilson95": [
          43.8,
          60.6
        ],
        "meanGrossPct": 0.0702,
        "meanBasePct": -0.1298,
        "meanStressPct": -0.2798
      },
      "side": {
        "n": 1093,
        "win": 487,
        "loss": 575,
        "amb": 9,
        "timeout": 22,
        "winPctResolved": 45.86,
        "wilson95": [
          42.9,
          48.9
        ],
        "meanGrossPct": -0.1921,
        "meanBasePct": -0.3921,
        "meanStressPct": -0.5421
      },
      "strongEarly": {
        "n": 64,
        "win": 33,
        "loss": 28,
        "amb": 2,
        "timeout": 1,
        "winPctResolved": 54.1,
        "wilson95": [
          41.7,
          66
        ],
        "meanGrossPct": 0.151,
        "meanBasePct": -0.049,
        "meanStressPct": -0.199
      },
      "strongLate": {
        "n": 72,
        "win": 36,
        "loss": 35,
        "amb": 0,
        "timeout": 1,
        "winPctResolved": 50.7,
        "wilson95": [
          39.3,
          62
        ],
        "meanGrossPct": -0.0017,
        "meanBasePct": -0.2017,
        "meanStressPct": -0.3517
      },
      "strongFollowTrend": {
        "n": 36,
        "win": 16,
        "loss": 19,
        "amb": 0,
        "timeout": 1,
        "winPctResolved": 45.71,
        "wilson95": [
          30.5,
          61.8
        ],
        "meanGrossPct": -0.2094,
        "meanBasePct": -0.4094,
        "meanStressPct": -0.5594
      },
      "strongAgainstTrend": {
        "n": 100,
        "win": 53,
        "loss": 44,
        "amb": 2,
        "timeout": 1,
        "winPctResolved": 54.64,
        "wilson95": [
          44.7,
          64.2
        ],
        "meanGrossPct": 0.1709,
        "meanBasePct": -0.0291,
        "meanStressPct": -0.1791
      },
      "strongBySymbol": {
        "BNBUSDT": {
          "n": 21,
          "win": 11,
          "loss": 9,
          "amb": 1,
          "timeout": 0,
          "winPctResolved": 55,
          "wilson95": [
            34.2,
            74.2
          ],
          "meanGrossPct": 0.2826,
          "meanBasePct": 0.0826,
          "meanStressPct": -0.0674
        },
        "XRPUSDT": {
          "n": 23,
          "win": 12,
          "loss": 11,
          "amb": 0,
          "timeout": 0,
          "winPctResolved": 52.17,
          "wilson95": [
            33,
            70.8
          ],
          "meanGrossPct": 0.2798,
          "meanBasePct": 0.0798,
          "meanStressPct": -0.0702
        },
        "LINKUSDT": {
          "n": 27,
          "win": 15,
          "loss": 11,
          "amb": 1,
          "timeout": 0,
          "winPctResolved": 57.69,
          "wilson95": [
            38.9,
            74.5
          ],
          "meanGrossPct": 0.0788,
          "meanBasePct": -0.1212,
          "meanStressPct": -0.2712
        },
        "OPUSDT": {
          "n": 29,
          "win": 18,
          "loss": 11,
          "amb": 0,
          "timeout": 0,
          "winPctResolved": 62.07,
          "wilson95": [
            44,
            77.3
          ],
          "meanGrossPct": 0.4932,
          "meanBasePct": 0.2932,
          "meanStressPct": 0.1432
        },
        "ARBUSDT": {
          "n": 36,
          "win": 13,
          "loss": 21,
          "amb": 0,
          "timeout": 2,
          "winPctResolved": 38.24,
          "wilson95": [
            23.9,
            55
          ],
          "meanGrossPct": -0.5348,
          "meanBasePct": -0.7348,
          "meanStressPct": -0.8848
        }
      },
      "bySymbol": {
        "BNBUSDT": {
          "n": 238,
          "win": 103,
          "loss": 131,
          "amb": 3,
          "timeout": 1,
          "winPctResolved": 44.02,
          "wilson95": [
            37.8,
            50.4
          ],
          "meanGrossPct": -0.111,
          "meanBasePct": -0.311,
          "meanStressPct": -0.461
        },
        "XRPUSDT": {
          "n": 226,
          "win": 108,
          "loss": 112,
          "amb": 2,
          "timeout": 4,
          "winPctResolved": 49.09,
          "wilson95": [
            42.6,
            55.7
          ],
          "meanGrossPct": -0.0461,
          "meanBasePct": -0.2461,
          "meanStressPct": -0.3961
        },
        "LINKUSDT": {
          "n": 263,
          "win": 127,
          "loss": 126,
          "amb": 4,
          "timeout": 6,
          "winPctResolved": 50.2,
          "wilson95": [
            44.1,
            56.3
          ],
          "meanGrossPct": -0.0173,
          "meanBasePct": -0.2173,
          "meanStressPct": -0.3673
        },
        "OPUSDT": {
          "n": 261,
          "win": 122,
          "loss": 135,
          "amb": 0,
          "timeout": 4,
          "winPctResolved": 47.47,
          "wilson95": [
            41.4,
            53.6
          ],
          "meanGrossPct": -0.1982,
          "meanBasePct": -0.3982,
          "meanStressPct": -0.5482
        },
        "ARBUSDT": {
          "n": 241,
          "win": 96,
          "loss": 134,
          "amb": 2,
          "timeout": 9,
          "winPctResolved": 41.74,
          "wilson95": [
            35.6,
            48.2
          ],
          "meanGrossPct": -0.445,
          "meanBasePct": -0.645,
          "meanStressPct": -0.795
        }
      }
    },
    "true": {
      "all": {
        "n": 1204,
        "win": 635,
        "loss": 521,
        "amb": 33,
        "timeout": 15,
        "winPctResolved": 54.93,
        "wilson95": [
          52.1,
          57.8
        ],
        "meanGrossPct": 0.1345,
        "meanBasePct": -0.0655,
        "meanStressPct": -0.2155
      },
      "strong": {
        "n": 132,
        "win": 69,
        "loss": 59,
        "amb": 3,
        "timeout": 1,
        "winPctResolved": 53.91,
        "wilson95": [
          45.3,
          62.3
        ],
        "meanGrossPct": 0.0818,
        "meanBasePct": -0.1182,
        "meanStressPct": -0.2682
      },
      "side": {
        "n": 1072,
        "win": 566,
        "loss": 462,
        "amb": 30,
        "timeout": 14,
        "winPctResolved": 55.06,
        "wilson95": [
          52,
          58.1
        ],
        "meanGrossPct": 0.141,
        "meanBasePct": -0.059,
        "meanStressPct": -0.209
      },
      "strongEarly": {
        "n": 52,
        "win": 32,
        "loss": 18,
        "amb": 1,
        "timeout": 1,
        "winPctResolved": 64,
        "wilson95": [
          50.1,
          75.9
        ],
        "meanGrossPct": 0.5826,
        "meanBasePct": 0.3826,
        "meanStressPct": 0.2326
      },
      "strongLate": {
        "n": 80,
        "win": 37,
        "loss": 41,
        "amb": 2,
        "timeout": 0,
        "winPctResolved": 47.44,
        "wilson95": [
          36.7,
          58.4
        ],
        "meanGrossPct": -0.2437,
        "meanBasePct": -0.4437,
        "meanStressPct": -0.5937
      },
      "strongFollowTrend": {
        "n": 82,
        "win": 40,
        "loss": 40,
        "amb": 2,
        "timeout": 0,
        "winPctResolved": 50,
        "wilson95": [
          39.3,
          60.7
        ],
        "meanGrossPct": -0.101,
        "meanBasePct": -0.301,
        "meanStressPct": -0.451
      },
      "strongAgainstTrend": {
        "n": 50,
        "win": 29,
        "loss": 19,
        "amb": 1,
        "timeout": 1,
        "winPctResolved": 60.42,
        "wilson95": [
          46.3,
          73
        ],
        "meanGrossPct": 0.3816,
        "meanBasePct": 0.1816,
        "meanStressPct": 0.0316
      },
      "strongBySymbol": {
        "BNBUSDT": {
          "n": 19,
          "win": 12,
          "loss": 7,
          "amb": 0,
          "timeout": 0,
          "winPctResolved": 63.16,
          "wilson95": [
            41,
            80.9
          ],
          "meanGrossPct": 0.2957,
          "meanBasePct": 0.0957,
          "meanStressPct": -0.0543
        },
        "XRPUSDT": {
          "n": 21,
          "win": 12,
          "loss": 9,
          "amb": 0,
          "timeout": 0,
          "winPctResolved": 57.14,
          "wilson95": [
            36.5,
            75.5
          ],
          "meanGrossPct": 0.4513,
          "meanBasePct": 0.2513,
          "meanStressPct": 0.1013
        },
        "LINKUSDT": {
          "n": 28,
          "win": 13,
          "loss": 13,
          "amb": 2,
          "timeout": 0,
          "winPctResolved": 50,
          "wilson95": [
            32.1,
            67.9
          ],
          "meanGrossPct": 0.0128,
          "meanBasePct": -0.1872,
          "meanStressPct": -0.3372
        },
        "OPUSDT": {
          "n": 29,
          "win": 15,
          "loss": 13,
          "amb": 1,
          "timeout": 0,
          "winPctResolved": 53.57,
          "wilson95": [
            35.8,
            70.5
          ],
          "meanGrossPct": 0.019,
          "meanBasePct": -0.181,
          "meanStressPct": -0.331
        },
        "ARBUSDT": {
          "n": 35,
          "win": 17,
          "loss": 17,
          "amb": 0,
          "timeout": 1,
          "winPctResolved": 50,
          "wilson95": [
            34.1,
            65.9
          ],
          "meanGrossPct": -0.1489,
          "meanBasePct": -0.3489,
          "meanStressPct": -0.4989
        }
      },
      "bySymbol": {
        "BNBUSDT": {
          "n": 237,
          "win": 127,
          "loss": 101,
          "amb": 7,
          "timeout": 2,
          "winPctResolved": 55.7,
          "wilson95": [
            49.2,
            62
          ],
          "meanGrossPct": 0.1216,
          "meanBasePct": -0.0784,
          "meanStressPct": -0.2284
        },
        "XRPUSDT": {
          "n": 228,
          "win": 121,
          "loss": 95,
          "amb": 10,
          "timeout": 2,
          "winPctResolved": 56.02,
          "wilson95": [
            49.4,
            62.5
          ],
          "meanGrossPct": 0.253,
          "meanBasePct": 0.053,
          "meanStressPct": -0.097
        },
        "LINKUSDT": {
          "n": 255,
          "win": 130,
          "loss": 116,
          "amb": 8,
          "timeout": 1,
          "winPctResolved": 52.85,
          "wilson95": [
            46.6,
            59
          ],
          "meanGrossPct": 0.0403,
          "meanBasePct": -0.1597,
          "meanStressPct": -0.3097
        },
        "OPUSDT": {
          "n": 245,
          "win": 131,
          "loss": 105,
          "amb": 6,
          "timeout": 3,
          "winPctResolved": 55.51,
          "wilson95": [
            49.1,
            61.7
          ],
          "meanGrossPct": 0.0908,
          "meanBasePct": -0.1092,
          "meanStressPct": -0.2592
        },
        "ARBUSDT": {
          "n": 239,
          "win": 126,
          "loss": 104,
          "amb": 2,
          "timeout": 7,
          "winPctResolved": 54.78,
          "wilson95": [
            48.3,
            61.1
          ],
          "meanGrossPct": 0.1798,
          "meanBasePct": -0.0202,
          "meanStressPct": -0.1702
        }
      }
    },
    "near": {
      "all": {
        "n": 1042,
        "win": 481,
        "loss": 537,
        "amb": 7,
        "timeout": 17,
        "winPctResolved": 47.25,
        "wilson95": [
          44.2,
          50.3
        ],
        "meanGrossPct": -0.109,
        "meanBasePct": -0.309,
        "meanStressPct": -0.459
      },
      "strong": {
        "n": 113,
        "win": 51,
        "loss": 61,
        "amb": 1,
        "timeout": 0,
        "winPctResolved": 45.54,
        "wilson95": [
          36.6,
          54.8
        ],
        "meanGrossPct": -0.2138,
        "meanBasePct": -0.4138,
        "meanStressPct": -0.5638
      },
      "side": {
        "n": 929,
        "win": 430,
        "loss": 476,
        "amb": 6,
        "timeout": 17,
        "winPctResolved": 47.46,
        "wilson95": [
          44.2,
          50.7
        ],
        "meanGrossPct": -0.0963,
        "meanBasePct": -0.2963,
        "meanStressPct": -0.4463
      },
      "strongEarly": {
        "n": 48,
        "win": 25,
        "loss": 22,
        "amb": 1,
        "timeout": 0,
        "winPctResolved": 53.19,
        "wilson95": [
          39.2,
          66.7
        ],
        "meanGrossPct": 0.3828,
        "meanBasePct": 0.1828,
        "meanStressPct": 0.0328
      },
      "strongLate": {
        "n": 65,
        "win": 26,
        "loss": 39,
        "amb": 0,
        "timeout": 0,
        "winPctResolved": 40,
        "wilson95": [
          29,
          52.1
        ],
        "meanGrossPct": -0.6543,
        "meanBasePct": -0.8543,
        "meanStressPct": -1.0043
      },
      "strongFollowTrend": {
        "n": 29,
        "win": 15,
        "loss": 14,
        "amb": 0,
        "timeout": 0,
        "winPctResolved": 51.72,
        "wilson95": [
          34.4,
          68.6
        ],
        "meanGrossPct": -0.1362,
        "meanBasePct": -0.3362,
        "meanStressPct": -0.4862
      },
      "strongAgainstTrend": {
        "n": 84,
        "win": 36,
        "loss": 47,
        "amb": 1,
        "timeout": 0,
        "winPctResolved": 43.37,
        "wilson95": [
          33.2,
          54.1
        ],
        "meanGrossPct": -0.2406,
        "meanBasePct": -0.4406,
        "meanStressPct": -0.5906
      },
      "strongBySymbol": {
        "BNBUSDT": {
          "n": 14,
          "win": 6,
          "loss": 8,
          "amb": 0,
          "timeout": 0,
          "winPctResolved": 42.86,
          "wilson95": [
            21.4,
            67.4
          ],
          "meanGrossPct": -0.355,
          "meanBasePct": -0.555,
          "meanStressPct": -0.705
        },
        "XRPUSDT": {
          "n": 18,
          "win": 6,
          "loss": 11,
          "amb": 1,
          "timeout": 0,
          "winPctResolved": 35.29,
          "wilson95": [
            17.3,
            58.7
          ],
          "meanGrossPct": -0.8884,
          "meanBasePct": -1.0884,
          "meanStressPct": -1.2384
        },
        "LINKUSDT": {
          "n": 23,
          "win": 14,
          "loss": 9,
          "amb": 0,
          "timeout": 0,
          "winPctResolved": 60.87,
          "wilson95": [
            40.8,
            77.8
          ],
          "meanGrossPct": 0.7756,
          "meanBasePct": 0.5756,
          "meanStressPct": 0.4256
        },
        "OPUSDT": {
          "n": 31,
          "win": 17,
          "loss": 14,
          "amb": 0,
          "timeout": 0,
          "winPctResolved": 54.84,
          "wilson95": [
            37.8,
            70.8
          ],
          "meanGrossPct": 0.2651,
          "meanBasePct": 0.0651,
          "meanStressPct": -0.0849
        },
        "ARBUSDT": {
          "n": 27,
          "win": 8,
          "loss": 19,
          "amb": 0,
          "timeout": 0,
          "winPctResolved": 29.63,
          "wilson95": [
            15.9,
            48.5
          ],
          "meanGrossPct": -1.0834,
          "meanBasePct": -1.2834,
          "meanStressPct": -1.4334
        }
      },
      "bySymbol": {
        "BNBUSDT": {
          "n": 194,
          "win": 98,
          "loss": 94,
          "amb": 0,
          "timeout": 2,
          "winPctResolved": 51.04,
          "wilson95": [
            44,
            58
          ],
          "meanGrossPct": 0.0766,
          "meanBasePct": -0.1234,
          "meanStressPct": -0.2734
        },
        "XRPUSDT": {
          "n": 182,
          "win": 89,
          "loss": 81,
          "amb": 5,
          "timeout": 7,
          "winPctResolved": 52.35,
          "wilson95": [
            44.9,
            59.7
          ],
          "meanGrossPct": 0.0751,
          "meanBasePct": -0.1249,
          "meanStressPct": -0.2749
        },
        "LINKUSDT": {
          "n": 225,
          "win": 96,
          "loss": 124,
          "amb": 1,
          "timeout": 4,
          "winPctResolved": 43.64,
          "wilson95": [
            37.2,
            50.2
          ],
          "meanGrossPct": -0.2118,
          "meanBasePct": -0.4118,
          "meanStressPct": -0.5618
        },
        "OPUSDT": {
          "n": 219,
          "win": 102,
          "loss": 114,
          "amb": 1,
          "timeout": 2,
          "winPctResolved": 47.22,
          "wilson95": [
            40.7,
            53.9
          ],
          "meanGrossPct": -0.1012,
          "meanBasePct": -0.3012,
          "meanStressPct": -0.4512
        },
        "ARBUSDT": {
          "n": 222,
          "win": 96,
          "loss": 124,
          "amb": 0,
          "timeout": 2,
          "winPctResolved": 43.64,
          "wilson95": [
            37.2,
            50.2
          ],
          "meanGrossPct": -0.3256,
          "meanBasePct": -0.5256,
          "meanStressPct": -0.6756
        }
      }
    }
  }
}
```

## Required conclusions/limits
Interpret stronger UP/DOWN conditional results strictly as exploratory until untouched future data and native executable original confirm. Same calendar interval across correlated contracts is not independent regime/OOS validation. Same 4h ambiguity pessimism, no funding, mark, slippage, gaps/liquidation, account-level DD or full realistic fills. Report all five symbols, both directions, both time periods. Failure in holdout may reject the conditional clue but cannot prove every false-breakout strategy negative.
No changes to canonical active strategy status (still 0 VERIFIED), user locked mandate, main EMBER, live, PAPER, Google Drive or scheduler.