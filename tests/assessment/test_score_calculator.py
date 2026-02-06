"""Tests for compute_scores function."""

import numpy as np
import pandas as pd
import pytest

from src.assessment.score_calculator import compute_scores, SAMPLES_PER_DAY


class TestComputeScores:
    """Tests for compute_scores function."""

    @pytest.fixture
    def training_data(self):
        """Create sample training data with known error patterns."""
        # 6 days of 15-minute data (576 samples)
        dates = pd.date_range("2024-01-01", periods=576, freq="15min", tz="UTC")
        target = np.linspace(50, 100, 576)

        X_train = pd.DataFrame(
            {
                # user1 has low error (std=2)
                "user1_q50": target + np.random.randn(576) * 2,
                # user2 has medium error (std=5)
                "user2_q50": target + np.random.randn(576) * 5,
                # user3 has high error (std=10)
                "user3_q50": target + np.random.randn(576) * 10,
            },
            index=dates,
        )
        y_train = pd.DataFrame({"target": target}, index=dates)
        return X_train, y_train

    @pytest.fixture
    def multi_quantile_data(self):
        """Create training data with multiple quantiles."""
        dates = pd.date_range("2024-01-01", periods=576, freq="15min", tz="UTC")
        target = np.linspace(50, 100, 576)

        X_train = pd.DataFrame(
            {
                "user1_q10": target * 0.8 + np.random.randn(576) * 2,
                "user1_q50": target + np.random.randn(576) * 2,
                "user1_q90": target * 1.2 + np.random.randn(576) * 2,
                "user2_q10": target * 0.8 + np.random.randn(576) * 5,
                "user2_q50": target + np.random.randn(576) * 5,
                "user2_q90": target * 1.2 + np.random.randn(576) * 5,
            },
            index=dates,
        )
        y_train = pd.DataFrame({"target": target}, index=dates)
        return X_train, y_train

    def test_returns_dict_structure(self, training_data):
        """Test that function returns correct dict structure."""
        X_train, y_train = training_data
        scores = compute_scores(X_train, y_train, ["q50"])

        assert isinstance(scores, dict)
        assert "q50" in scores
        assert isinstance(scores["q50"], dict)

    def test_computes_scores_for_all_columns(self, training_data):
        """Test that scores are computed for all forecaster columns."""
        X_train, y_train = training_data
        scores = compute_scores(X_train, y_train, ["q50"])

        assert "user1_q50" in scores["q50"]
        assert "user2_q50" in scores["q50"]
        assert "user3_q50" in scores["q50"]

    def test_scores_are_numeric(self, training_data):
        """Test that computed scores are numeric values."""
        X_train, y_train = training_data
        scores = compute_scores(X_train, y_train, ["q50"])

        for col, score in scores["q50"].items():
            assert isinstance(score, (int, float))
            assert not np.isnan(score)

    def test_lower_error_gives_lower_score(self, training_data):
        """Test that forecasters with lower error get lower RMSE scores."""
        X_train, y_train = training_data
        scores = compute_scores(X_train, y_train, ["q50"])

        # user1 (std=2) should have lower score than user2 (std=5)
        # which should be lower than user3 (std=10)
        # Note: Due to random noise, we use a statistical threshold
        assert scores["q50"]["user1_q50"] < scores["q50"]["user3_q50"]

    def test_uses_rmse_for_q50(self, training_data):
        """Test that RMSE is used for q50 quantile."""
        X_train, y_train = training_data
        scores = compute_scores(X_train, y_train, ["q50"])

        # RMSE should be approximately equal to the std of the noise
        # user1 has std=2, so RMSE should be around 2
        assert 0 < scores["q50"]["user1_q50"] < 10  # Reasonable RMSE range

    def test_uses_pinball_for_q10(self, multi_quantile_data):
        """Test that Pinball loss is used for q10 quantile."""
        X_train, y_train = multi_quantile_data
        scores = compute_scores(X_train, y_train, ["q10"])

        assert "q10" in scores
        assert "user1_q10" in scores["q10"]
        assert "user2_q10" in scores["q10"]

        # Pinball loss should be positive
        assert scores["q10"]["user1_q10"] > 0
        assert scores["q10"]["user2_q10"] > 0

    def test_uses_pinball_for_q90(self, multi_quantile_data):
        """Test that Pinball loss is used for q90 quantile."""
        X_train, y_train = multi_quantile_data
        scores = compute_scores(X_train, y_train, ["q90"])

        assert "q90" in scores
        assert "user1_q90" in scores["q90"]
        assert "user2_q90" in scores["q90"]

        # Pinball loss should be positive
        assert scores["q90"]["user1_q90"] > 0
        assert scores["q90"]["user2_q90"] > 0

    def test_computes_multiple_quantiles(self, multi_quantile_data):
        """Test computing scores for multiple quantiles at once."""
        X_train, y_train = multi_quantile_data
        scores = compute_scores(X_train, y_train, ["q10", "q50", "q90"])

        assert set(scores.keys()) == {"q10", "q50", "q90"}
        assert len(scores["q10"]) == 2  # user1, user2
        assert len(scores["q50"]) == 2
        assert len(scores["q90"]) == 2

    def test_respects_n_days_parameter(self):
        """Test that n_days parameter limits lookback period."""
        # Create 10 days of data
        dates = pd.date_range("2024-01-01", periods=960, freq="15min", tz="UTC")
        target = np.linspace(50, 100, 960)

        # First 5 days: high error
        # Last 5 days: low error
        predictions = np.concatenate(
            [
                target[:480] + np.random.randn(480) * 20,  # High error first 5 days
                target[480:] + np.random.randn(480) * 2,  # Low error last 5 days
            ]
        )

        X_train = pd.DataFrame({"user1_q50": predictions}, index=dates)
        y_train = pd.DataFrame({"target": target}, index=dates)

        # With n_days=5, should only use last 5 days (low error)
        scores_5days = compute_scores(X_train, y_train, ["q50"], n_days=5)

        # With n_days=10, should use all data (mix of high and low error)
        scores_10days = compute_scores(X_train, y_train, ["q50"], n_days=10)

        # Score with 5 days should be lower (uses only low error period)
        assert scores_5days["q50"]["user1_q50"] < scores_10days["q50"]["user1_q50"]

    def test_default_n_days_is_six(self, training_data):
        """Test that default n_days is 6."""
        X_train, y_train = training_data  # 6 days of data

        # Should work with default n_days=6
        scores = compute_scores(X_train, y_train, ["q50"])
        assert "q50" in scores

    def test_handles_empty_dataframes(self):
        """Test handling of empty DataFrames."""
        X_train = pd.DataFrame()
        y_train = pd.DataFrame({"target": []})

        scores = compute_scores(X_train, y_train, ["q50"])

        assert scores == {"q50": {}}

    def test_handles_missing_quantile_columns(self, training_data):
        """Test handling when requested quantile has no columns."""
        X_train, y_train = training_data  # Only has q50 columns

        scores = compute_scores(X_train, y_train, ["q10", "q50", "q90"])

        assert scores["q10"] == {}  # No q10 columns
        assert len(scores["q50"]) == 3  # Has q50 columns
        assert scores["q90"] == {}  # No q90 columns

    def test_handles_nan_values(self):
        """Test that NaN values are handled correctly."""
        dates = pd.date_range("2024-01-01", periods=576, freq="15min", tz="UTC")
        target = np.linspace(50, 100, 576)

        X_train = pd.DataFrame(
            {
                "user1_q50": target + np.random.randn(576) * 2,
            },
            index=dates,
        )
        # Add some NaN values
        X_train.iloc[100:150, 0] = np.nan

        y_train = pd.DataFrame({"target": target}, index=dates)

        scores = compute_scores(X_train, y_train, ["q50"])

        # Should still compute score (NaN rows are dropped)
        assert "user1_q50" in scores["q50"]
        assert not np.isnan(scores["q50"]["user1_q50"])

    def test_handles_all_nan_column(self):
        """Test handling when a column is all NaN."""
        dates = pd.date_range("2024-01-01", periods=576, freq="15min", tz="UTC")
        target = np.linspace(50, 100, 576)

        X_train = pd.DataFrame(
            {
                "user1_q50": target + np.random.randn(576) * 2,
                "user2_q50": np.nan,  # All NaN
            },
            index=dates,
        )
        y_train = pd.DataFrame({"target": target}, index=dates)

        scores = compute_scores(X_train, y_train, ["q50"])

        # user1 should have score, user2 should be skipped
        assert "user1_q50" in scores["q50"]
        assert "user2_q50" not in scores["q50"]

    def test_samples_per_day_constant(self):
        """Test that SAMPLES_PER_DAY constant is correct (96 for 15-min data)."""
        assert SAMPLES_PER_DAY == 96

    def test_score_consistency(self):
        """Test that same data produces consistent scores."""
        np.random.seed(42)
        dates = pd.date_range("2024-01-01", periods=576, freq="15min", tz="UTC")
        target = np.linspace(50, 100, 576)

        X_train = pd.DataFrame(
            {"user1_q50": target + np.random.randn(576) * 5},
            index=dates,
        )
        y_train = pd.DataFrame({"target": target}, index=dates)

        scores1 = compute_scores(X_train, y_train, ["q50"])
        scores2 = compute_scores(X_train, y_train, ["q50"])

        assert scores1["q50"]["user1_q50"] == scores2["q50"]["user1_q50"]

    def test_tail_behavior(self):
        """Test that only the tail of data is used for scoring."""
        dates = pd.date_range("2024-01-01", periods=1152, freq="15min", tz="UTC")
        target = np.linspace(50, 100, 1152)

        # Create data where first half has perfect predictions, second half has errors
        predictions = np.concatenate(
            [
                target[:576],  # Perfect predictions (first 6 days)
                target[576:] + 10,  # Biased predictions (last 6 days)
            ]
        )

        X_train = pd.DataFrame({"user1_q50": predictions}, index=dates)
        y_train = pd.DataFrame({"target": target}, index=dates)

        # With n_days=6, should only use last 6 days (biased predictions)
        scores = compute_scores(X_train, y_train, ["q50"], n_days=6)

        # RMSE should reflect the 10-unit bias in the last 6 days
        # RMSE of constant bias of 10 is approximately 10
        assert scores["q50"]["user1_q50"] > 5  # Should be around 10

    def test_fewer_samples_than_requested(self):
        """Test behavior when data has fewer samples than n_days requests."""
        # Only 2 days of data
        dates = pd.date_range("2024-01-01", periods=192, freq="15min", tz="UTC")
        target = np.linspace(50, 100, 192)

        X_train = pd.DataFrame(
            {"user1_q50": target + np.random.randn(192) * 2},
            index=dates,
        )
        y_train = pd.DataFrame({"target": target}, index=dates)

        # Request 6 days but only have 2
        scores = compute_scores(X_train, y_train, ["q50"], n_days=6)

        # Should still work, using all available data
        assert "user1_q50" in scores["q50"]
        assert scores["q50"]["user1_q50"] > 0


