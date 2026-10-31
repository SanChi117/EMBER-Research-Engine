"""A245 verify exact original sources, then reuse A228 authentic Binance USD-M archives and validations."""
from research.a228_five_original import a228_prepare_pinned_originals_and_real_futures as base

base.PINS={
 "MTF_Hybrid":{"repo":"win-boom/BTCquant","commit":"82c6955a15f80196d1e0ae8320b2c41432980b40",
               "path":"user_data/strategies/mtf_hybrid_strategy.py","git_blob":"92a23a6d8fe5ea5e0314183c9deecc87d3bfeec6"},
 "FailureToReturnStrategy":{"repo":"hrodrig/freqhub-strategies","commit":"210952246ae457a5f6d5e089ddea8b4960a71775",
               "path":"strategies/FreqHub.Strategy.FailureToReturn/FailureToReturnStrategy.py","git_blob":"6e80c0b96754c21744726120b6904f940621ec01"},
 "FVGChannel":{"repo":"jaredrsommer/freqtradestrategies","commit":"9d66f71ce21f2f65feaad6bb967215be22a3cfd6",
               "path":"FVGChannel.py","git_blob":"e9f94dd1fd06dea9de68e7ea86ca12d13a4283ce"},
 "VolatilitySystem":{"repo":"freqtrade/freqtrade-strategies","commit":"f3340ce11f5bdf62f598522e64d1f5638eaa13f5",
               "path":"user_data/strategies/futures/VolatilitySystem.py","git_blob":"15ce2473f3f60bd33c4a67b0b8b228e379850f19"},
 "FAdxSmaStrategy":{"repo":"freqtrade/freqtrade-strategies","commit":"f3340ce11f5bdf62f598522e64d1f5638eaa13f5",
               "path":"user_data/strategies/futures/FAdxSmaStrategy.py","git_blob":"3bb13caf079e8360a959c3ad4dd2b2507f3045c0"},
 "FReinforcedStrategy":{"repo":"freqtrade/freqtrade-strategies","commit":"f3340ce11f5bdf62f598522e64d1f5638eaa13f5",
               "path":"user_data/strategies/futures/FReinforcedStrategy.py","git_blob":"11bfdde9fcecf772a2d223c88b9ee62bfd8737d3"}
}
if __name__=="__main__":
    base.main()
