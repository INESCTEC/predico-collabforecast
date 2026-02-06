"""Tests for benchmark strategies (ArithmeticMean and BestForecaster)."""

import numpy as np
import pandas as pd
import pytest

from src.strategies import (
    StrategyRegistry,
    ArithmeticMeanStrategy,
    BestForecasterStrategy,
)


class TestArithmeticMeanStrategy:
    """Tests for ArithmeticMeanStrategy."""

    @pytest.fixture
    def strategy(self):
        """Create strategy instance."""
        return ArithmeticMeanStrategy()

    @pytest.fixture
    def sample_data(self):
        """Create sample test data."""
        dates = pd.date_range("2024-01-01", periods=4, freq="15min", tz="UTC")
        X_test = pd.DataFrame(
            {
                "user1_q50": [10.0, 20.0, 30.0, 40.0],
                "user2_q50": [20.0, 30.0, 40.0, 50.0],
                "user3_q50": [30.0, 40.0, 50.0, 60.0],
                "user1_q10": [5.0, 10.0, 15.0, 20.0],
                "user2_q10": [10.0, 15.0, 20.0, 25.0],
            },
            index=dates,
        )
        return X_test

    def test_strategy_is_registered(self):
        """Test that ArithmeticMeanStrategy is registered."""
        assert StrategyRegistry.is_registered("arithmetic_mean")

    def test_strategy_name(self, strategy):
        """Test strategy name."""
        assert strategy.name == "arithmetic_mean"

    def test_fit_without_scores(self, strategy):
        """Test fit works without requiring scores."""
        strategy.fit(pd.DataFrame(), pd.DataFrame(), ["q50"])
        assert strategy.is_fitted

    def test_predict_calculates_mean(self, strategy, sample_data):
        """Test that predict calculates arithmetic mean of forecasters."""
        strategy.fit(pd.DataFrame(), pd.DataFrame(), ["q50"])
        predictions = strategy.predict(sample_data, ["q50"])

        # For q50: mean([10,20,30], [20,30,40], [30,40,50], [40,50,60])
        # = [20, 30, 40, 50]
        q50_predictions = predictions[predictions["variable"] == "q50"]["value"].values
        np.testing.assert_array_almost_equal(q50_predictions, [20.0, 30.0, 40.0, 50.0])

    def test_predict_multiple_quantiles(self, strategy, sample_data):
        """Test prediction for multiple quantiles."""
        strategy.fit(pd.DataFrame(), pd.DataFrame(), ["q50", "q10"])
        predictions = strategy.predict(sample_data, ["q50", "q10"])

        assert set(predictions["variable"].unique()) == {"q50", "q10"}

    def test_weights_are_equal(self, strategy, sample_data):
        """Test that all forecasters receive equal weights."""
        strategy.fit(pd.DataFrame(), pd.DataFrame(), ["q50"])
        strategy.predict(sample_data, ["q50"])

        weights = strategy.get_weights()
        q50_weights = list(weights["q50"].values())

        # All weights should be equal (1/3 for 3 forecasters)
        assert all(abs(w - 1 / 3) < 0.01 for w in q50_weights)

    def test_output_format(self, strategy, sample_data):
        """Test output DataFrame has correct columns."""
        strategy.fit(pd.DataFrame(), pd.DataFrame(), ["q50"])
        predictions = strategy.predict(sample_data, ["q50"])

        assert list(predictions.columns) == ["datetime", "variable", "value"]

    def test_values_are_non_negative(self, strategy):
        """Test that negative values are clipped to zero."""
        dates = pd.date_range("2024-01-01", periods=2, freq="15min", tz="UTC")
        X_test = pd.DataFrame(
            {
                "user1_q50": [-10.0, 10.0],
                "user2_q50": [-20.0, -5.0],
            },
            index=dates,
        )

        strategy.fit(pd.DataFrame(), pd.DataFrame(), ["q50"])
        predictions = strategy.predict(X_test, ["q50"])

        # All values should be >= 0
        assert (predictions["value"] >= 0).all()


