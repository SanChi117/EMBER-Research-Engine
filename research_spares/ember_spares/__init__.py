"""Offline research primitives, never an order placement or live strategy engine.

All components are opt-in and return values only. The package does not open
network connections, accept exchange credentials, or place real/PAPER orders.
"""

from .registry import REGISTRY, Component, get_component

__version__ = "0.1.0"
__all__ = ["REGISTRY", "Component", "get_component"]
