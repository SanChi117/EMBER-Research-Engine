import unittest
from datetime import datetime, timezone
from ember_spares.bridge import normalized_candles,run_on_candles
from ember_spares.plugin import SpareInputError

class DummyPolars:
  def __init__(self,rows): self.rows=rows
  def to_dicts(self):return self.rows

class DummyLazyPolars:
  def __init__(self,rows): self.rows=rows
  def collect(self):return DummyPolars(self.rows)

class DummyPandas:
  def __init__(self,rows): self.rows=rows
  def to_dict(self,orient):
    assert orient=='records'
    return self.rows

class BridgeTests(unittest.TestCase):
  def rows(self):
    return [dict(timestamp=100+i*60,open=100.,high=105.,low=95.,close=102.,volume=100.) for i in range(10)]

  def test_polars_pandas_lists(self):
    rows=self.rows()
    for frame in [rows,DummyPolars(rows),DummyLazyPolars(rows),DummyPandas(rows)]:
      candles=normalized_candles(frame,timeframe_seconds=60)
      self.assertEqual(len(candles),10)
      self.assertEqual(candles[0]['available_at'],160)
      result=run_on_candles('Z16',frame,timeframe_seconds=60,decision_at=1000)
      self.assertEqual(result['bull_count'],0)

  def test_utc_datetime(self):
    t=datetime(2026,11,1,tzinfo=timezone.utc)
    r=[dict(timestamp=t,open=100,high=101,low=99,close=100,volume=1)]
    self.assertEqual(len(normalized_candles(r,timeframe_seconds=60)),1)
    with self.assertRaises(SpareInputError):
      normalized_candles([{**r[0],'timestamp':t.replace(tzinfo=None)}],timeframe_seconds=60)

  def test_multi_asset_isolation(self):
    rows=[dict(r,symbol='BTC') for r in self.rows()]+[dict(r,symbol='ETH') for r in self.rows()]
    with self.assertRaises(SpareInputError): normalized_candles(rows,timeframe_seconds=60)
    self.assertEqual(len(normalized_candles(rows,timeframe_seconds=60,symbol='BTC')),10)
    with self.assertRaises(SpareInputError):normalized_candles(rows,timeframe_seconds=60,symbol='SOL')

  def test_future_refused(self):
    with self.assertRaises(SpareInputError):
      run_on_candles('Z16',self.rows(),timeframe_seconds=60,decision_at=150)
    with self.assertRaises(SpareInputError):
      normalized_candles(self.rows())
    with self.assertRaises(SpareInputError):
      normalized_candles(self.rows()*2,timeframe_seconds=60)

if __name__=='__main__':unittest.main()