class TestBestForecasterStrategy:
    """Tests for BestForecasterStrategy."""

    @pytest.fixture
    def strategy(self):
        """Create strategy instance."""
        return BestForecasterStrategy(n_score_days=1)

    @pytest.fixture
    def sample_data(self):
        """Create sample test data with clear differences between forecasters."""
        dates = pd.date_range("2024-01-01", periods=4, freq="15min", tz="UTC")
        X_test = pd.DataFrame(
            {
                "user1_q50": [10.0, 20.0, 30.0, 40.0],  # Best forecaster
                "user2_q50": [100.0, 200.0, 300.0, 400.0],  # Worse forecaster
                "user1_q10": [5.0, 10.0, 15.0, 20.0],
                "user2_q10": [50.0, 100.0, 150.0, 200.0],
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
        # user1 has lowest error, user2 highest
        target = np.linspace(10, 50, 96)
        X_train = pd.DataFrame(
            {
                "user1_q50": target + np.random.randn(96) * 1,  # Low error
                "user2_q50": target + np.random.randn(96) * 20,  # High error
                "user1_q10": target * 0.8 + np.random.randn(96) * 1,
                "user2_q10": target * 0.8 + np.random.randn(96) * 20,
            },
            index=dates,
        )
        y_train = pd.DataFrame({"target": target}, index=dates)
        return X_train, y_train

    def test_strategy_is_registered(self):
        """Test that BestForecasterStrategy is registered."""
        assert StrategyRegistry.is_registered("best_forecaster")

    def test_strategy_name(self, strategy):
        """Test strategy name."""
        assert strategy.name == "best_forecaster"

    def test_fit_identifies_best_forecaster(self, strategy, sample_training_data):
        """Test fit identifies the best forecaster per quantile."""
        X_train, y_train = sample_training_data
        strategy.fit(X_train, y_train, ["q50", "q10"])

        # user1 has lowest error, should be selected as best
        assert strategy._best_forecasters["q50"] == "user1_q50"
        assert strategy._best_forecasters["q10"] == "user1_q10"

    def test_predict_uses_best_forecaster(
        self, strategy, sample_data, sample_training_data
    ):
        """Test predict uses only the best forecaster's predictions."""
        X_train, y_train = sample_training_data
        strategy.fit(X_train, y_train, ["q50"])
        predictions = strategy.predict(sample_data, ["q50"])

        # Should use user1 (best) predictions: [10, 20, 30, 40]
        q50_predictions = predictions[predictions["variable"] == "q50"]["value"].values
        np.testing.assert_array_almost_equal(q50_predictions, [10.0, 20.0, 30.0, 40.0])

    def test_weight_is_one_for_best(self, strategy, sample_data, sample_training_data):
        """Test that best forecaster gets weight 1.0, others 0."""
        X_train, y_train = sample_training_data
        strategy.fit(X_train, y_train, ["q50"])
        strategy.predict(sample_data, ["q50"])

        weights = strategy.get_weights()
        assert weights["q50"]["user1"] == 1.0

    def test_fallback_without_scores(self, strategy, sample_data):
        """Test fallback to first forecaster when no training data provided."""
        # Empty training data means no scores can be computed
        strategy.fit(pd.DataFrame(), pd.DataFrame({"target": []}), ["q50"])
        predictions = strategy.predict(sample_data, ["q50"])

        # Should use first available forecaster (user1)
        q50_predictions = predictions[predictions["variable"] == "q50"]["value"].values
        np.testing.assert_array_almost_equal(q50_predictions, [10.0, 20.0, 30.0, 40.0])

    def test_fallback_when_best_not_in_test(self, strategy):
        """Test fallback when best forecaster not in test data."""
        # Training data with user1 and user2
        train_dates = pd.date_range("2023-12-31", periods=96, freq="15min", tz="UTC")
        target = np.linspace(10, 50, 96)
        X_train = pd.DataFrame(
            {
                "user1_q50": target + np.random.randn(96) * 1,  # Best but not in test
                "user2_q50": target + np.random.randn(96) * 10,
            },
            index=train_dates,
        )
        y_train = pd.DataFrame({"target": target}, index=train_dates)

        # Test data with only user3
        test_dates = pd.date_range("2024-01-01", periods=4, freq="15min", tz="UTC")
        X_test = pd.DataFrame(
            {
                "user3_q50": [100.0, 200.0, 300.0, 400.0],
            },
            index=test_dates,
        )

        strategy.fit(X_train, y_train, ["q50"])
        predictions = strategy.predict(X_test, ["q50"])

        # Should fall back to user3 (only available)
        q50_predictions = predictions[predictions["variable"] == "q50"]["value"].values
        np.testing.assert_array_almost_equal(
            q50_predictions, [100.0, 200.0, 300.0, 400.0]
        )

    def test_output_format(self, strategy, sample_data, sample_training_data):
        """Test output DataFrame has correct columns."""
        X_train, y_train = sample_training_data
        strategy.fit(X_train, y_train, ["q50"])
        predictions = strategy.predict(sample_data, ["q50"])

        assert list(predictions.columns) == ["datetime", "variable", "value"]

    def test_values_are_non_negative(self, strategy, sample_training_data):
        """Test that negative values are clipped to zero."""
        X_train, y_train = sample_training_data
        test_dates = pd.date_range("2024-01-01", periods=2, freq="15min", tz="UTC")
        X_test = pd.DataFrame(
            {
                "user1_q50": [-10.0, 10.0],
                "user2_q50": [-20.0, -5.0],
            },
            index=test_dates,
        )

        strategy.fit(X_train, y_train, ["q50"])
        predictions = strategy.predict(X_test, ["q50"])

        # All values should be >= 0
        assert (predictions["value"] >= 0).all()


class TestStrategyRegistryForBenchmarks:
    """Test strategy registry with benchmark strategies."""

    def test_get_arithmetic_mean(self):
        """Test getting arithmetic_mean strategy from registry."""
        strategy = StrategyRegistry.get("arithmetic_mean")
        assert isinstance(strategy, ArithmeticMeanStrategy)

    def test_get_best_forecaster(self):
        """Test getting best_forecaster strategy from registry."""
        strategy = StrategyRegistry.get("best_forecaster")
        assert isinstance(strategy, BestForecasterStrategy)

    def test_all_benchmark_strategies_listed(self):
        """Test all benchmark strategies are in list."""
        strategies = StrategyRegistry.list_strategies()
        assert "arithmetic_mean" in strategies
        assert "best_forecaster" in strategies
        assert "weighted_avg" in strategies
