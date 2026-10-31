"""Offline research primitives, never an order placement or live strategy engine.

All components are opt-in and return values only. The package does not open
network connections, accept exchange credentials, or place real/PAPER orders.
"""

from .registry import REGISTRY, Component, get_component

__version__ = "0.3.0"
__all__ = ["REGISTRY", "Component", "get_component"]

from .plugin import invoke, manifest, SpareInputError
__all__ += ["invoke", "manifest", "SpareInputError"]

from .bridge import normalized_candles, run_on_candles
__all__ += ["normalized_candles", "run_on_candles"]

from .binance_feed import BinanceUSDMPublic, SourceUnavailable
from .workflow import calculate_indicators, usd_m_snapshot
from .operations import SQLiteResearchLedger, bar_bracket_uncertainty
__all__ += ["BinanceUSDMPublic", "SourceUnavailable", "calculate_indicators", "usd_m_snapshot", "SQLiteResearchLedger", "bar_bracket_uncertainty"]

from .adapters import parity_from_exports, normalized_signal_rows, trade_report_rows
__all__ += ['parity_from_exports','normalized_signal_rows','trade_report_rows']

from .ready import run_binance_usdm
__all__ += ['run_binance_usdm']
