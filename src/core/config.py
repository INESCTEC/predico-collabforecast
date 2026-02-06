"""
Configuration dataclasses for the forecast engine.

This module provides typed configuration objects that replace scattered
settings throughout the codebase. Configuration can be loaded from
environment variables, config files, or passed directly.

Example usage::

    from forecast.src.core.config import ForecastConfig, StrategyConfig

    # Default configuration
    config = ForecastConfig()

    # Custom configuration
    config = ForecastConfig(
        quantiles=("q10", "q50", "q90"),
        default_strategy="weighted_avg",
        resource_strategies={"wind_resource": ["weighted_avg", "stacked_lr"]},
    )

    # Access strategy config for a resource
    strategies = config.get_strategies_for_resource("wind_resource")
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class StrategyConfig:
    """
    Configuration for a specific forecast strategy.

    :param name: Strategy name (must match registered strategy)
    :param version: Optional version constraint
    :param params: Strategy-specific parameters
    """

    name: str
    version: str | None = None
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class WeightingConfig:
    """
    Configuration for forecaster weight calculation.

    :param beta: Exponential decay parameter for weight calculation.
        Higher values give more weight to better-scoring forecasters.
        Default is 0.001 (production value).
    :param scores_calculation_days: Number of days of historical scores
        to use for weight calculation. Default is 6.
    :param min_submission_days_lookback: Lookback window for checking
        forecaster participation. Default is 7.
    :param min_submission_days: Minimum days with submissions required
        for a forecaster to be included. Default is 6.
    """

    beta: float = 0.001
    scores_calculation_days: int = 6
    min_submission_days_lookback: int = 7
    min_submission_days: int = 6

    def __post_init__(self) -> None:
        """Validate configuration values."""
        if self.min_submission_days > self.min_submission_days_lookback:
            raise ValueError(
                "min_submission_days must be less than or equal to "
                "min_submission_days_lookback."
            )


@dataclass
class FeatureConfig:
    """
    Configuration for feature engineering.

    :param add_lags: Whether to add lag features
    :param max_lags: Maximum number of lag steps
    :param forecasters_diversity: Whether to add diversity features
        (std, var, mean across forecasters)
    :param augment_with_poly: Whether to add polynomial features
    :param augment_with_roll_stats: Whether to add rolling statistics
    :param scale_features: Whether to scale features before modeling
    :param standardize: Whether to standardize (z-score) features
    :param normalize: Whether to normalize (0-1) features
    """

    add_lags: bool = True
    max_lags: int = 2
    forecasters_diversity: bool = True
    augment_with_poly: bool = True
    augment_with_roll_stats: bool = False
    scale_features: bool = True
    standardize: bool = True
    normalize: bool = False


@dataclass
class ModelConfig:
    """
    Configuration for ML model training.

    :param model_type: Model type for ensemble ("LR" or "GBR")
    :param solver: Solver for quantile regression
    :param nr_cv_splits: Number of cross-validation splits
    :param hyperparam_update_every_days: How often to re-tune hyperparameters
    :param lr_config_params: Hyperparameter grid for Linear Regression
    :param gbr_config_params: Hyperparameter grid for Gradient Boosting
    """

    model_type: str = "LR"
    solver: str = "highs"
    nr_cv_splits: int = 5
    hyperparam_update_every_days: int = 1
    lr_config_params: dict[str, list] = field(
        default_factory=lambda: {
            "alpha": [0.000001, 0.00001, 0.0001, 0.001, 0.005],
            "fit_intercept": [True, False],
        }
    )
    gbr_config_params: dict[str, list] = field(
        default_factory=lambda: {
            "learning_rate": [0.00001, 0.0001, 0.001, 0.005, 0.01],
            "max_features": [0.85, 0.95, 1.0],
            "max_depth": [3, 4],
            "max_iter": [350],
        }
    )


@dataclass
class OnlineLearningConfig:
    """
    Configuration for online learning strategies.

    These parameters control how online strategies adapt to new data
    and handle forecaster participation patterns.

    :param forgetting_factor: Exponential decay for old weights (γ).
        Value of 0.85 gives approximately 6-day effective window.
        Higher values = longer memory, slower adaptation.
    :param learning_rate: Weight update magnitude (η).
        Higher values = faster response to recent performance.
    :param cold_start_mode: How to handle new forecasters:
        - "pessimistic": Start with minimal weight, scale up over cold_start_min_days
        - "neutral": Start with average weight
        - "optimistic": Start with slightly above-average weight
    :param cold_start_min_days: Days before forecaster gets full weight.
    :param absence_mode: How to handle missing submissions:
        - "preserve": Keep last weight unchanged
        - "decay": Gradually reduce weight during absence
        - "penalty": Apply immediate penalty then decay
    :param absence_decay_rate: Daily weight decay during absence (0.98 = 2%/day).
    :param max_absence_days: Reset to cold-start after this many days absent.
    :param outlier_detection: Whether to detect outliers using DTW.
    :param outlier_alpha: MAD multiplier for outlier threshold.
    """

    # Forgetting/adaptation
    forgetting_factor: float = 0.85  # γ - effective ~6-day window
    learning_rate: float = 0.1  # η - weight update magnitude

    # Cold-start
    cold_start_mode: str = "pessimistic"  # "pessimistic", "neutral", "optimistic"
    cold_start_min_days: int = 6  # Days before full weight

    # Missing submissions
    absence_mode: str = "decay"  # "preserve", "decay", "penalty"
    absence_decay_rate: float = 0.98  # Daily decay during absence
    max_absence_days: int = 14  # Reset to cold-start after this

    # Outlier detection (reuse existing DTW detection)
    outlier_detection: bool = True
    outlier_alpha: float = 20.0

    def __post_init__(self) -> None:
        """Validate configuration values."""
        if not 0 < self.forgetting_factor <= 1:
            raise ValueError("forgetting_factor must be in (0, 1]")
        if self.learning_rate <= 0:
            raise ValueError("learning_rate must be positive")
        if self.cold_start_mode not in ("pessimistic", "neutral", "optimistic"):
            raise ValueError(
                "cold_start_mode must be 'pessimistic', 'neutral', or 'optimistic'"
            )
        if self.absence_mode not in ("preserve", "decay", "penalty"):
            raise ValueError("absence_mode must be 'preserve', 'decay', or 'penalty'")
        if not 0 < self.absence_decay_rate <= 1:
            raise ValueError("absence_decay_rate must be in (0, 1]")


@dataclass
class MoEConfig:
    """
    Configuration for Mixture of Experts ensemble strategy.

    The MoE strategy uses a gating network (MLP) to learn dynamic weights
    for combining forecaster predictions based on meta-features.

    :param hidden_size: Hidden layer size for gating MLP (default: 32)
    :param activation: Activation function for MLP (default: "relu")
    :param alpha: L2 regularization strength (default: 0.01)
    :param max_iter: Maximum training iterations (default: 500)
    :param learning_rate_init: Initial learning rate (default: 0.001)
    :param early_stopping: Whether to use early stopping (default: True)
    :param validation_fraction: Fraction of data for validation (default: 0.1)
    :param rolling_accuracy_window: Window for rolling MAE (default: 7 days)
    :param submission_rate_window: Window for submission rate (default: 30 days)
    :param imputation_window: Window for rolling mean imputation (default: 7 days)
    :param expert_change_threshold: Experts joined/left to trigger retrain (default: 2)
    :param skill_drop_threshold: Relative skill drop to trigger retrain (default: 0.1)
    :param min_retrain_interval: Minimum days between retrains (default: 7)
    :param outlier_detection: Whether to detect outliers (default: True)
    :param outlier_alpha: MAD multiplier for outlier threshold (default: 20.0)
    """

    # Gating network parameters
    hidden_size: int = 32
    activation: str = "relu"
    alpha: float = 0.01  # L2 regularization (replaces dropout)
    max_iter: int = 500
    learning_rate_init: float = 0.001
    early_stopping: bool = True
    validation_fraction: float = 0.1

    # Meta-feature windows
    rolling_accuracy_window: int = 7  # days for rolling MAE
    submission_rate_window: int = 30  # days for submission rate
    imputation_window: int = 7  # days for rolling mean imputation

    # Retraining triggers
    expert_change_threshold: int = 2  # experts joined/left
    skill_drop_threshold: float = 0.1  # relative skill drop vs baseline
    min_retrain_interval: int = 7  # min days between retrains

    # Outlier detection
    outlier_detection: bool = True
    outlier_alpha: float = 20.0

    def __post_init__(self) -> None:
        """Validate configuration values."""
        if self.hidden_size < 1:
            raise ValueError("hidden_size must be at least 1")
        if self.activation not in ("relu", "tanh", "logistic", "identity"):
            raise ValueError(
                "activation must be 'relu', 'tanh', 'logistic', or 'identity'"
            )
        if self.alpha < 0:
            raise ValueError("alpha must be non-negative")
        if not 0 < self.validation_fraction < 1:
            raise ValueError("validation_fraction must be in (0, 1)")
        if self.expert_change_threshold < 1:
            raise ValueError("expert_change_threshold must be at least 1")
        if not 0 < self.skill_drop_threshold < 1:
            raise ValueError("skill_drop_threshold must be in (0, 1)")


@dataclass
class AdaptiveSelectionConfig:
    """
    Configuration for Adaptive Selection ensemble strategy.

    This strategy dynamically selects forecasters based on predicted error
    and diversity, with K varying per hour based on an adaptive threshold.
    Selection is performed at hourly granularity (4 × 15-min samples).

    :param error_model_type: Model type for error prediction ("ridge" or "lgbm").
        Default: "ridge" (lightweight, fast).
    :param error_lookback_days: Days of historical data for computing features.
        Default: 6 (matches production).
    :param threshold_percentile: Percentile for selecting forecasters (0.0-1.0).
        0.6 means select forecasters in top 60% by predicted error.
    :param threshold_floor_multiplier: Floor = median_error × multiplier.
        Ensures minimum quality even when pool is homogeneous.
    :param min_k: Minimum forecasters to select per hour block.
    :param max_k: Maximum forecasters to select per hour block.
    :param diversity_weight: Balance between error and diversity (0.0-1.0).
        0.0 = error only, 1.0 = diversity only. Default: 0.3.
    :param min_diversity_gain: Stop greedy selection if marginal diversity
        gain falls below this threshold.
    :param hour_block_size: Samples per hour block (4 for 15-min data).
    :param outlier_detection: Whether to detect outliers using DTW.
    :param outlier_alpha: MAD multiplier for outlier threshold.
    """

    # Error prediction
    error_model_type: str = "ridge"
    error_lookback_days: int = 6

    # Threshold setting
    threshold_percentile: float = 0.6
    threshold_floor_multiplier: float = 1.5
    min_k: int = 2
    max_k: int = 10

    # Diversity parameters
    diversity_weight: float = 0.3
    min_diversity_gain: float = 0.1

    # Hour block settings
    hour_block_size: int = 4  # 4 samples per hour (15-min resolution)

    # Outlier detection
    outlier_detection: bool = True
    outlier_alpha: float = 20.0

    def __post_init__(self) -> None:
        """Validate configuration values."""
        if self.error_model_type not in ("ridge", "lgbm"):
            raise ValueError("error_model_type must be 'ridge' or 'lgbm'")
        if self.error_lookback_days < 1:
            raise ValueError("error_lookback_days must be at least 1")
        if not 0 < self.threshold_percentile <= 1:
            raise ValueError("threshold_percentile must be in (0, 1]")
        if self.threshold_floor_multiplier < 1:
            raise ValueError("threshold_floor_multiplier must be at least 1.0")
        if self.min_k < 1:
            raise ValueError("min_k must be at least 1")
        if self.max_k < self.min_k:
            raise ValueError("max_k must be >= min_k")
        if not 0 <= self.diversity_weight <= 1:
            raise ValueError("diversity_weight must be in [0, 1]")
        if self.min_diversity_gain < 0:
            raise ValueError("min_diversity_gain must be non-negative")
        if self.hour_block_size < 1:
            raise ValueError("hour_block_size must be at least 1")


@dataclass
class ForecastConfig:
    """
    Main configuration for the forecast engine.

    This dataclass consolidates all forecast engine settings into a single
    typed configuration object. It supports per-resource strategy configuration
    and provides defaults matching current production settings.

    :param quantiles: Tuple of quantile names to forecast
    :param time_resolution: Data time resolution (e.g., "15Min")
    :param forecast_horizon: Forecast horizon (e.g., "D+1" for day-ahead)
    :param default_strategy: Default strategy name for all resources
    :param resource_strategies: Dict mapping resource_id to list of strategy names.
        Allows different resources to use different strategies, or multiple
        strategies for comparison.
    :param weighting: Configuration for forecaster weight calculation
    :param features: Configuration for feature engineering
    :param model: Configuration for ML model training
    :param n_jobs: Number of parallel jobs for computation
    :param ensemble_models: List of ensemble model identifiers

    Example::

        config = ForecastConfig(
            quantiles=("q10", "q50", "q90"),
            default_strategy="weighted_avg",
            resource_strategies={
                "wind_offshore": ["weighted_avg", "stacked_lr"],
                "solar_belgium": ["weighted_avg"],
            },
        )

        # Get strategies for a resource
        strategies = config.get_strategies_for_resource("wind_offshore")
        # Returns: ["weighted_avg", "stacked_lr"]

        strategies = config.get_strategies_for_resource("unknown_resource")
        # Returns: ["weighted_avg"]  (default)
    """

    # Core forecast settings
    quantiles: tuple[str, ...] = ("q10", "q50", "q90")
    time_resolution: str = "15Min"
    forecast_horizon: str = "D+1"

    # Strategy configuration
    default_strategy: str = "weighted_avg"
    resource_strategies: dict[str, list[str]] = field(default_factory=dict)

    # Sub-configurations
    weighting: WeightingConfig = field(default_factory=WeightingConfig)
    features: FeatureConfig = field(default_factory=FeatureConfig)
    model: ModelConfig = field(default_factory=ModelConfig)

    # Runtime settings
    n_jobs: int = 1
    ensemble_models: tuple[str, ...] = ("LR", "weighted_avg")

    def get_strategies_for_resource(self, resource_id: str) -> list[str]:
        """
        Get the list of strategies to run for a specific resource.

        :param resource_id: Resource identifier

        :return: List of strategy names. Returns resource-specific strategies
            if configured, otherwise returns the default strategy.
        """
        return self.resource_strategies.get(resource_id, [self.default_strategy])

    def with_overrides(self, **kwargs: Any) -> "ForecastConfig":
        """
        Create a new config with specified overrides.

        :param kwargs: Configuration values to override

        :return: New ForecastConfig instance with overrides applied

        Example::

            base_config = ForecastConfig()
            test_config = base_config.with_overrides(n_jobs=4, default_strategy="stacked_lr")
        """
        from dataclasses import asdict

        current = asdict(self)
        current.update(kwargs)

        # Handle nested configs
        if "weighting" in kwargs and isinstance(kwargs["weighting"], dict):
            current["weighting"] = WeightingConfig(**kwargs["weighting"])
        if "features" in kwargs and isinstance(kwargs["features"], dict):
            current["features"] = FeatureConfig(**kwargs["features"])
        if "model" in kwargs and isinstance(kwargs["model"], dict):
            current["model"] = ModelConfig(**kwargs["model"])

        return ForecastConfig(**current)

    @classmethod
    def from_settings(cls) -> "ForecastConfig":
        """
        Create config from current settings.py values.

        This factory method provides backward compatibility with the existing
        settings module during migration.

        :return: ForecastConfig populated from settings.py
        """
        # Import here to avoid circular imports during transition
        from conf import settings

        return cls(
            quantiles=tuple(settings.QUANTILES),
            time_resolution=settings.MARKET_DATA_TIME_RESOLUTION,
            forecast_horizon=settings.MARKET_FORECAST_HORIZON,
            n_jobs=settings.N_JOBS,
            ensemble_models=tuple(settings.ENSEMBLE_MODELS),
            weighting=WeightingConfig(
                scores_calculation_days=settings.SCORES_CALCULATION_DAYS,
                min_submission_days_lookback=settings.MIN_SUBMISSION_DAYS_LOOKBACK,
                min_submission_days=settings.MIN_SUBMISSION_DAYS,
            ),
            # Use FeatureConfig and ModelConfig defaults
            # (previously read from settings.Stack.params, now decoupled)
            features=FeatureConfig(),
            model=ModelConfig(),
        )
