"""
Consolidated exceptions for the forecast engine.

This module provides a hierarchy of custom exceptions used throughout
the forecast engine. Exceptions are organized by category:

- Base exceptions
- Market/session exceptions
- Data exceptions
- Model exceptions
- Strategy exceptions
"""


# =============================================================================
# Base Exceptions
# =============================================================================


class ForecastEngineException(Exception):
    """
    Base exception for all forecast engine errors.

    All custom exceptions in the forecast engine inherit from this class,
    allowing callers to catch all forecast-related exceptions with a single
    except clause.

    :param message: Human-readable error description
    :param errors: Optional dict or list with additional error details
    """

    def __init__(self, message: str, errors: dict | list | None = None):
        super().__init__(message)
        self.errors = errors


# =============================================================================
# Market/Session Exceptions
# =============================================================================


class MarketSessionException(ForecastEngineException):
    """Raised when a market session operation fails."""

    pass


class NoMarketSessionException(ForecastEngineException):
    """Raised when no market session is available for the requested operation."""

    pass


class NoMarketBuyersException(ForecastEngineException):
    """Raised when no buyers are found for a market session."""

    pass


class NoMarketUsersException(ForecastEngineException):
    """Raised when no users are found for a market session."""

    pass


class MarketWeightsException(ForecastEngineException):
    """Raised when weight calculation for market participants fails."""

    pass


# =============================================================================
# Data Exceptions
# =============================================================================


class DataException(ForecastEngineException):
    """Base exception for data-related errors."""

    pass


# =============================================================================
# Feature Engineering Exceptions
# =============================================================================


class FeatureEngineeringException(ForecastEngineException):
    """Base exception for feature engineering errors."""

    pass


# =============================================================================
# Model Exceptions
# =============================================================================


class ModelException(ForecastEngineException):
    """Base exception for model-related errors."""

    pass


class ModelNotFittedError(ModelException):
    """Raised when predict is called on an unfitted model."""

    pass


# =============================================================================
# Strategy Exceptions
# =============================================================================


class StrategyException(ForecastEngineException):
    """Base exception for strategy-related errors."""

    pass


class StrategyNotFoundError(StrategyException):
    """Raised when a requested strategy is not found in the registry."""

    pass


class StrategyExecutionError(StrategyException):
    """Raised when strategy execution fails."""

    pass


# =============================================================================
# Forecast Exceptions
# =============================================================================


class ForecastError(ForecastEngineException):
    """Raised when forecast generation fails."""

    pass


# =============================================================================
# Scoring Exceptions
# =============================================================================


class ScoringException(ForecastEngineException):
    """Base exception for scoring-related errors."""

    pass


# =============================================================================
# API Exceptions (for API client interactions)
# =============================================================================


class APIException(ForecastEngineException):
    """Base exception for API-related errors."""

    pass


class LoginException(APIException):
    """Raised when API login fails."""

    pass


class UserException(APIException):
    """Raised when user-related API operation fails."""

    pass