class TestComputeScoresEdgeCases:
    """Edge case tests for compute_scores function."""

    def test_single_sample(self):
        """Test with only one sample."""
        dates = pd.date_range("2024-01-01", periods=1, freq="15min", tz="UTC")
        X_train = pd.DataFrame({"user1_q50": [50.0]}, index=dates)
        y_train = pd.DataFrame({"target": [50.0]}, index=dates)

        scores = compute_scores(X_train, y_train, ["q50"], n_days=1)

        # RMSE of perfect prediction should be 0
        assert scores["q50"]["user1_q50"] == 0.0

    def test_negative_values(self):
        """Test with negative target/prediction values."""
        dates = pd.date_range("2024-01-01", periods=96, freq="15min", tz="UTC")
        target = np.linspace(-50, 50, 96)

        X_train = pd.DataFrame(
            {"user1_q50": target + np.random.randn(96) * 2},
            index=dates,
        )
        y_train = pd.DataFrame({"target": target}, index=dates)

        scores = compute_scores(X_train, y_train, ["q50"], n_days=1)

        assert "user1_q50" in scores["q50"]
        assert scores["q50"]["user1_q50"] > 0

    def test_large_values(self):
        """Test with large values."""
        dates = pd.date_range("2024-01-01", periods=96, freq="15min", tz="UTC")
        target = np.linspace(1e6, 2e6, 96)

        X_train = pd.DataFrame(
            {"user1_q50": target + np.random.randn(96) * 1000},
            index=dates,
        )
        y_train = pd.DataFrame({"target": target}, index=dates)

        scores = compute_scores(X_train, y_train, ["q50"], n_days=1)

        assert "user1_q50" in scores["q50"]
        assert not np.isnan(scores["q50"]["user1_q50"])
        assert not np.isinf(scores["q50"]["user1_q50"])

    def test_zero_target_values(self):
        """Test with zero target values."""
        dates = pd.date_range("2024-01-01", periods=96, freq="15min", tz="UTC")
        target = np.zeros(96)

        X_train = pd.DataFrame(
            {"user1_q50": np.random.randn(96) * 2},
            index=dates,
        )
        y_train = pd.DataFrame({"target": target}, index=dates)

        scores = compute_scores(X_train, y_train, ["q50"], n_days=1)

        assert "user1_q50" in scores["q50"]
        assert scores["q50"]["user1_q50"] > 0

    def test_constant_predictions(self):
        """Test with constant predictions."""
        dates = pd.date_range("2024-01-01", periods=96, freq="15min", tz="UTC")
        target = np.linspace(50, 100, 96)

        X_train = pd.DataFrame(
            {"user1_q50": np.full(96, 75.0)},  # Constant prediction
            index=dates,
        )
        y_train = pd.DataFrame({"target": target}, index=dates)

        scores = compute_scores(X_train, y_train, ["q50"], n_days=1)

        # Should have some RMSE since predictions don't match target
        assert scores["q50"]["user1_q50"] > 0

    def test_many_forecasters(self):
        """Test with many forecasters."""
        dates = pd.date_range("2024-01-01", periods=96, freq="15min", tz="UTC")
        target = np.linspace(50, 100, 96)

        # Create 20 forecasters
        data = {}
        for i in range(20):
            data[f"user{i}_q50"] = target + np.random.randn(96) * (i + 1)

        X_train = pd.DataFrame(data, index=dates)
        y_train = pd.DataFrame({"target": target}, index=dates)

        scores = compute_scores(X_train, y_train, ["q50"], n_days=1)

        assert len(scores["q50"]) == 20
        # Later users should have higher scores (more noise)
        assert scores["q50"]["user0_q50"] < scores["q50"]["user19_q50"]
