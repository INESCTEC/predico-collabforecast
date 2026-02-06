"""
Core module for the forecast engine plugin architecture.

This module provides the foundational interfaces, configuration, and
exceptions for the extensible forecast engine.

Interfaces
----------
ForecastStrategy
    Protocol for ensemble forecasting strategies
OnlineForecastStrategy
    Extended protocol for online learning strategies
FeatureTransformer
    Protocol for feature engineering transformers
Scorer
    Protocol for forecast evaluation metrics

Configuration
-------------
ForecastConfig
    Main configuration dataclass
StrategyConfig
    Per-strategy configuration
WeightingConfig
    Forecaster weight calculation settings
OnlineLearningConfig
    Online learning strategy settings
FeatureConfig
    Feature engineering settings
ModelConfig
    ML model training settings

Data Classes
------------
ForecastResult
    Container for strategy output

Example usage::

    from src.core import (
        ForecastStrategy,
        ForecastConfig,
        ForecastResult,
        ForecastEngineException,
    )

    # Create configuration
    config = ForecastConfig(
        quantiles=("q10", "q50", "q90"),
        default_strategy="weighted_avg",
    )

    # Check if a class implements ForecastStrategy
    if isinstance(my_strategy, ForecastStrategy):
        result = my_strategy.predict(X_test, config.quantiles)
"""

# Interfaces
from .interfaces import (
    FeatureTransformer,
    ForecastResult,
    ForecastStrategy,
    OnlineForecastStrategy,
    Scorer,
)

# Configuration
from .config import (
    FeatureConfig,
    ForecastConfig,
    MoEConfig,
    ModelConfig,
    OnlineLearningConfig,
    StrategyConfig,
    WeightingConfig,
)

# Exceptions
from .exceptions import (
    # Base
    ForecastEngineException,
    # Market/Session
    MarketSessionException,
    NoMarketSessionException,
    NoMarketBuyersException,
    NoMarketUsersException,
    MarketWeightsException,
    # Data
    DataException,
    # Feature Engineering
    FeatureEngineeringException,
    # Model
    ModelException,
    ModelNotFittedError,
    # Strategy
    StrategyException,
    StrategyNotFoundError,
    StrategyExecutionError,
    # Forecast
    ForecastError,
    # Scoring
    ScoringException,
    # API
    APIException,
    LoginException,
    UserException,
)

__all__ = [
    # Interfaces
    "ForecastStrategy",
    "OnlineForecastStrategy",
    "FeatureTransformer",
    "Scorer",
    "ForecastResult",
    # Configuration
    "ForecastConfig",
    "MoEConfig",
    "StrategyConfig",
    "WeightingConfig",
    "OnlineLearningConfig",
    "FeatureConfig",
    "ModelConfig",
    # Base Exceptions
    "ForecastEngineException",
    # Market/Session Exceptions
    "MarketSessionException",
    "NoMarketSessionException",
    "NoMarketBuyersException",
    "NoMarketUsersException",
    "MarketWeightsException",
    # Data Exceptions
    "DataException",
    # Feature Engineering Exceptions
    "FeatureEngineeringException",
    # Model Exceptions
    "ModelException",
    "ModelNotFittedError",
    # Strategy Exceptions
    "StrategyException",
    "StrategyNotFoundError",
    "StrategyExecutionError",
    # Forecast Exceptions
    "ForecastError",
    # Scoring Exceptions
    "ScoringException",
    # API Exceptions
    "APIException",
    "LoginException",
    "UserException",
]
