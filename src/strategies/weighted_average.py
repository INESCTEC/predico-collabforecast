"""
Weighted average ensemble strategy.

This is the **production ensemble** strategy used in the Predico platform.
It combines forecaster predictions using exponentially-weighted averaging
based on recent skill scores.

The strategy:
1. Uses recent RMSE (for q50) or Pinball loss (for q10/q90) scores as weights
2. Applies exponential transformation: weight = exp(-beta * score)
3. Optionally detects and removes outlier forecast profiles using DTW
4. Calculates weighted average of remaining forecaster predictions

Example usage::

    from src.strategies import WeightedAverageStrategy

    strategy = WeightedAverageStrategy(beta=0.001, outlier_detection=True)
    strategy.fit(X_train, y_train, ["q10", "q50", "q90"], scores=assessment_scores)
    predictions = strategy.predict(X_test, ["q10", "q50", "q90"])
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from loguru import logger

from .core import BaseStrategy, StrategyRegistry
from .utils import detect_outliers_dtw
from ..assessment.score_calculator import compute_scores


@StrategyRegistry.register("weighted_avg")
class WeightedAverageStrategy(BaseStrategy):
    """
    Weighted average ensemble strategy (production ensemble).

    This strategy combines forecaster predictions using exponentially-weighted
    averaging based on recent skill scores. It is the default production
    ensemble used in the Predico platform.

    Weight calculation:
        weight_i = exp(-beta * score_i) / sum(exp(-beta * score_j))

    Where:
        - score_i is the recent skill score for forecaster i
        - beta controls the weight decay (default: 0.001)
        - Lower scores (better performance) result in higher weights

    :param beta: Exponential decay parameter for weight calculation.
        Higher values give more weight to better-scoring forecasters.
        Default is 0.001.
    :param outlier_detection: Whether to detect and remove outlier profiles
        using DTW distance before ensemble. Default is True.
    :param outlier_alpha: MAD multiplier for outlier threshold.
        Higher values result in fewer outliers detected. Default is 20.0.
    :param min_forecasters_for_outlier_detection: Minimum number of forecasters
        required to run outlier detection. Default is 4.
    :param default_score: Score assigned to forecasters without historical scores.
        Default is 999999 (effectively zero weight).

    Example::

        strategy = WeightedAverageStrategy(beta=0.001)

        # Fit with assessment scores
        strategy.fit(
            X_train, y_train,
            quantiles=["q10", "q50", "q90"],
            scores={
                "q50": {"user_1": {"recent_score": 0.05}, ...},
                "q10": {...},
                "q90": {...}
            }
        )

        # Generate predictions
        predictions = strategy.predict(X_test, ["q10", "q50", "q90"])
    """

    def __init__(
        self,
        beta: float = 0.001,
        outlier_detection: bool = True,
        outlier_alpha: float = 20.0,
        min_forecasters_for_outlier_detection: int = 4,
        default_score: float = 999999.0,
        n_score_days: int = 6,
    ):
        """
        Initialize the weighted average strategy.

        :param beta: Exponential decay parameter (default: 0.001)
        :param outlier_detection: Enable outlier detection (default: True)
        :param outlier_alpha: MAD multiplier for outliers (default: 20.0)
        :param min_forecasters_for_outlier_detection: Min forecasters for
            outlier detection (default: 4)
        :param default_score: Score for unknown forecasters (default: 999999)
        :param n_score_days: Number of days for score calculation (default: 6)
        """
        super().__init__(
            beta=beta,
            outlier_detection=outlier_detection,
            outlier_alpha=outlier_alpha,
            min_forecasters_for_outlier_detection=min_forecasters_for_outlier_detection,
            default_score=default_score,
            n_score_days=n_score_days,
        )
        self._beta = beta
        self._outlier_detection = outlier_detection
        self._outlier_alpha = outlier_alpha
        self._min_forecasters = min_forecasters_for_outlier_detection
        self._default_score = default_score
        self._n_score_days = n_score_days
        self._scores: dict[str, dict[str, float]] = {}

    @property
    def name(self) -> str:
        """Return strategy name."""
        return "weighted_avg"

    def _do_fit(
        self,
        X_train: pd.DataFrame,
        y_train: pd.DataFrame,
        quantiles: list[str],
        **kwargs: Any,
    ) -> None:
        """
        Fit the weighted average strategy.

        Computes skill scores from training data for weight calculation.

        :param X_train: Historical forecaster predictions
        :param y_train: Historical actual values with 'target' column
        :param quantiles: List of quantile names
        :param kwargs: Additional parameters (unused)
        """
        # Compute scores from training data (strategy controls lookback)
        self._scores = compute_scores(
            X_train, y_train, quantiles, n_days=self._n_score_days
        )

        if not any(self._scores.values()):
            logger.warning(
                "No scores computed from training data. "
                "All forecasters will receive equal weights."
            )

        self._add_metadata("beta", self._beta)
        self._add_metadata("outlier_detection", self._outlier_detection)
        self._add_metadata("n_score_days", self._n_score_days)

    def _do_predict(
        self,
        X_test: pd.DataFrame,
        quantiles: list[str],
    ) -> pd.DataFrame:
        """
        Generate weighted average ensemble predictions.

        :param X_test: DataFrame with forecaster predictions for forecast period.
            Columns should be in format "{forecaster_id}_{quantile}" or
            "{forecaster_id}" for single-quantile data.
        :param quantiles: List of quantile names to predict

        :return: DataFrame with columns [datetime, variable, value]
        """
        results = []

        for quantile in quantiles:
            # Extract columns for this quantile
            quantile_cols = self._get_quantile_columns(X_test, quantile)

            if not quantile_cols:
                # Try without suffix (for pre-filtered data)
                quantile_cols = list(X_test.columns)

            if not quantile_cols:
                logger.warning(f"No forecaster columns found for {quantile}")
                continue

            forecast_df = X_test[quantile_cols].copy()

            # Get normalized scores for this quantile (simple dict: {col: score})
            quantile_scores = self._scores.get(quantile, {})

            # Outlier detection
            if (
                self._outlier_detection
                and forecast_df.shape[1] >= self._min_forecasters
            ):
                outliers = detect_outliers_dtw(forecast_df, self._outlier_alpha)
                if outliers:
                    logger.info(
                        f"Outlier detection for {quantile}: "
                        f"removing {len(outliers)} forecasters"
                    )
                    forecast_df = forecast_df.drop(columns=outliers)
                    self._add_metadata(f"outliers_{quantile}", outliers)

            # Calculate weights from normalized scores
            raw_scores = np.array(
                [
                    quantile_scores.get(col, self._default_score)
                    for col in forecast_df.columns
                ]
            )

            # Apply exponential transformation
            exp_scores = np.exp(-self._beta * raw_scores)

            # Normalize weights
            weights = exp_scores / exp_scores.sum()

            # Store weights
            weight_dict = {
                self._extract_forecaster_id(col): float(w)
                for col, w in zip(forecast_df.columns, weights)
            }
            self._set_weights(quantile, weight_dict)

            # Calculate weighted average
            weighted_sum = (forecast_df * weights).sum(axis=1)

            # Format output using base class helper (includes clipping)
            results.append(self._format_predictions(weighted_sum, quantile))

        if not results:
            return pd.DataFrame(columns=["datetime", "variable", "value"])

        return pd.concat(results, ignore_index=True)
