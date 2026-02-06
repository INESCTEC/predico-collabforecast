"""Tests for forecaster diversity feature generation."""

import numpy as np
import pandas as pd
import pytest

from src.features import create_diversity_features


class TestCreateDiversityFeatures:
    """Tests for create_diversity_features function."""

    @pytest.fixture
    def sample_df(self):
        """Create sample DataFrame with forecaster columns."""
        return pd.DataFrame(
            {
                "user1_q50": [10.0, 20.0, 30.0],
                "user2_q50": [12.0, 22.0, 32.0],
                "user3_q50": [14.0, 24.0, 34.0],
                "user1_q10": [5.0, 10.0, 15.0],
                "user2_q10": [6.0, 11.0, 16.0],
            }
        )

    def test_creates_diversity_columns(self, sample_df):
        """Test that all diversity columns are created."""
        result = create_diversity_features(sample_df, quantile="q50")

        assert "forecasters_std" in result.columns
        assert "forecasters_var" in result.columns
        assert "forecasters_mean" in result.columns
        assert len(result.columns) == 3

    def test_mean_is_correct(self, sample_df):
        """Test that mean calculation is correct."""
        result = create_diversity_features(sample_df, quantile="q50")

        # Mean of [10, 12, 14] = 12, [20, 22, 24] = 22, [30, 32, 34] = 32
        np.testing.assert_array_almost_equal(
            result["forecasters_mean"].values, [12.0, 22.0, 32.0]
        )

    def test_std_is_correct(self, sample_df):
        """Test that standard deviation calculation is correct."""
        result = create_diversity_features(sample_df, quantile="q50")

        # Std of [10, 12, 14], [20, 22, 24], [30, 32, 34]
        expected_std = np.std([10.0, 12.0, 14.0], ddof=1)
        np.testing.assert_almost_equal(result["forecasters_std"].iloc[0], expected_std)

    def test_var_is_correct(self, sample_df):
        """Test that variance calculation is correct."""
        result = create_diversity_features(sample_df, quantile="q50")

        expected_var = np.var([10.0, 12.0, 14.0], ddof=1)
        np.testing.assert_almost_equal(result["forecasters_var"].iloc[0], expected_var)

    def test_filters_by_quantile(self, sample_df):
        """Test that only specified quantile columns are used."""
        result_q50 = create_diversity_features(sample_df, quantile="q50")
        result_q10 = create_diversity_features(sample_df, quantile="q10")

        # q50 has 3 forecasters, q10 has 2
        # Mean of [10, 12, 14] = 12 for q50
        # Mean of [5, 6] = 5.5 for q10
        np.testing.assert_almost_equal(result_q50["forecasters_mean"].iloc[0], 12.0)
        np.testing.assert_almost_equal(result_q10["forecasters_mean"].iloc[0], 5.5)

    def test_uses_all_columns_when_no_quantile(self, sample_df):
        """Test that all numeric columns are used when quantile is None."""
        result = create_diversity_features(sample_df, quantile=None)

        # Mean across all 5 columns
        expected_mean = np.mean([10.0, 12.0, 14.0, 5.0, 6.0])
        np.testing.assert_almost_equal(
            result["forecasters_mean"].iloc[0], expected_mean
        )

    def test_preserves_index(self, sample_df):
        """Test that output preserves the original index."""
        sample_df.index = pd.date_range("2024-01-01", periods=3, freq="h", tz="UTC")
        result = create_diversity_features(sample_df, quantile="q50")

        pd.testing.assert_index_equal(result.index, sample_df.index)

    def test_empty_dataframe(self):
        """Test handling of empty DataFrame."""
        empty_df = pd.DataFrame()
        result = create_diversity_features(empty_df)

        assert result.empty

    def test_no_matching_columns(self):
        """Test handling when no columns match the quantile pattern."""
        df = pd.DataFrame({"user1_q50": [1.0], "user2_q50": [2.0]})
        result = create_diversity_features(df, quantile="q90")

        assert result.empty

    def test_single_forecaster(self):
        """Test handling with a single forecaster (std/var should be NaN)."""
        df = pd.DataFrame({"user1_q50": [10.0, 20.0, 30.0]})
        result = create_diversity_features(df, quantile="q50")

        # Mean should equal the single forecaster
        np.testing.assert_array_almost_equal(
            result["forecasters_mean"].values, [10.0, 20.0, 30.0]
        )
        # Std and var should be NaN for single value
        assert result["forecasters_std"].isna().all()

    def test_handles_inf_values(self):
        """Test that infinite values are replaced with NaN."""
        df = pd.DataFrame({"user1_q50": [np.inf, 10.0], "user2_q50": [np.inf, 20.0]})
        result = create_diversity_features(df, quantile="q50")

        # Result should not contain inf
        assert not np.isinf(result.values).any()
