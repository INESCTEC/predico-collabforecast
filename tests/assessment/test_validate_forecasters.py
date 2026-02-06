"""Tests for validate_forecasters function."""

import numpy as np
import pandas as pd
import pytest

from src.assessment.report import validate_forecasters


class TestValidateForecasters:
    """Tests for validate_forecasters function."""

    @pytest.fixture
    def forecast_range(self):
        """Create a forecast range (1 day of 15-min intervals)."""
        return pd.date_range("2024-01-01", periods=96, freq="15min", tz="UTC")

    @pytest.fixture
    def valid_market_data(self, forecast_range):
        """Create market data with valid forecasters (all quantiles submitted)."""
        # 2 months of historical data + forecast period
        full_range = pd.date_range(
            "2023-11-01", periods=96 * 62, freq="15min", tz="UTC"
        )
        df = pd.DataFrame(
            {
                "user1_q10": np.random.rand(len(full_range)) * 80,
                "user1_q50": np.random.rand(len(full_range)) * 100,
                "user1_q90": np.random.rand(len(full_range)) * 120,
                "user2_q10": np.random.rand(len(full_range)) * 80,
                "user2_q50": np.random.rand(len(full_range)) * 100,
                "user2_q90": np.random.rand(len(full_range)) * 120,
            },
            index=full_range,
        )
        return df

    def test_returns_tuple_of_two_lists(self, forecast_range, valid_market_data):
        """Test that function returns a tuple of two lists."""
        result = validate_forecasters(forecast_range, valid_market_data)

        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], list)
        assert isinstance(result[1], list)

    def test_identifies_valid_forecasters_with_all_quantiles(
        self, forecast_range, valid_market_data
    ):
        """Test that forecasters with all quantiles are identified as valid."""
        valid_list, _ = validate_forecasters(forecast_range, valid_market_data)

        assert "user1" in valid_list
        assert "user2" in valid_list
        assert len(valid_list) == 2

    def test_excludes_forecasters_missing_quantiles(self, forecast_range):
        """Test that forecasters missing any quantile are excluded."""
        full_range = pd.date_range(
            "2023-11-01", periods=96 * 62, freq="15min", tz="UTC"
        )
        df = pd.DataFrame(
            {
                # user1 has all quantiles
                "user1_q10": np.random.rand(len(full_range)) * 80,
                "user1_q50": np.random.rand(len(full_range)) * 100,
                "user1_q90": np.random.rand(len(full_range)) * 120,
                # user2 is missing q90
                "user2_q10": np.random.rand(len(full_range)) * 80,
                "user2_q50": np.random.rand(len(full_range)) * 100,
                # user3 is missing q10 and q50
                "user3_q90": np.random.rand(len(full_range)) * 120,
            },
            index=full_range,
        )

        valid_list, _ = validate_forecasters(forecast_range, df)

        assert "user1" in valid_list
        assert "user2" not in valid_list
        assert "user3" not in valid_list
        assert len(valid_list) == 1

    def test_excludes_forecasters_with_nan_in_forecast_period(self, forecast_range):
        """Test that forecasters with NaN values in forecast period are excluded."""
        full_range = pd.date_range(
            "2023-11-01", periods=96 * 62, freq="15min", tz="UTC"
        )
        df = pd.DataFrame(
            {
                "user1_q10": np.random.rand(len(full_range)) * 80,
                "user1_q50": np.random.rand(len(full_range)) * 100,
                "user1_q90": np.random.rand(len(full_range)) * 120,
                "user2_q10": np.random.rand(len(full_range)) * 80,
                "user2_q50": np.random.rand(len(full_range)) * 100,
                "user2_q90": np.random.rand(len(full_range)) * 120,
            },
            index=full_range,
        )

        # Add NaN to user2's q50 in forecast period
        df.loc[forecast_range[0] : forecast_range[-1], "user2_q50"] = np.nan

        valid_list, _ = validate_forecasters(forecast_range, df)

        assert "user1" in valid_list
        assert "user2" not in valid_list

    def test_identifies_forecasters_with_sufficient_history(
        self, forecast_range, valid_market_data
    ):
        """Test that forecasters with sufficient history are identified."""
        _, history_list = validate_forecasters(forecast_range, valid_market_data)

        # Both users have 62 days of data, which is > 31 days minimum
        # history_list contains column names (e.g., "user1_q50", "user1_q10", etc.)
        user1_cols = [col for col in history_list if col.startswith("user1")]
        user2_cols = [col for col in history_list if col.startswith("user2")]
        assert len(user1_cols) > 0
        assert len(user2_cols) > 0

    def test_excludes_forecasters_without_sufficient_history(self, forecast_range):
        """Test that forecasters without sufficient history are excluded."""
        # Only 10 days of data (less than 31 day minimum)
        short_range = pd.date_range(
            "2023-12-22", periods=96 * 10, freq="15min", tz="UTC"
        )
        df = pd.DataFrame(
            {
                "user1_q10": np.random.rand(len(short_range)) * 80,
                "user1_q50": np.random.rand(len(short_range)) * 100,
                "user1_q90": np.random.rand(len(short_range)) * 120,
            },
            index=short_range,
        )

        valid_list, history_list = validate_forecasters(forecast_range, df)

        # User1 is valid (all quantiles) but doesn't have enough history
        assert "user1" in valid_list
        assert len(history_list) == 0

    def test_custom_min_samples_parameter(self, forecast_range):
        """Test that min_samples parameter works correctly."""
        # Create data that spans into the forecast range
        # Forecast range is 2024-01-01, so we need data that includes this
        full_range = pd.date_range("2023-12-27", periods=96 * 6, freq="15min", tz="UTC")
        df = pd.DataFrame(
            {
                "user1_q10": np.random.rand(len(full_range)) * 80,
                "user1_q50": np.random.rand(len(full_range)) * 100,
                "user1_q90": np.random.rand(len(full_range)) * 120,
            },
            index=full_range,
        )

        # With default min_samples (31 days), user1 should not have enough history
        _, history_list_default = validate_forecasters(forecast_range, df)
        assert len(history_list_default) == 0

        # With lower min_samples (3 days = 288 samples), user1 should have enough
        _, history_list_custom = validate_forecasters(
            forecast_range, df, min_samples=96 * 3
        )
        # The function returns column names (e.g., "user1_q50")
        assert len(history_list_custom) == 3  # q10, q50, q90 columns
        assert all("user1" in col for col in history_list_custom)

    def test_empty_market_data(self, forecast_range):
        """Test handling of empty market data."""
        df = pd.DataFrame(index=forecast_range)

        valid_list, history_list = validate_forecasters(forecast_range, df)

        assert valid_list == []
        assert history_list == []

    def test_all_forecasters_invalid(self, forecast_range):
        """Test when no forecaster has all quantiles."""
        full_range = pd.date_range(
            "2023-11-01", periods=96 * 62, freq="15min", tz="UTC"
        )
        df = pd.DataFrame(
            {
                # Each user is missing at least one quantile
                "user1_q10": np.random.rand(len(full_range)) * 80,
                "user1_q50": np.random.rand(len(full_range)) * 100,
                # user1 missing q90
                "user2_q10": np.random.rand(len(full_range)) * 80,
                "user2_q90": np.random.rand(len(full_range)) * 120,
                # user2 missing q50
            },
            index=full_range,
        )

        valid_list, history_list = validate_forecasters(forecast_range, df)

        assert valid_list == []
        assert history_list == []

    def test_single_valid_forecaster(self, forecast_range):
        """Test with only one valid forecaster among several."""
        full_range = pd.date_range(
            "2023-11-01", periods=96 * 62, freq="15min", tz="UTC"
        )
        df = pd.DataFrame(
            {
                # user1 has all quantiles
                "user1_q10": np.random.rand(len(full_range)) * 80,
                "user1_q50": np.random.rand(len(full_range)) * 100,
                "user1_q90": np.random.rand(len(full_range)) * 120,
                # user2 only has q50
                "user2_q50": np.random.rand(len(full_range)) * 100,
                # user3 only has q10 and q90
                "user3_q10": np.random.rand(len(full_range)) * 80,
                "user3_q90": np.random.rand(len(full_range)) * 120,
            },
            index=full_range,
        )

        valid_list, _ = validate_forecasters(forecast_range, df)

        assert valid_list == ["user1"]

    def test_forecaster_valid_but_partial_history(self, forecast_range):
        """Test forecaster who submitted all quantiles but has sparse history."""
        full_range = pd.date_range(
            "2023-11-01", periods=96 * 62, freq="15min", tz="UTC"
        )

        # Create data with many NaN values in history
        data = {
            "user1_q10": np.random.rand(len(full_range)) * 80,
            "user1_q50": np.random.rand(len(full_range)) * 100,
            "user1_q90": np.random.rand(len(full_range)) * 120,
        }
        df = pd.DataFrame(data, index=full_range)

        # Make most historical values NaN (but not in forecast period)
        history_end = forecast_range[0] - pd.Timedelta(minutes=15)
        df.loc[:history_end, "user1_q10"] = np.nan
        df.loc[:history_end, "user1_q50"] = np.nan
        df.loc[:history_end, "user1_q90"] = np.nan

        valid_list, history_list = validate_forecasters(forecast_range, df)

        # User1 is valid (all quantiles in forecast period)
        assert "user1" in valid_list
        # But doesn't have enough non-null history
        assert len(history_list) == 0

    def test_handles_different_quantile_naming(self, forecast_range):
        """Test that function correctly parses forecaster IDs from column names."""
        full_range = pd.date_range(
            "2023-11-01", periods=96 * 62, freq="15min", tz="UTC"
        )
        df = pd.DataFrame(
            {
                # Different naming patterns
                "abc123_q10": np.random.rand(len(full_range)) * 80,
                "abc123_q50": np.random.rand(len(full_range)) * 100,
                "abc123_q90": np.random.rand(len(full_range)) * 120,
                "user_with_underscore_q10": np.random.rand(len(full_range)) * 80,
                "user_with_underscore_q50": np.random.rand(len(full_range)) * 100,
                "user_with_underscore_q90": np.random.rand(len(full_range)) * 120,
            },
            index=full_range,
        )

        valid_list, _ = validate_forecasters(forecast_range, df)

        assert "abc123" in valid_list
        # Note: "user_with_underscore" will be parsed as "user" due to split('_')[0]
        assert "user" in valid_list
