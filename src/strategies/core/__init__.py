"""
Strategy infrastructure module.

This module contains the base classes and registry for the strategy system.
Concrete strategies should import from the parent `strategies` package.

Contents:
- BaseStrategy: Abstract base class for all strategies
- SimpleStrategy: Simplified base for combine-only strategies
- StrategyRegistry: Plugin registration and discovery
"""

from .base import BaseStrategy
from .simple import SimpleStrategy
from .registry import StrategyRegistry

__all__ = [
    "BaseStrategy",
    "SimpleStrategy",
    "StrategyRegistry",
]
