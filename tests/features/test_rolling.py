"""Tests for rolling window feature generation."""

import numpy as np
import pandas as pd
import pytest

from src.features import create_rolling_features


class TestCreateRollingFeatures:
    """Tests for create_rolling_features function."""

    @pytest.fixture
    def sample_df(self):
        """Create sample DataFrame with datetime index."""
        dates = pd.date_range("2024-01-01", periods=5, freq="h", tz="UTC")
        return pd.DataFrame(
            {"a": [1.0, 2.0, 3.0, 4.0, 5.0], "b": [10.0, 20.0, 30.0, 40.0, 50.0]},
            index=dates,
        )

    def test_creates_default_rolling_features(self, sample_df):
        """Test creating default rolling features (mean and std)."""
        result = create_rolling_features(sample_df, window=2)

        assert "a_avg" in result.columns
        assert "a_std" in result.columns
        assert "b_avg" in result.columns
        assert "b_std" in result.columns
        assert len(result.columns) == 4

    def test_creates_specified_stats(self, sample_df):
        """Test creating specific statistics."""
        result = create_rolling_features(
            sample_df, window=2, stats=["mean", "min", "max"]
        )

        assert "a_avg" in result.columns
        assert "a_min" in result.columns
        assert "a_max" in result.columns
        assert "a_std" not in result.columns

    def test_rolling_mean_is_correct(self, sample_df):
        """Test that rolling mean calculation is correct."""
        result = create_rolling_features(sample_df, window=2, stats=["mean"])

        # Rolling mean with window=2, min_periods=1
        # [1.0, (1+2)/2, (2+3)/2, (3+4)/2, (4+5)/2]
        np.testing.assert_array_almost_equal(
            result["a_avg"].values, [1.0, 1.5, 2.5, 3.5, 4.5]
        )

    def test_rolling_std_is_correct(self, sample_df):
        """Test that rolling std calculation is correct."""
        result = create_rolling_features(sample_df, window=3, stats=["std"])

        # First value has only 1 point, so std is NaN
        # Second value has 2 points, etc.
        # Window of [1, 2, 3] has std ≈ 1.0
        np.testing.assert_almost_equal(result["a_std"].iloc[2], 1.0, decimal=5)

    def test_specific_columns(self, sample_df):
        """Test creating rolling features for specific columns."""
        result = create_rolling_features(sample_df, window=2, columns=["a"])

        assert "a_avg" in result.columns
        assert "b_avg" not in result.columns

    def test_larger_window(self, sample_df):
        """Test with larger window size."""
        result = create_rolling_features(sample_df, window=3, stats=["mean"])

        # Window=3 rolling mean with min_periods=1
        # [1, (1+2)/2, (1+2+3)/3, (2+3+4)/3, (3+4+5)/3]
        np.testing.assert_array_almost_equal(
            result["a_avg"].values, [1.0, 1.5, 2.0, 3.0, 4.0]
        )

    def test_preserves_index(self, sample_df):
        """Test that output preserves the original index."""
        result = create_rolling_features(sample_df, window=2)

        pd.testing.assert_index_equal(result.index, sample_df.index)

    def test_empty_dataframe(self):
        """Test handling of empty DataFrame."""
        empty_df = pd.DataFrame()
        result = create_rolling_features(empty_df, window=2)

        assert result.empty

    def test_no_numeric_columns(self):
        """Test handling DataFrame with no numeric columns."""
        df = pd.DataFrame({"text": ["a", "b", "c"]})
        result = create_rolling_features(df, window=2)

        assert result.empty

    def test_returns_only_rolling_features(self, sample_df):
        """Test that original columns are not included in output."""
        result = create_rolling_features(sample_df, window=2)

        assert "a" not in result.columns
        assert "b" not in result.columns

    def test_invalid_stat_ignored(self, sample_df):
        """Test that invalid statistics are ignored."""
        result = create_rolling_features(
            sample_df, window=2, stats=["mean", "invalid_stat"]
        )

        assert "a_avg" in result.columns
        assert "a_invalid_stat" not in result.columns

    def test_var_calculation(self, sample_df):
        """Test variance calculation."""
        result = create_rolling_features(sample_df, window=3, stats=["var"])

        # Window of [1, 2, 3] has var = 1.0
        np.testing.assert_almost_equal(result["a_var"].iloc[2], 1.0, decimal=5)
