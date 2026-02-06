"""Tests for difference feature generation."""

import numpy as np
import pandas as pd
import pytest

from src.features import create_difference_features


class TestCreateDifferenceFeatures:
    """Tests for create_difference_features function."""

    @pytest.fixture
    def sample_df(self):
        """Create sample DataFrame with datetime index."""
        dates = pd.date_range("2024-01-01", periods=5, freq="h", tz="UTC")
        return pd.DataFrame(
            {"a": [1.0, 3.0, 6.0, 10.0, 15.0], "b": [10.0, 20.0, 35.0, 55.0, 80.0]},
            index=dates,
        )

    def test_creates_first_difference(self, sample_df):
        """Test creating first-order difference."""
        result = create_difference_features(sample_df, order=1)

        assert "a_diff" in result.columns
        assert "b_diff" in result.columns
        assert len(result.columns) == 2

    def test_creates_second_difference(self, sample_df):
        """Test creating up to second-order difference."""
        result = create_difference_features(sample_df, order=2)

        assert "a_diff" in result.columns
        assert "a_diff2" in result.columns
        assert "b_diff" in result.columns
        assert "b_diff2" in result.columns
        assert len(result.columns) == 4

    def test_first_difference_values_are_correct(self, sample_df):
        """Test that first difference values are correct."""
        result = create_difference_features(sample_df, order=1)

        # a = [1, 3, 6, 10, 15]
        # diff = [NaN, 2, 3, 4, 5]
        assert pd.isna(result["a_diff"].iloc[0])
        np.testing.assert_array_almost_equal(
            result["a_diff"].iloc[1:].values, [2.0, 3.0, 4.0, 5.0]
        )

    def test_second_difference_values_are_correct(self, sample_df):
        """Test that second difference values are correct."""
        result = create_difference_features(sample_df, order=2)

        # a = [1, 3, 6, 10, 15]
        # diff1 = [NaN, 2, 3, 4, 5]
        # diff2 = [NaN, NaN, 1, 1, 1]
        assert pd.isna(result["a_diff2"].iloc[0])
        assert pd.isna(result["a_diff2"].iloc[1])
        np.testing.assert_array_almost_equal(
            result["a_diff2"].iloc[2:].values, [1.0, 1.0, 1.0]
        )

    def test_specific_columns(self, sample_df):
        """Test creating difference for specific columns."""
        result = create_difference_features(sample_df, order=1, columns=["a"])

        assert "a_diff" in result.columns
        assert "b_diff" not in result.columns
        assert len(result.columns) == 1

    def test_preserves_index(self, sample_df):
        """Test that output preserves the original index."""
        result = create_difference_features(sample_df, order=1)

        pd.testing.assert_index_equal(result.index, sample_df.index)

    def test_empty_dataframe(self):
        """Test handling of empty DataFrame."""
        empty_df = pd.DataFrame()
        result = create_difference_features(empty_df, order=1)

        assert result.empty

    def test_no_numeric_columns(self):
        """Test handling DataFrame with no numeric columns."""
        df = pd.DataFrame({"text": ["a", "b", "c"]})
        result = create_difference_features(df, order=1)

        assert result.empty

    def test_returns_only_difference_features(self, sample_df):
        """Test that original columns are not included in output."""
        result = create_difference_features(sample_df, order=1)

        assert "a" not in result.columns
        assert "b" not in result.columns

    def test_constant_series(self):
        """Test difference of constant series is zero."""
        df = pd.DataFrame({"x": [5.0, 5.0, 5.0, 5.0]})
        result = create_difference_features(df, order=1)

        # Difference of constant series should be 0 (after first NaN)
        np.testing.assert_array_almost_equal(
            result["x_diff"].iloc[1:].values, [0.0, 0.0, 0.0]
        )

    def test_negative_values(self):
        """Test difference with negative values."""
        df = pd.DataFrame({"x": [10.0, 5.0, 0.0, -5.0, -10.0]})
        result = create_difference_features(df, order=1)

        # Differences: [NaN, -5, -5, -5, -5]
        np.testing.assert_array_almost_equal(
            result["x_diff"].iloc[1:].values, [-5.0, -5.0, -5.0, -5.0]
        )

    def test_higher_order_naming(self):
        """Test naming for higher order differences."""
        df = pd.DataFrame({"x": [1.0, 4.0, 9.0, 16.0, 25.0, 36.0]})
        result = create_difference_features(df, order=3)

        assert "x_diff" in result.columns
        assert "x_diff2" in result.columns
        assert "x_diff3" in result.columns
