"""H1 timestamp and two-leg bid/ask provenance negative tests (no trades)."""
import unittest
from decimal import Decimal as D
from types import SimpleNamespace

from research.platform import basis_source as b
from research.platform.market_contract import DataUntrusted

SETTLE=1759392000013
T=1760000040000
H4=14400000


def books():
    spot=b.TopBook("BTCUSDT","BINANCE","SPOT",D("100"),D("100.1"),T)
    perp=b.TopBook("BTCUSDT","BINANCE","PERP_USDM",D("100.2"),D("100.3"),T)
    return spot,perp


class SourceBasisNegative(unittest.TestCase):
    def test_actual_irregular_settlement_milliseconds_valid(self):
        r=b.FundingSettlement("BTCUSDT",SETTLE,SETTLE+1,D("0.0001"))
        self.assertEqual(r.settlement_ms%H4,13)
    def test_future_settlement_cannot_be_known(self):
        with self.assertRaisesRegex(DataUntrusted,"BEFORE_SETTLEMENT"):
            b.FundingSettlement("BTCUSDT",SETTLE,SETTLE-1,D("0.0001"))
    def test_realized_future_funding_excluded_from_history_asof(self):
        first=b.FundingSettlement("BTCUSDT",SETTLE,SETTLE,D("0.0001"))
        future=b.FundingSettlement("BTCUSDT",SETTLE+28800000,
                                   SETTLE+28801000,D("0.0002"))
        self.assertEqual(b.settled_funding_asof([first,future],SETTLE+1),(first,))
    def test_executable_basis_bid_perp_over_ask_spot(self):
        spot,perp=books()
        value=b.executable_spot_long_perp_short_basis(spot,perp,decision_at_ms=T+1)
        self.assertEqual(value,D("100.2")/D("100.1")-1)
        self.assertLess(value,D("100.3")/D("100")-1)
    def test_stale_second_leg_rejected(self):
        spot,perp=books()
        with self.assertRaisesRegex(DataUntrusted,"STALE_OR_FUTURE_LEG"):
            b.executable_spot_long_perp_short_basis(
                spot,perp,decision_at_ms=T+15001)
    def test_cross_venue_and_kind_rejected(self):
        spot,perp=books()
        bad=b.TopBook("BTCUSDT","BYBIT","PERP_USDM",D("100.2"),D("100.3"),T)
        with self.assertRaisesRegex(DataUntrusted,"IDENTITY_MISMATCH"):
            b.executable_spot_long_perp_short_basis(spot,bad,decision_at_ms=T)
        with self.assertRaisesRegex(DataUntrusted,"IDENTITY_MISMATCH"):
            b.executable_spot_long_perp_short_basis(perp,spot,decision_at_ms=T)
    def test_crossed_book_and_nonfinite_rejected(self):
        with self.assertRaisesRegex(DataUntrusted,"CROSSED"):
            b.TopBook("BTCUSDT","BINANCE","SPOT",D("101"),D("100"),T)
        with self.assertRaisesRegex(DataUntrusted,"NONFINITE"):
            b.TopBook("BTCUSDT","BINANCE","SPOT",D("NaN"),D("101"),T)
    def test_inclusive_exchange_end_is_not_test_window(self):
        start=1759276800000
        end=start+12*H4
        rows=[SimpleNamespace(open_ms=start+i*H4) for i in range(13)]
        trimmed=b.half_open_bars(rows,start,end)
        self.assertEqual(len(trimmed),12)
        self.assertEqual(trimmed[-1].open_ms,start+11*H4)
    def test_future_quote_rejected(self):
        spot,perp=books()
        with self.assertRaisesRegex(DataUntrusted,"STALE_OR_FUTURE_LEG"):
            b.executable_spot_long_perp_short_basis(
                spot,perp,decision_at_ms=T-1)


if __name__=="__main__":
    unittest.main()
