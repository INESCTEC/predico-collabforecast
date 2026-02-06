"""Tests for SimpleStrategy base class and MedianStrategy example."""

import numpy as np
import pandas as pd
import pytest

from src.strategies import (
    BaseStrategy,
    SimpleStrategy,
    StrategyRegistry,
    MedianStrategy,
)


class TestSimpleStrategyHelpers:
    """Tests for helper methods added to BaseStrategy."""

    @pytest.fixture
    def strategy(self):
        """Create a concrete SimpleStrategy for testing."""
        return MedianStrategy()

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

    def test_get_quantile_columns(self, strategy, sample_data):
        """Test _get_quantile_columns extracts correct columns."""
        q50_cols = strategy._get_quantile_columns(sample_data, "q50")
        assert set(q50_cols) == {"user1_q50", "user2_q50", "user3_q50"}

        q10_cols = strategy._get_quantile_columns(sample_data, "q10")
        assert set(q10_cols) == {"user1_q10", "user2_q10"}

    def test_get_quantile_columns_empty(self, strategy, sample_data):
        """Test _get_quantile_columns returns empty list for missing quantile."""
        q90_cols = strategy._get_quantile_columns(sample_data, "q90")
        assert q90_cols == []

    def test_extract_forecaster_id(self, strategy):
        """Test _extract_forecaster_id parses column names correctly."""
        assert strategy._extract_forecaster_id("user1_q50") == "user1"
        assert strategy._extract_forecaster_id("forecaster_abc_q10") == "forecaster_abc"
        assert strategy._extract_forecaster_id("single") == "single"

    def test_format_predictions(self, strategy):
        """Test _format_predictions creates correct DataFrame format."""
        dates = pd.date_range("2024-01-01", periods=3, freq="15min", tz="UTC")
        values = pd.Series([10.0, 20.0, 30.0], index=dates)

        result = strategy._format_predictions(values, "q50")

        assert list(result.columns) == ["datetime", "variable", "value"]
        assert len(result) == 3
        assert (result["variable"] == "q50").all()
        np.testing.assert_array_equal(result["value"].values, [10.0, 20.0, 30.0])

    def test_format_predictions_clips_negative(self, strategy):
        """Test _format_predictions clips negative values to zero."""
        dates = pd.date_range("2024-01-01", periods=3, freq="15min", tz="UTC")
        values = pd.Series([-10.0, 0.0, 10.0], index=dates)

        result = strategy._format_predictions(values, "q50")

        np.testing.assert_array_equal(result["value"].values, [0.0, 0.0, 10.0])

    def test_set_equal_weights(self, strategy, sample_data):
        """Test _set_equal_weights sets correct equal weights."""
        q50_cols = strategy._get_quantile_columns(sample_data, "q50")
        strategy._set_equal_weights("q50", q50_cols)

        weights = strategy.get_weights()
        assert "q50" in weights
        assert len(weights["q50"]) == 3
        for weight in weights["q50"].values():
            assert abs(weight - 1 / 3) < 0.001

    def test_set_equal_weights_empty(self, strategy):
        """Test _set_equal_weights handles empty columns gracefully."""
        strategy._set_equal_weights("q90", [])
        # Should not raise, weights should be empty or not set
        weights = strategy.get_weights()
        assert "q90" not in weights or len(weights.get("q90", {})) == 0


class TestSimpleStrategyInterface:
    """Tests for SimpleStrategy interface and inheritance."""

    def test_simple_strategy_inherits_base(self):
        """Test SimpleStrategy inherits from BaseStrategy."""
        assert issubclass(SimpleStrategy, BaseStrategy)

    def test_combine_is_abstract(self):
        """Test that combine() must be implemented."""
        # Cannot instantiate SimpleStrategy directly
        with pytest.raises(TypeError, match="combine"):
            SimpleStrategy()


