"""Tests for WeightedAverageStrategy."""

import numpy as np
import pandas as pd
import pytest

from src.strategies import BaseStrategy, StrategyRegistry, WeightedAverageStrategy
from src.core.exceptions import ModelNotFittedError, StrategyNotFoundError
from src.core.interfaces import ForecastStrategy


class TestStrategyRegistry:
    """Tests for StrategyRegistry."""

    def test_weighted_average_is_registered(self):
        """Verify weighted_avg strategy is registered on import."""
        assert StrategyRegistry.is_registered("weighted_avg")

    def test_list_strategies(self):
        """Test listing available strategies."""
        strategies = StrategyRegistry.list_strategies()
        assert "weighted_avg" in strategies

    def test_get_registered_strategy(self):
        """Test getting a registered strategy."""
        strategy = StrategyRegistry.get("weighted_avg")
        assert isinstance(strategy, WeightedAverageStrategy)
        assert strategy.name == "weighted_avg"

    def test_get_unregistered_strategy_raises(self):
        """Test that getting unregistered strategy raises error."""
        with pytest.raises(StrategyNotFoundError):
            StrategyRegistry.get("nonexistent_strategy")

    def test_register_duplicate_raises(self):
        """Test that registering duplicate name raises error."""
        with pytest.raises(ValueError, match="already registered"):

            @StrategyRegistry.register("weighted_avg")
            class DuplicateStrategy(BaseStrategy):
                @property
                def name(self):
                    return "weighted_avg"

                def _do_fit(self, X_train, y_train, quantiles, **kwargs):
                    pass

                def _do_predict(self, X_test, quantiles):
                    return pd.DataFrame()


