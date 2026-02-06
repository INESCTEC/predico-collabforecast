"""
Feature engineering helper functions.

These utilities help strategies create common feature types.
Each strategy decides which features to use and how to combine them.

Example usage::

    from forecast.src.features import (
        create_lag_features,
        create_polynomial_features,
        create_diversity_features,
    )

    # Strategy creates its own feature pipeline
    def _do_fit(self, X_train, y_train, quantiles, **kwargs):
        features = [X_train]
        features.append(create_lag_features(X_train, max_lags=2))
        features.append(create_polynomial_features(X_train, degree=2))
        X_augmented = pd.concat(features, axis=1).dropna()
        # ... train model
"""

from .lag import create_lag_features
from .polynomial import create_polynomial_features
from .diversity import create_diversity_features
from .rolling import create_rolling_features
from .difference import create_difference_features

__all__ = [
    "create_lag_features",
    "create_polynomial_features",
    "create_diversity_features",
    "create_rolling_features",
    "create_difference_features",
]