class TestMedianStrategy:
    """Tests for MedianStrategy example implementation."""

    @pytest.fixture
    def strategy(self):
        """Create strategy instance."""
        return MedianStrategy()

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
        """Test that MedianStrategy is registered."""
        assert StrategyRegistry.is_registered("median")

    def test_strategy_name(self, strategy):
        """Test strategy name."""
        assert strategy.name == "median"

    def test_fit_sets_fitted_flag(self, strategy):
        """Test fit sets the fitted flag."""
        strategy.fit(pd.DataFrame(), pd.DataFrame(), ["q50"])
        assert strategy.is_fitted

    def test_predict_calculates_median(self, strategy, sample_data):
        """Test that predict calculates median of forecasters."""
        strategy.fit(pd.DataFrame(), pd.DataFrame(), ["q50"])
        predictions = strategy.predict(sample_data, ["q50"])

        # For q50: median([10,20,30], [20,30,40], [30,40,50], [40,50,60])
        # = [20, 30, 40, 50] (middle value of 3 forecasters)
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

    def test_empty_quantile_returns_empty(self, strategy, sample_data):
        """Test missing quantile returns empty result."""
        strategy.fit(pd.DataFrame(), pd.DataFrame(), ["q90"])
        predictions = strategy.predict(sample_data, ["q90"])

        # q90 not in sample_data, should return empty
        assert len(predictions) == 0 or predictions.empty

    def test_get_from_registry(self):
        """Test getting median strategy from registry."""
        strategy = StrategyRegistry.get("median")
        assert isinstance(strategy, MedianStrategy)


class TestCustomSimpleStrategy:
    """Test creating a custom strategy using SimpleStrategy."""

    def test_custom_strategy_works(self):
        """Test that a custom SimpleStrategy implementation works."""

        # Define a simple custom strategy inline
        @StrategyRegistry.register("test_max")
        class MaxStrategy(SimpleStrategy):
            @property
            def name(self) -> str:
                return "test_max"

            def combine(self, forecasts, quantile, **kwargs):
                return forecasts.max(axis=1)

        try:
            # Test it works
            dates = pd.date_range("2024-01-01", periods=3, freq="15min", tz="UTC")
            X_test = pd.DataFrame(
                {
                    "user1_q50": [10.0, 20.0, 30.0],
                    "user2_q50": [15.0, 25.0, 35.0],
                },
                index=dates,
            )

            strategy = StrategyRegistry.get("test_max")
            strategy.fit(pd.DataFrame(), pd.DataFrame(), ["q50"])
            predictions = strategy.predict(X_test, ["q50"])

            # Should return max of each row: [15, 25, 35]
            values = predictions[predictions["variable"] == "q50"]["value"].values
            np.testing.assert_array_almost_equal(values, [15.0, 25.0, 35.0])

        finally:
            # Cleanup: unregister the test strategy
            StrategyRegistry.unregister("test_max")

    def test_custom_strategy_with_weights(self):
        """Test custom strategy can set custom weights."""

        @StrategyRegistry.register("test_weighted")
        class CustomWeightedStrategy(SimpleStrategy):
            @property
            def name(self) -> str:
                return "test_weighted"

            def combine(self, forecasts, quantile, **kwargs):
                # Set custom weights (first forecaster gets all weight)
                cols = list(forecasts.columns)
                weights = {self._extract_forecaster_id(cols[0]): 1.0}
                for col in cols[1:]:
                    weights[self._extract_forecaster_id(col)] = 0.0
                self._set_weights(quantile, weights)

                # Return first forecaster's predictions
                return forecasts.iloc[:, 0]

        try:
            dates = pd.date_range("2024-01-01", periods=3, freq="15min", tz="UTC")
            X_test = pd.DataFrame(
                {
                    "user1_q50": [10.0, 20.0, 30.0],
                    "user2_q50": [100.0, 200.0, 300.0],
                },
                index=dates,
            )

            strategy = StrategyRegistry.get("test_weighted")
            strategy.fit(pd.DataFrame(), pd.DataFrame(), ["q50"])
            predictions = strategy.predict(X_test, ["q50"])

            # Check custom weights were set
            weights = strategy.get_weights()
            assert weights["q50"]["user1"] == 1.0
            assert weights["q50"]["user2"] == 0.0

            # Check predictions use first forecaster
            values = predictions[predictions["variable"] == "q50"]["value"].values
            np.testing.assert_array_almost_equal(values, [10.0, 20.0, 30.0])

        finally:
            StrategyRegistry.unregister("test_weighted")