class TestWeightedAverageStrategy:
    """Tests for WeightedAverageStrategy."""

    @pytest.fixture
    def strategy(self):
        """Create a strategy instance."""
        return WeightedAverageStrategy(beta=0.001, n_score_days=1)

    @pytest.fixture
    def sample_data(self):
        """Create sample test data."""
        dates = pd.date_range("2024-01-01", periods=96, freq="15min", tz="UTC")
        X_test = pd.DataFrame(
            {
                "user1_q50": np.random.rand(96) * 100,
                "user2_q50": np.random.rand(96) * 100,
                "user3_q50": np.random.rand(96) * 100,
            },
            index=dates,
        )
        return X_test

    @pytest.fixture
    def sample_training_data(self):
        """Create sample training data for score computation."""
        # Create 96 rows (1 day) of training data
        dates = pd.date_range("2023-12-31", periods=96, freq="15min", tz="UTC")
        # Create forecaster predictions with different error levels
        # user1 has lowest error, user2 medium, user3 highest
        target = np.linspace(50, 100, 96)
        X_train = pd.DataFrame(
            {
                "user1_q50": target + np.random.randn(96) * 2,  # Low error
                "user2_q50": target + np.random.randn(96) * 5,  # Medium error
                "user3_q50": target + np.random.randn(96) * 10,  # High error
            },
            index=dates,
        )
        y_train = pd.DataFrame({"target": target}, index=dates)
        return X_train, y_train

    def test_strategy_name(self, strategy):
        """Test strategy name."""
        assert strategy.name == "weighted_avg"

    def test_strategy_implements_protocol(self, strategy):
        """Test strategy implements ForecastStrategy protocol."""
        assert isinstance(strategy, ForecastStrategy)

    def test_strategy_not_fitted_initially(self, strategy):
        """Test strategy is not fitted initially."""
        assert not strategy.is_fitted

    def test_predict_before_fit_raises(self, strategy, sample_data):
        """Test that predict before fit raises error."""
        with pytest.raises(ModelNotFittedError):
            strategy.predict(sample_data, ["q50"])

    def test_fit_returns_self(self, strategy, sample_training_data):
        """Test that fit returns self for chaining."""
        X_train, y_train = sample_training_data
        result = strategy.fit(X_train, y_train, ["q50"])
        assert result is strategy

    def test_fit_sets_fitted_state(self, strategy, sample_training_data):
        """Test that fit sets fitted state."""
        X_train, y_train = sample_training_data
        strategy.fit(X_train, y_train, ["q50"])
        assert strategy.is_fitted

    def test_predict_returns_dataframe(
        self, strategy, sample_data, sample_training_data
    ):
        """Test that predict returns DataFrame with correct columns."""
        X_train, y_train = sample_training_data
        strategy.fit(X_train, y_train, ["q50"])
        predictions = strategy.predict(sample_data, ["q50"])

        assert isinstance(predictions, pd.DataFrame)
        assert list(predictions.columns) == ["datetime", "variable", "value"]
        assert len(predictions) == 96  # One per timestamp

    def test_predict_values_are_non_negative(
        self, strategy, sample_data, sample_training_data
    ):
        """Test that predicted values are non-negative."""
        X_train, y_train = sample_training_data
        strategy.fit(X_train, y_train, ["q50"])
        predictions = strategy.predict(sample_data, ["q50"])

        assert (predictions["value"] >= 0).all()

    def test_weights_sum_to_one(self, strategy, sample_data, sample_training_data):
        """Test that weights sum to 1.0."""
        X_train, y_train = sample_training_data
        strategy.fit(X_train, y_train, ["q50"])
        strategy.predict(sample_data, ["q50"])

        weights = strategy.get_weights()
        assert "q50" in weights
        weight_sum = sum(weights["q50"].values())
        assert abs(weight_sum - 1.0) < 1e-6

    def test_lower_scores_get_higher_weights(
        self, strategy, sample_data, sample_training_data
    ):
        """Test that lower scores (better performance) get higher weights."""
        X_train, y_train = sample_training_data
        strategy.fit(X_train, y_train, ["q50"])
        strategy.predict(sample_data, ["q50"])

        weights = strategy.get_weights()["q50"]
        # user1 has lowest error, should have highest weight
        # user3 has highest error, should have lowest weight
        assert weights["user1"] > weights["user3"]

    def test_beta_affects_weight_distribution(self, sample_data, sample_training_data):
        """Test that higher beta gives more weight to better forecasters."""
        X_train, y_train = sample_training_data

        # Low beta (more equal weights)
        strategy_low = WeightedAverageStrategy(beta=0.0001, n_score_days=1)
        strategy_low.fit(X_train, y_train, ["q50"])
        strategy_low.predict(sample_data, ["q50"])
        weights_low = strategy_low.get_weights()["q50"]

        # High beta (more concentrated weights)
        strategy_high = WeightedAverageStrategy(beta=0.5, n_score_days=1)
        strategy_high.fit(X_train, y_train, ["q50"])
        strategy_high.predict(sample_data, ["q50"])
        weights_high = strategy_high.get_weights()["q50"]

        # Higher beta should give more weight to the best forecaster (user1)
        assert weights_high["user1"] > weights_low["user1"]

    def test_get_result_returns_forecast_result(
        self, strategy, sample_data, sample_training_data
    ):
        """Test that get_result returns ForecastResult."""
        X_train, y_train = sample_training_data
        strategy.fit(X_train, y_train, ["q50"])
        predictions = strategy.predict(sample_data, ["q50"])
        result = strategy.get_result(predictions)

        assert result.strategy_name == "weighted_avg"
        assert result.predictions is predictions
        assert "q50" in result.weights

    def test_multiple_quantiles(self):
        """Test predicting multiple quantiles."""
        strategy = WeightedAverageStrategy(beta=0.001, n_score_days=1)

        # Training data
        train_dates = pd.date_range("2023-12-31", periods=96, freq="15min", tz="UTC")
        target = np.linspace(50, 100, 96)
        X_train = pd.DataFrame(
            {
                "user1_q10": target * 0.8 + np.random.randn(96) * 2,
                "user2_q10": target * 0.8 + np.random.randn(96) * 5,
                "user1_q50": target + np.random.randn(96) * 2,
                "user2_q50": target + np.random.randn(96) * 5,
                "user1_q90": target * 1.2 + np.random.randn(96) * 2,
                "user2_q90": target * 1.2 + np.random.randn(96) * 5,
            },
            index=train_dates,
        )
        y_train = pd.DataFrame({"target": target}, index=train_dates)

        # Test data
        test_dates = pd.date_range("2024-01-01", periods=96, freq="15min", tz="UTC")
        X_test = pd.DataFrame(
            {
                "user1_q10": np.random.rand(96) * 80,
                "user2_q10": np.random.rand(96) * 80,
                "user1_q50": np.random.rand(96) * 100,
                "user2_q50": np.random.rand(96) * 100,
                "user1_q90": np.random.rand(96) * 120,
                "user2_q90": np.random.rand(96) * 120,
            },
            index=test_dates,
        )

        strategy.fit(X_train, y_train, ["q10", "q50", "q90"])
        predictions = strategy.predict(X_test, ["q10", "q50", "q90"])

        # Should have 96 * 3 = 288 rows
        assert len(predictions) == 288

        # Should have all three quantiles
        assert set(predictions["variable"].unique()) == {"q10", "q50", "q90"}

        # Should have weights for all quantiles
        weights = strategy.get_weights()
        assert set(weights.keys()) == {"q10", "q50", "q90"}
