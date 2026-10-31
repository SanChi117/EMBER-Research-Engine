"""A243: genuine Binance USD-M BTC/ETH original Winner15m prerequisites.
Wrap original A228 SHA-authenticated real kline/mark/funding downloader.
"""
from research.a228_five_original import a228_prepare_pinned_originals_and_real_futures as base

base.COINS=("BTCUSDT","ETHUSDT")
base.PINS={
 "Winner15m":{
  "repo":"win-boom/BTCquant",
  "commit":"82c6955a15f80196d1e0ae8320b2c41432980b40",
  "path":"user_data/strategies/winner_strat.py",
  "git_blob":"585df3f6198837230816c73fe59957996f45d13a"
 }
}

if __name__=="__main__":
    base.main()
