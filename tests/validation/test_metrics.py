"""Tests for the internal validation metrics module."""

import numpy as np
import pandas as pd
import pytest

from examples.internal.validation import metrics


class TestComputeForecasterScores:
    """Tests for compute_forecaster_scores function."""

    @pytest.fixture
    def sample_submissions(self):
        """Create sample submission data with multiple forecasters."""
        np.random.seed(42)
        dates = pd.date_range("2024-01-01", periods=96, freq="15min")

        submissions = []
        for forecaster_id in ["fc_1", "fc_2", "fc_3"]:
            for variable in ["q10", "q50", "q90"]:
                base_value = 100 + np.random.randn(96) * 10
                if variable == "q10":
                    values = base_value - 20
                elif variable == "q90":
                    values = base_value + 20
                else:
                    values = base_value

                for i, (dt, val) in enumerate(zip(dates, values)):
                    submissions.append(
                        {
                            "datetime": dt,
                            "value": val,
                            "forecaster_id": forecaster_id,
                            "variable": variable,
                            "session_id": 1,
                        }
                    )

        return pd.DataFrame(submissions)

    @pytest.fixture
    def sample_measurements(self):
        """Create sample measurement data."""
        np.random.seed(42)
        dates = pd.date_range("2024-01-01", periods=96, freq="15min")
        observed = 100 + np.random.randn(96) * 5

        return pd.DataFrame(
            {
                "datetime": dates,
                "observed": observed,
                "session_id": [1] * 96,
            }
        )

    def test_returns_list_of_dicts(self, sample_submissions, sample_measurements):
        """Test that the function returns a list of dictionaries."""
        result = metrics.compute_forecaster_scores(
            sample_submissions, sample_measurements
        )
        assert isinstance(result, list)
        assert all(isinstance(item, dict) for item in result)

    def test_score_dict_has_required_keys(
        self, sample_submissions, sample_measurements
    ):
        """Test that score dictionaries have required keys."""
        result = metrics.compute_forecaster_scores(
            sample_submissions, sample_measurements
        )

        required_keys = {"type", "name", "variable", "n_samples"}
        for score in result:
            assert required_keys.issubset(score.keys())

    def test_type_is_forecaster(self, sample_submissions, sample_measurements):
        """Test that all scores have type='forecaster'."""
        result = metrics.compute_forecaster_scores(
            sample_submissions, sample_measurements
        )

        for score in result:
            assert score["type"] == "forecaster"

    def test_computes_scores_for_all_forecasters(
        self, sample_submissions, sample_measurements
    ):
        """Test that scores are computed for all forecasters."""
        result = metrics.compute_forecaster_scores(
            sample_submissions, sample_measurements
        )

        forecaster_names = {score["name"] for score in result}
        assert forecaster_names == {"fc_1", "fc_2", "fc_3"}

    def test_computes_scores_for_all_variables(
        self, sample_submissions, sample_measurements
    ):
        """Test that scores are computed for all variables."""
        result = metrics.compute_forecaster_scores(
            sample_submissions, sample_measurements
        )

        variables = {score["variable"] for score in result}
        # Should have q10, q50, q90, and winkler
        assert "q10" in variables
        assert "q50" in variables
        assert "q90" in variables
        assert "winkler" in variables

    def test_q50_has_rmse_and_mae(self, sample_submissions, sample_measurements):
        """Test that Q50 scores include RMSE and MAE."""
        result = metrics.compute_forecaster_scores(
            sample_submissions, sample_measurements
        )

        q50_scores = [s for s in result if s["variable"] == "q50"]
        for score in q50_scores:
            assert "rmse" in score
            assert "mae" in score
            assert score["rmse"] >= 0
            assert score["mae"] >= 0

    def test_all_quantiles_have_pinball(self, sample_submissions, sample_measurements):
        """Test that all quantile scores include pinball loss."""
        result = metrics.compute_forecaster_scores(
            sample_submissions, sample_measurements
        )

        quantile_scores = [s for s in result if s["variable"] in ["q10", "q50", "q90"]]
        for score in quantile_scores:
            assert "pinball" in score
            assert score["pinball"] >= 0

    def test_winkler_score_computed(self, sample_submissions, sample_measurements):
        """Test that Winkler score is computed for forecasters with q10 and q90."""
        result = metrics.compute_forecaster_scores(
            sample_submissions, sample_measurements
        )

        winkler_scores = [s for s in result if s["variable"] == "winkler"]
        # Should have one winkler score per forecaster
        assert len(winkler_scores) == 3
        for score in winkler_scores:
            assert "winkler" in score
            assert score["winkler"] >= 0

    def test_n_samples_is_correct(self, sample_submissions, sample_measurements):
        """Test that n_samples matches the number of matched records."""
        result = metrics.compute_forecaster_scores(
            sample_submissions, sample_measurements
        )

        for score in result:
            # Each forecaster should have 96 samples per variable
            assert score["n_samples"] == 96

    def test_empty_submissions_returns_empty(self, sample_measurements):
        """Test that empty submissions returns empty list."""
        empty_submissions = pd.DataFrame(
            columns=["datetime", "value", "forecaster_id", "variable", "session_id"]
        )

        result = metrics.compute_forecaster_scores(
            empty_submissions, sample_measurements
        )
        assert result == []

    def test_no_matching_data_returns_empty(self, sample_submissions):
        """Test that non-matching datetimes result in empty scores.

        Note: The merge is done on datetime only (not session_id) because
        measurements for D+1 forecasts appear in later sessions.
        """
        # Use different datetimes that don't overlap with sample_submissions
        measurements = pd.DataFrame(
            {
                "datetime": pd.date_range(
                    "2024-02-01", periods=96, freq="15min"
                ),  # Different date
                "observed": [100] * 96,
                "session_id": [999] * 96,
            }
        )

        result = metrics.compute_forecaster_scores(sample_submissions, measurements)
        assert result == []

    def test_partial_quantiles_no_winkler(self, sample_measurements):
        """Test that forecasters without q10 or q90 don't get Winkler score."""
        # Create submissions with only q50
        dates = pd.date_range("2024-01-01", periods=96, freq="15min")
        submissions = pd.DataFrame(
            {
                "datetime": dates,
                "value": [100] * 96,
                "forecaster_id": ["fc_partial"] * 96,
                "variable": ["q50"] * 96,
                "session_id": [1] * 96,
            }
        )

        result = metrics.compute_forecaster_scores(submissions, sample_measurements)

        winkler_scores = [s for s in result if s["variable"] == "winkler"]
        assert len(winkler_scores) == 0

    def test_lower_error_gives_lower_rmse(self, sample_measurements):
        """Test that a forecaster with lower error gets lower RMSE."""
        dates = pd.date_range("2024-01-01", periods=96, freq="15min")
        observed = sample_measurements["observed"].values

        # Good forecaster: small error
        good_forecasts = observed + np.random.randn(96) * 1
        # Bad forecaster: large error
        bad_forecasts = observed + np.random.randn(96) * 20

        submissions = []
        for dt, good_val, bad_val in zip(dates, good_forecasts, bad_forecasts):
            submissions.append(
                {
                    "datetime": dt,
                    "value": good_val,
                    "forecaster_id": "good_fc",
                    "variable": "q50",
                    "session_id": 1,
                }
            )
            submissions.append(
                {
                    "datetime": dt,
                    "value": bad_val,
                    "forecaster_id": "bad_fc",
                    "variable": "q50",
                    "session_id": 1,
                }
            )

        submissions_df = pd.DataFrame(submissions)
        result = metrics.compute_forecaster_scores(submissions_df, sample_measurements)

        q50_scores = {s["name"]: s["rmse"] for s in result if s["variable"] == "q50"}
        assert q50_scores["good_fc"] < q50_scores["bad_fc"]

    def test_coverage_pct_is_computed(self, sample_submissions, sample_measurements):
        """Test that coverage_pct is computed when max_samples is provided."""
        result = metrics.compute_forecaster_scores(
            sample_submissions, sample_measurements, max_samples=100
        )

        q50_scores = [s for s in result if s["variable"] == "q50"]
        for score in q50_scores:
            assert "coverage_pct" in score
            assert score["coverage_pct"] is not None
            # 96 samples out of 100 max = 96%
            assert score["coverage_pct"] == 96.0

    def test_coverage_pct_is_none_without_max_samples(
        self, sample_submissions, sample_measurements
    ):
        """Test that coverage_pct is None when max_samples is not provided."""
        result = metrics.compute_forecaster_scores(
            sample_submissions, sample_measurements
        )

        for score in result:
            assert score.get("coverage_pct") is None

    def test_ensemble_comparison_is_computed(
        self, sample_submissions, sample_measurements
    ):
        """Test that ensemble_rmse and ensemble_mae are computed for Q50."""
        # Create fake ensemble forecasts
        dates = pd.date_range("2024-01-01", periods=96, freq="15min")
        forecasts_df = pd.DataFrame(
            {
                "datetime": dates,
                "value": [100] * 96,  # Constant forecast
                "strategy": ["weighted_avg"] * 96,
                "variable": ["q50"] * 96,
            }
        )

        result = metrics.compute_forecaster_scores(
            sample_submissions, sample_measurements, forecasts_df=forecasts_df
        )

        q50_scores = [s for s in result if s["variable"] == "q50"]
        for score in q50_scores:
            assert "ensemble_rmse" in score
            assert "ensemble_mae" in score
            assert score["ensemble_rmse"] is not None
            assert score["ensemble_mae"] is not None

    def test_ensemble_comparison_only_for_q50(
        self, sample_submissions, sample_measurements
    ):
        """Test that ensemble comparison is only computed for Q50, not Q10/Q90."""
        # Create fake ensemble forecasts
        dates = pd.date_range("2024-01-01", periods=96, freq="15min")
        forecasts_df = pd.DataFrame(
            {
                "datetime": dates,
                "value": [100] * 96,
                "strategy": ["weighted_avg"] * 96,
                "variable": ["q50"] * 96,
            }
        )

        result = metrics.compute_forecaster_scores(
            sample_submissions, sample_measurements, forecasts_df=forecasts_df
        )

        q10_scores = [s for s in result if s["variable"] == "q10"]
        for score in q10_scores:
            assert "ensemble_rmse" not in score
            assert "ensemble_mae" not in score

    def test_ensemble_comparison_uses_same_datetimes(self, sample_measurements):
        """Test that ensemble comparison uses only the forecaster's datetimes."""
        # Create a forecaster with only half the datetimes
        dates_full = pd.date_range("2024-01-01", periods=96, freq="15min")
        dates_half = dates_full[:48]  # First half only

        submissions = pd.DataFrame(
            {
                "datetime": dates_half,
                "value": [100] * 48,
                "forecaster_id": ["partial_fc"] * 48,
                "variable": ["q50"] * 48,
                "session_id": [1] * 48,
            }
        )

        # Ensemble has all 96 datetimes
        forecasts_df = pd.DataFrame(
            {
                "datetime": dates_full,
                "value": [100] * 96,
                "strategy": ["weighted_avg"] * 96,
                "variable": ["q50"] * 96,
            }
        )

        result = metrics.compute_forecaster_scores(
            submissions, sample_measurements, max_samples=96, forecasts_df=forecasts_df
        )

        q50_score = [s for s in result if s["variable"] == "q50"][0]
        # Forecaster has 48 samples, max is 96, so coverage is 50%
        assert q50_score["coverage_pct"] == 50.0
        # Ensemble comparison should exist
        assert "ensemble_rmse" in q50_score


