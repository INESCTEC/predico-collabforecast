"""Tests for lag feature generation."""

import numpy as np
import pandas as pd
import pytest

from src.features import create_lag_features


class TestCreateLagFeatures:
    """Tests for create_lag_features function."""

    @pytest.fixture
    def sample_df(self):
        """Create sample DataFrame with datetime index."""
        dates = pd.date_range("2024-01-01", periods=5, freq="h", tz="UTC")
        return pd.DataFrame(
            {"a": [1.0, 2.0, 3.0, 4.0, 5.0], "b": [10.0, 20.0, 30.0, 40.0, 50.0]},
            index=dates,
        )

    def test_creates_single_lag(self, sample_df):
        """Test creating a single lag."""
        result = create_lag_features(sample_df, max_lags=1)

        assert "a_t-1" in result.columns
        assert "b_t-1" in result.columns
        assert len(result.columns) == 2

    def test_creates_multiple_lags(self, sample_df):
        """Test creating multiple lags."""
        result = create_lag_features(sample_df, max_lags=3)

        assert "a_t-1" in result.columns
        assert "a_t-2" in result.columns
        assert "a_t-3" in result.columns
        assert "b_t-1" in result.columns
        assert "b_t-2" in result.columns
        assert "b_t-3" in result.columns
        assert len(result.columns) == 6

    def test_lag_values_are_correct(self, sample_df):
        """Test that lagged values are correct."""
        result = create_lag_features(sample_df, max_lags=2)

        # First row should have NaN for lag features
        assert pd.isna(result["a_t-1"].iloc[0])
        assert pd.isna(result["a_t-2"].iloc[0])
        assert pd.isna(result["a_t-2"].iloc[1])

        # Check actual shifted values
        np.testing.assert_equal(result["a_t-1"].iloc[1], 1.0)
        np.testing.assert_equal(result["a_t-1"].iloc[2], 2.0)
        np.testing.assert_equal(result["a_t-2"].iloc[2], 1.0)

    def test_specific_columns(self, sample_df):
        """Test creating lags for specific columns only."""
        result = create_lag_features(sample_df, max_lags=2, columns=["a"])

        assert "a_t-1" in result.columns
        assert "a_t-2" in result.columns
        assert "b_t-1" not in result.columns
        assert len(result.columns) == 2

    def test_preserves_index(self, sample_df):
        """Test that output preserves the original index."""
        result = create_lag_features(sample_df, max_lags=1)

        pd.testing.assert_index_equal(result.index, sample_df.index)

    def test_empty_dataframe(self):
        """Test handling of empty DataFrame."""
        empty_df = pd.DataFrame()
        result = create_lag_features(empty_df, max_lags=2)

        assert result.empty

    def test_no_numeric_columns(self):
        """Test handling DataFrame with no numeric columns."""
        df = pd.DataFrame({"text": ["a", "b", "c"]})
        result = create_lag_features(df, max_lags=2)

        assert result.empty

    def test_nonexistent_column(self, sample_df):
        """Test handling of nonexistent column in columns list."""
        result = create_lag_features(sample_df, max_lags=1, columns=["nonexistent"])

        assert result.empty

    def test_returns_only_lag_features(self, sample_df):
        """Test that original columns are not included in output."""
        result = create_lag_features(sample_df, max_lags=1)

        assert "a" not in result.columns
        assert "b" not in result.columns
