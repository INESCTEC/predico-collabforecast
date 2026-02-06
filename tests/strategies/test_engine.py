"""Tests for ForecastEngine."""

import numpy as np
import pandas as pd
import pytest

from src.market.engine import ForecastEngine
from src.core.config import ForecastConfig
from src.core.interfaces import ForecastResult
from src.core.exceptions import StrategyNotFoundError, ForecastError


class TestForecastEngine:
    """Tests for ForecastEngine."""

    @pytest.fixture
    def config(self):
        """Create a test configuration."""
        return ForecastConfig(
            default_strategy="weighted_avg",
            resource_strategies={
                "wind": ["weighted_avg"],
                "solar": ["weighted_avg"],
            },
        )

    @pytest.fixture
    def engine(self, config):
        """Create a ForecastEngine instance."""
        return ForecastEngine(config)

    @pytest.fixture
    def sample_data(self):
        """Create sample test data."""
        dates = pd.date_range("2024-01-01", periods=96, freq="15min", tz="UTC")
        X_test = pd.DataFrame(
            {
                "user1_q50": np.random.rand(96) * 100,
                "user2_q50": np.random.rand(96) * 100,
                "user1_q10": np.random.rand(96) * 80,
                "user2_q10": np.random.rand(96) * 80,
                "user1_q90": np.random.rand(96) * 120,
                "user2_q90": np.random.rand(96) * 120,
            },
            index=dates,
        )
        return X_test, dates

    @pytest.fixture
    def sample_scores(self):
        """Create sample assessment scores."""
        return {
            "q50": {
                "scores": pd.DataFrame(
                    [
                        {"submission": "user1_q50", "recent_score": 0.05},
                        {"submission": "user2_q50", "recent_score": 0.10},
                    ]
                )
            },
            "q10": {
                "scores": pd.DataFrame(
                    [
                        {"submission": "user1_q10", "recent_score": 0.06},
                        {"submission": "user2_q10", "recent_score": 0.11},
                    ]
                )
            },
            "q90": {
                "scores": pd.DataFrame(
                    [
                        {"submission": "user1_q90", "recent_score": 0.07},
                        {"submission": "user2_q90", "recent_score": 0.12},
                    ]
                )
            },
        }

    def test_engine_initialization(self, engine, config):
        """Test engine initializes with config."""
        assert engine.config is config

    def test_engine_default_config(self):
        """Test engine uses default config if none provided."""
        engine = ForecastEngine()
        assert engine.config is not None
        assert engine.config.default_strategy == "weighted_avg"

    def test_forecast_returns_dict_of_results(self, engine, sample_data, sample_scores):
        """Test forecast returns dict mapping strategy to ForecastResult."""
        X_test, dates = sample_data

        results = engine.forecast(
            resource_id="wind",
            X_train=pd.DataFrame(),
            y_train=pd.DataFrame(),
            X_test=X_test,
            forecast_range=dates,
            scores=sample_scores,
        )

        assert isinstance(results, dict)
        assert "weighted_avg" in results
        assert isinstance(results["weighted_avg"], ForecastResult)

    def test_forecast_result_has_predictions(self, engine, sample_data, sample_scores):
        """Test forecast result contains predictions DataFrame."""
        X_test, dates = sample_data

        results = engine.forecast(
            resource_id="wind",
            X_train=pd.DataFrame(),
            y_train=pd.DataFrame(),
            X_test=X_test,
            forecast_range=dates,
            scores=sample_scores,
        )

        predictions = results["weighted_avg"].predictions
        assert isinstance(predictions, pd.DataFrame)
        assert list(predictions.columns) == ["datetime", "variable", "value"]

    def test_forecast_result_has_weights(self, engine, sample_data, sample_scores):
        """Test forecast result contains weights."""
        X_test, dates = sample_data

        results = engine.forecast(
            resource_id="wind",
            X_train=pd.DataFrame(),
            y_train=pd.DataFrame(),
            X_test=X_test,
            forecast_range=dates,
            scores=sample_scores,
        )

        weights = results["weighted_avg"].weights
        assert isinstance(weights, dict)
        assert "q50" in weights

    def test_get_results_after_forecast(self, engine, sample_data, sample_scores):
        """Test get_results returns stored results."""
        X_test, dates = sample_data

        engine.forecast(
            resource_id="wind",
            X_train=pd.DataFrame(),
            y_train=pd.DataFrame(),
            X_test=X_test,
            forecast_range=dates,
            scores=sample_scores,
        )

        stored = engine.get_results("wind")
        assert "weighted_avg" in stored

    def test_get_results_no_forecast_raises(self, engine):
        """Test get_results raises if no forecast done for resource."""
        with pytest.raises(ForecastError):
            engine.get_results("nonexistent_resource")

    def test_forecast_uses_resource_strategies(self, sample_data, sample_scores):
        """Test forecast uses strategies configured for resource."""
        config = ForecastConfig(
            default_strategy="weighted_avg",
            resource_strategies={"wind": ["weighted_avg"]},
        )
        engine = ForecastEngine(config)
        X_test, dates = sample_data

        results = engine.forecast(
            resource_id="wind",
            X_train=pd.DataFrame(),
            y_train=pd.DataFrame(),
            X_test=X_test,
            forecast_range=dates,
            scores=sample_scores,
        )

        assert "weighted_avg" in results

    def test_forecast_uses_default_for_unknown_resource(
        self, sample_data, sample_scores
    ):
        """Test forecast uses default strategy for unknown resource."""
        config = ForecastConfig(default_strategy="weighted_avg")
        engine = ForecastEngine(config)
        X_test, dates = sample_data

        results = engine.forecast(
            resource_id="unknown_resource",
            X_train=pd.DataFrame(),
            y_train=pd.DataFrame(),
            X_test=X_test,
            forecast_range=dates,
            scores=sample_scores,
        )

        assert "weighted_avg" in results

    def test_forecast_unknown_strategy_raises(self, engine, sample_data, sample_scores):
        """Test forecast with unknown strategy raises error."""
        X_test, dates = sample_data

        with pytest.raises(StrategyNotFoundError):
            engine.forecast(
                resource_id="wind",
                X_train=pd.DataFrame(),
                y_train=pd.DataFrame(),
                X_test=X_test,
                forecast_range=dates,
                strategies=["nonexistent_strategy"],
                scores=sample_scores,
            )

    def test_clear_results(self, engine, sample_data, sample_scores):
        """Test clear_results removes stored results."""
        X_test, dates = sample_data

        engine.forecast(
            resource_id="wind",
            X_train=pd.DataFrame(),
            y_train=pd.DataFrame(),
            X_test=X_test,
            forecast_range=dates,
            scores=sample_scores,
        )

        engine.clear_results()

        with pytest.raises(ForecastError):
            engine.get_results("wind")

    def test_forecast_with_custom_quantiles(self, engine, sample_data, sample_scores):
        """Test forecast with custom quantiles."""
        X_test, dates = sample_data

        results = engine.forecast(
            resource_id="wind",
            X_train=pd.DataFrame(),
            y_train=pd.DataFrame(),
            X_test=X_test,
            forecast_range=dates,
            quantiles=["q50"],  # Only q50
            scores=sample_scores,
        )

        predictions = results["weighted_avg"].predictions
        assert set(predictions["variable"].unique()) == {"q50"}