class TestMetricFunctions:
    """Tests for individual metric functions."""

    @pytest.fixture
    def sample_data(self):
        """Create sample data for metric calculations."""
        return pd.DataFrame(
            {
                "observed": [100, 110, 105, 95, 100],
                "forecast": [98, 112, 103, 97, 102],
            }
        )

    def test_rmse_calculation(self, sample_data):
        """Test RMSE calculation."""
        result = metrics.rmse(sample_data)
        # Manual: sqrt(mean([4, 4, 4, 4, 4])) = sqrt(4) = 2
        assert isinstance(result, float)
        assert result >= 0

    def test_mae_calculation(self, sample_data):
        """Test MAE calculation."""
        result = metrics.mae(sample_data)
        # Manual: mean([2, 2, 2, 2, 2]) = 2
        assert isinstance(result, float)
        assert result >= 0

    def test_pinball_loss_q50(self, sample_data):
        """Test pinball loss for Q50."""
        result = metrics.pinball_loss(sample_data, "q50")
        assert isinstance(result, float)
        assert result >= 0

    def test_pinball_loss_q10(self, sample_data):
        """Test pinball loss for Q10."""
        result = metrics.pinball_loss(sample_data, "q10")
        assert isinstance(result, float)
        assert result >= 0

    def test_pinball_loss_q90(self, sample_data):
        """Test pinball loss for Q90."""
        result = metrics.pinball_loss(sample_data, "q90")
        assert isinstance(result, float)
        assert result >= 0

    def test_winkler_score(self):
        """Test Winkler score calculation."""
        data = pd.DataFrame(
            {
                "observed": [100, 110, 150],
                "q10": [90, 100, 110],
                "q90": [110, 120, 130],
            }
        )
        result = metrics.winkler_score(data)
        assert isinstance(result, float)
        assert result >= 0
        # Third observation is outside interval, so penalty applied
        assert result > 20  # Base width is 20, penalty should increase it
