"""
Best forecaster strategy.

This strategy selects the forecaster with the best recent performance
(lowest score) for each quantile and uses their predictions directly.

This strategy extends BaseStrategy (not SimpleStrategy) because it requires
custom training logic in _do_fit() to compute scores and identify the best
forecaster per quantile.

Example usage::

    from src.strategies import BestForecasterStrategy

    strategy = BestForecasterStrategy()
    strategy.fit(X_train, y_train, ["q10", "q50", "q90"])
    predictions = strategy.predict(X_test, ["q10", "q50", "q90"])
"""

from __future__ import annotations

from typing import Any

import pandas as pd
from loguru import logger

from .core import BaseStrategy, StrategyRegistry
from ..assessment.score_calculator import compute_scores


@StrategyRegistry.register("best_forecaster")
class BestForecasterStrategy(BaseStrategy):
    """
    Best forecaster selection strategy.

    This strategy identifies the forecaster with the lowest recent skill score
    (best performance) for each quantile and uses their predictions directly.
    Only one forecaster contributes per quantile (weight = 1.0).

    This serves as a benchmark to evaluate whether ensemble methods
    outperform simply selecting the best individual forecaster.

    :param default_score: Score assigned to forecasters without historical scores.
        Default is 999999 (effectively never selected as best).

    Example::

        strategy = BestForecasterStrategy()

        # Fit with assessment scores
        strategy.fit(
            X_train, y_train,
            quantiles=["q10", "q50", "q90"],
            scores={
                "q50": {"scores": pd.DataFrame([
                    {"submission": "user_1_q50", "recent_score": 0.05},
                    {"submission": "user_2_q50", "recent_score": 0.10},
                ])},
                ...
            }
        )

        # Generate predictions (uses only the best forecaster)
        predictions = strategy.predict(X_test, ["q10", "q50", "q90"])
    """

    def __init__(self, default_score: float = 999999.0, n_score_days: int = 6):
        """
        Initialize the best forecaster strategy.

        :param default_score: Score for unknown forecasters (default: 999999)
        :param n_score_days: Number of days for score calculation (default: 6)
        """
        super().__init__(
            default_score=default_score,
            n_score_days=n_score_days,
        )
        self._default_score = default_score
        self._n_score_days = n_score_days
        self._best_forecasters: dict[
            str, str
        ] = {}  # quantile -> best forecaster column

    @property
    def name(self) -> str:
        """Return strategy name."""
        return "best_forecaster"

    def _do_fit(
        self,
        X_train: pd.DataFrame,
        y_train: pd.DataFrame,
        quantiles: list[str],
        **kwargs: Any,
    ) -> None:
        """
        Fit the best forecaster strategy.

        Computes scores from training data and identifies the best forecaster
        for each quantile based on lowest skill score.

        :param X_train: Historical forecaster predictions
        :param y_train: Historical actual values with 'target' column
        :param quantiles: List of quantile names
        :param kwargs: Additional parameters (unused)
        """
        # Compute scores from training data
        scores = compute_scores(X_train, y_train, quantiles, n_days=self._n_score_days)

        self._best_forecasters = {}

        for quantile in quantiles:
            quantile_scores = scores.get(quantile, {})

            if not quantile_scores:
                logger.warning(
                    f"No scores computed for {quantile}, "
                    f"will use first available forecaster"
                )
                self._best_forecasters[quantile] = None
                continue

            # Find forecaster with lowest score (best performance)
            best_col = min(quantile_scores, key=quantile_scores.get)
            self._best_forecasters[quantile] = best_col
            logger.info(
                f"Best forecaster for {quantile}: {best_col} "
                f"(score: {quantile_scores[best_col]:.4f})"
            )

        self._add_metadata("best_forecasters", self._best_forecasters.copy())
        self._add_metadata("n_score_days", self._n_score_days)

    def _do_predict(
        self,
        X_test: pd.DataFrame,
        quantiles: list[str],
    ) -> pd.DataFrame:
        """
        Generate predictions using the best forecaster for each quantile.

        :param X_test: DataFrame with forecaster predictions for forecast period
        :param quantiles: List of quantile names to predict
        :return: DataFrame with columns [datetime, variable, value]
        """
        results = []

        for quantile in quantiles:
            # Extract columns for this quantile
            cols = self._get_quantile_columns(X_test, quantile)

            if not cols:
                logger.warning(f"No forecaster columns found for {quantile}")
                continue

            forecasts = X_test[cols]
            best_col = self._best_forecasters.get(quantile)

            # Select best forecaster or fallback to first available
            if best_col and best_col in forecasts.columns:
                selected_col = best_col
            elif best_col:
                # Best forecaster column not in test data, use first available
                logger.warning(
                    f"Best forecaster '{best_col}' not in test data, "
                    f"using first available for {quantile}"
                )
                selected_col = cols[0]
            else:
                # No best forecaster identified, use first available
                selected_col = cols[0]
                logger.warning(
                    f"No best forecaster for {quantile}, using {selected_col}"
                )

            # Set weight = 1.0 for selected forecaster only
            forecaster_id = self._extract_forecaster_id(selected_col)
            self._set_weights(quantile, {forecaster_id: 1.0})

            # Format output using base class helper (includes clipping)
            results.append(self._format_predictions(forecasts[selected_col], quantile))

        if not results:
            logger.warning("No predictions generated - no valid quantile columns found")
            return pd.DataFrame(columns=["datetime", "variable", "value"])

        return pd.concat(results, ignore_index=True)
