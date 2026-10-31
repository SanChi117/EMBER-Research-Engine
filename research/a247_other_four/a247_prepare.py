"""A247 pinned other four unchanged sources with genuine Binance USD-M 5m/mark/funding."""
from research.a228_five_original import a228_prepare_pinned_originals_and_real_futures as base
base.PINS={
 "momentum_wick":{"repo":"TheoBrigitte/freqtrade","commit":"c9def379b1036064d592c3a0518a07811f5a9a76",
   "path":"strategies/momentum/momentum_wick.py","git_blob":"1377a5bbf454252ca835cca3056787ac8ed73c04"},
 "momentum_rsi":{"repo":"TheoBrigitte/freqtrade","commit":"c9def379b1036064d592c3a0518a07811f5a9a76",
   "path":"strategies/momentum/momentum_rsi.py","git_blob":"3f839276f661f242a30e4dd1aa0b739459e7d65b"},
 "FSupertrendStrategy":{"repo":"freqtrade/freqtrade-strategies","commit":"f3340ce11f5bdf62f598522e64d1f5638eaa13f5",
   "path":"user_data/strategies/futures/FSupertrendStrategy.py","git_blob":"e6ec4c039a7e7759570a4df5176294f7ff19a04f"},
 "FOttStrategy":{"repo":"freqtrade/freqtrade-strategies","commit":"f3340ce11f5bdf62f598522e64d1f5638eaa13f5",
   "path":"user_data/strategies/futures/FOttStrategy.py","git_blob":"3961d9b836be4ba0427bb39a23dfe03b70d81728"},
}
if __name__=="__main__":
    base.main()
