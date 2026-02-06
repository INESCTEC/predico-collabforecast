"""Tests for polynomial feature generation."""

import numpy as np
import pandas as pd
import pytest

from src.features import create_polynomial_features


class TestCreatePolynomialFeatures:
    """Tests for create_polynomial_features function."""

    @pytest.fixture
    def sample_df(self):
        """Create sample DataFrame."""
        return pd.DataFrame(
            {"a": [1.0, 2.0, 3.0, 4.0], "b": [2.0, 3.0, 4.0, 5.0]},
        )

    def test_creates_squared_features(self, sample_df):
        """Test creating squared features (degree 2)."""
        result = create_polynomial_features(sample_df, degree=2)

        assert "a_sqr" in result.columns
        assert "b_sqr" in result.columns
        assert len(result.columns) == 2

    def test_creates_squared_and_cubic(self, sample_df):
        """Test creating squared and cubic features (degree 3)."""
        result = create_polynomial_features(sample_df, degree=3)

        assert "a_sqr" in result.columns
        assert "a_cub" in result.columns
        assert "b_sqr" in result.columns
        assert "b_cub" in result.columns
        assert len(result.columns) == 4

    def test_polynomial_values_are_correct(self, sample_df):
        """Test that polynomial values are correct."""
        result = create_polynomial_features(sample_df, degree=3)

        # a = [1, 2, 3, 4]
        np.testing.assert_array_almost_equal(
            result["a_sqr"].values, [1.0, 4.0, 9.0, 16.0]
        )
        np.testing.assert_array_almost_equal(
            result["a_cub"].values, [1.0, 8.0, 27.0, 64.0]
        )

    def test_specific_columns(self, sample_df):
        """Test creating polynomial features for specific columns."""
        result = create_polynomial_features(sample_df, degree=2, columns=["a"])

        assert "a_sqr" in result.columns
        assert "b_sqr" not in result.columns
        assert len(result.columns) == 1

    def test_higher_degree_naming(self):
        """Test naming convention for higher degrees."""
        df = pd.DataFrame({"x": [2.0]})
        result = create_polynomial_features(df, degree=5)

        assert "x_sqr" in result.columns  # degree 2
        assert "x_cub" in result.columns  # degree 3
        assert "x_pow4" in result.columns  # degree 4
        assert "x_pow5" in result.columns  # degree 5

    def test_preserves_index(self, sample_df):
        """Test that output preserves the original index."""
        sample_df.index = pd.date_range("2024-01-01", periods=4, freq="h")
        result = create_polynomial_features(sample_df, degree=2)

        pd.testing.assert_index_equal(result.index, sample_df.index)

    def test_empty_dataframe(self):
        """Test handling of empty DataFrame."""
        empty_df = pd.DataFrame()
        result = create_polynomial_features(empty_df, degree=2)

        assert result.empty

    def test_no_numeric_columns(self):
        """Test handling DataFrame with no numeric columns."""
        df = pd.DataFrame({"text": ["a", "b", "c"]})
        result = create_polynomial_features(df, degree=2)

        assert result.empty

    def test_returns_only_polynomial_features(self, sample_df):
        """Test that original columns are not included in output."""
        result = create_polynomial_features(sample_df, degree=2)

        assert "a" not in result.columns
        assert "b" not in result.columns

    def test_handles_negative_values(self):
        """Test polynomial features with negative values."""
        df = pd.DataFrame({"x": [-2.0, -1.0, 0.0, 1.0, 2.0]})
        result = create_polynomial_features(df, degree=3)

        np.testing.assert_array_almost_equal(
            result["x_sqr"].values, [4.0, 1.0, 0.0, 1.0, 4.0]
        )
        np.testing.assert_array_almost_equal(
            result["x_cub"].values, [-8.0, -1.0, 0.0, 1.0, 8.0]
        )
