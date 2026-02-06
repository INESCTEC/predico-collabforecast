"""
Synthetic Data Generator for forecast simulation testing.

This module provides the SyntheticGenerator class which creates controlled
test datasets with:
- Synthetic power measurements (wind/solar patterns)
- Synthetic forecasters with configurable behavioral archetypes
- Scenario templates for testing specific ensemble behaviors

Example:
    >>> from core import SyntheticGenerator
    >>> generator = SyntheticGenerator(seed=42, use_case="wind_power")
    >>> dataset_path = generator.generate_dataset(
    ...     name="test_dataset",
    ...     n_forecasters=5,
    ...     n_days=30,
    ...     archetypes="skilled:2,noisy:2,biased:1",
    ... )
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from loguru import logger


# Archetype configurations (fixed, not user-customizable)
# Each archetype can have optional *_range entries to enable diversity variation
ARCHETYPE_CONFIGS = {
    "skilled": {
        "description": "High accuracy, well-calibrated forecaster",
        "noise_std": 0.05,
        "noise_std_range": (0.03, 0.08),
        "bias": 0.0,
        "bias_range": (-0.02, 0.02),
        "lag_hours": 0,
        "interval_scale": 1.0,
        "interval_scale_range": (0.85, 1.15),
        "invert": False,
        "dropout_prob": 0.0,
    },
    "noisy": {
        "description": "Random errors around truth",
        "noise_std": 0.20,
        "noise_std_range": (0.12, 0.30),
        "bias": 0.0,
        "bias_range": (-0.05, 0.05),
        "lag_hours": 0,
        "interval_scale": 1.0,
        "interval_scale_range": (0.8, 1.2),
        "invert": False,
        "dropout_prob": 0.0,
    },
    "biased": {
        "description": "Systematic over-prediction",
        "noise_std": 0.08,
        "noise_std_range": (0.05, 0.12),
        "bias": 0.10,
        "bias_range": (0.05, 0.20),
        "lag_hours": 0,
        "interval_scale": 1.0,
        "interval_scale_range": (0.9, 1.1),
        "invert": False,
        "dropout_prob": 0.0,
    },
    "biased_low": {
        "description": "Systematic under-prediction",
        "noise_std": 0.08,
        "noise_std_range": (0.05, 0.12),
        "bias": -0.10,
        "bias_range": (-0.20, -0.05),
        "lag_hours": 0,
        "interval_scale": 1.0,
        "interval_scale_range": (0.9, 1.1),
        "invert": False,
        "dropout_prob": 0.0,
    },
    "lagged": {
        "description": "Good but uses stale information",
        "noise_std": 0.05,
        "noise_std_range": (0.03, 0.08),
        "bias": 0.0,
        "bias_range": (-0.02, 0.02),
        "lag_hours": 6,
        "lag_hours_range": (3, 12),
        "interval_scale": 1.0,
        "interval_scale_range": (0.9, 1.1),
        "invert": False,
        "dropout_prob": 0.0,
    },
    "overconfident": {
        "description": "Narrow intervals, poor coverage",
        "noise_std": 0.06,
        "noise_std_range": (0.04, 0.10),
        "bias": 0.0,
        "bias_range": (-0.02, 0.02),
        "lag_hours": 0,
        "interval_scale": 0.5,
        "interval_scale_range": (0.3, 0.7),
        "invert": False,
        "dropout_prob": 0.0,
    },
    "underconfident": {
        "description": "Wide intervals, good coverage",
        "noise_std": 0.06,
        "noise_std_range": (0.04, 0.10),
        "bias": 0.0,
        "bias_range": (-0.02, 0.02),
        "lag_hours": 0,
        "interval_scale": 2.0,
        "interval_scale_range": (1.5, 2.5),
        "invert": False,
        "dropout_prob": 0.0,
    },
    "adversarial": {
        "description": "Deliberately incorrect predictions",
        "noise_std": 0.10,
        "noise_std_range": (0.05, 0.15),
        "bias": 0.0,
        "bias_range": (-0.05, 0.05),
        "lag_hours": 0,
        "interval_scale": 1.0,
        "interval_scale_range": (0.9, 1.1),
        "invert": True,
        "dropout_prob": 0.0,
    },
    "intermittent": {
        "description": "Sometimes missing submissions",
        "noise_std": 0.08,
        "noise_std_range": (0.05, 0.12),
        "bias": 0.0,
        "bias_range": (-0.02, 0.02),
        "lag_hours": 0,
        "interval_scale": 1.0,
        "interval_scale_range": (0.9, 1.1),
        "invert": False,
        "dropout_prob": 0.15,
        "dropout_prob_range": (0.08, 0.25),
    },
    "variable": {
        "description": "Realistic time-varying skill (daily fluctuations + monthly drift)",
        "base_noise_std": 0.10,
        "base_noise_std_range": (0.06, 0.15),
        "daily_variation": 0.5,  # How much noise varies day-to-day
        "daily_variation_range": (0.3, 0.7),
        "monthly_drift": 0.3,  # How much skill changes month-to-month
        "monthly_drift_range": (0.15, 0.45),
        "bias": 0.0,
        "bias_range": (-0.02, 0.02),
        "lag_hours": 0,
        "interval_scale": 1.0,
        "interval_scale_range": (0.9, 1.1),
        "invert": False,
        "dropout_prob": 0.0,
    },
    "outlier": {
        "description": "Occasionally produces outlier predictions",
        "noise_std": 0.08,
        "noise_std_range": (0.05, 0.12),
        "bias": 0.0,
        "bias_range": (-0.02, 0.02),
        "lag_hours": 0,
        "interval_scale": 1.0,
        "interval_scale_range": (0.9, 1.1),
        "invert": False,
        "dropout_prob": 0.0,
        "outlier_prob": 0.10,  # 10% probability of outlier day
        "outlier_prob_range": (0.05, 0.20),
        "outlier_magnitude": 3.0,  # Multiplier for outlier deviation
        "outlier_magnitude_range": (2.0, 4.0),
    },
    "regime_high": {
        "description": "Excellent in high-output regimes (top 30%), over-predicts otherwise",
        "noise_std_good": 0.03,
        "noise_std_good_range": (0.02, 0.05),
        "noise_std_bad": 0.12,
        "noise_std_bad_range": (0.08, 0.16),
        "bias_good": 0.0,
        "bias_good_range": (-0.01, 0.01),
        "bias_bad": 0.20,
        "bias_bad_range": (0.15, 0.25),
        "threshold_percentile": 70,
        "threshold_percentile_range": (65, 75),
        "lag_hours": 0,
        "interval_scale": 1.0,
        "interval_scale_range": (0.9, 1.1),
        "invert": False,
        "dropout_prob": 0.0,
    },
    "regime_low": {
        "description": "Excellent in low-output regimes (bottom 30%), under-predicts otherwise",
        "noise_std_good": 0.03,
        "noise_std_good_range": (0.02, 0.05),
        "noise_std_bad": 0.12,
        "noise_std_bad_range": (0.08, 0.16),
        "bias_good": 0.0,
        "bias_good_range": (-0.01, 0.01),
        "bias_bad": -0.20,
        "bias_bad_range": (-0.25, -0.15),
        "threshold_percentile": 30,
        "threshold_percentile_range": (25, 35),
        "lag_hours": 0,
        "interval_scale": 1.0,
        "interval_scale_range": (0.9, 1.1),
        "invert": False,
        "dropout_prob": 0.0,
    },
}


@dataclass
class GenerationMetadata:
    """Metadata about the synthetic dataset generation."""

    seed: int
    use_case: str
    n_days: int
    n_forecasters: int
    forecaster_archetypes: list[dict[str, Any]]
    scenario: str | None
    scenario_params: dict[str, Any]
    generation_time: str
    data_start: str
    data_end: str
    diversity: float = 0.0
    extra_params: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "seed": self.seed,
            "use_case": self.use_case,
            "n_days": self.n_days,
            "n_forecasters": self.n_forecasters,
            "diversity": self.diversity,
            "forecaster_archetypes": self.forecaster_archetypes,
            "scenario": self.scenario,
            "scenario_params": self.scenario_params,
            "generation_time": self.generation_time,
            "data_start": self.data_start,
            "data_end": self.data_end,
            "extra_params": self.extra_params,
        }


class SyntheticGenerator:
    """Generate synthetic forecasting datasets for testing.

    Creates controlled test scenarios with known properties for:
    - Benchmarking ensemble strategies
    - Testing edge cases (missing data, outliers)
    - Validating algorithm correctness

    :param seed: Random seed for reproducibility
    :param use_case: Type of power generation ("wind_power" or "solar_power")

    Example:
        >>> generator = SyntheticGenerator(seed=42)
        >>> path = generator.generate_dataset(
        ...     name="benchmark_test",
        ...     n_forecasters=5,
        ...     n_days=30,
        ... )
    """

    def __init__(
        self,
        seed: int = 42,
        use_case: str = "wind_power",
        diversity: float = 0.0,
    ) -> None:
        """Initialize the generator.

        :param seed: Random seed for reproducibility
        :param use_case: Type of power generation pattern to simulate
        :param diversity: Parameter diversity level (0.0 to 1.0).
            Controls how much each forecaster's parameters can deviate
            from archetype defaults. 0.0 = identical parameters (default),
            1.0 = maximum variation within archetype ranges.
        """
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        self.use_case = use_case
        self.diversity = max(0.0, min(1.0, diversity))  # Clamp to [0, 1]

        if use_case not in ("wind_power", "solar_power"):
            logger.warning(
                f"Unknown use_case '{use_case}'. Using 'wind_power' pattern as default."
            )
            self.use_case = "wind_power"

        if diversity > 0:
            logger.info(f"Diversity enabled: {self.diversity:.2f}")

    def _apply_diversity(
        self,
        base_value: float,
        param_range: tuple[float, float],
        diversity: float,
        rng: np.random.Generator,
    ) -> float:
        """Apply diversity-based variation to a parameter.

        Given a base value and a valid range, computes a varied value
        based on the diversity level. With diversity=0, returns the base
        value unchanged. With diversity=1, the value can vary across the
        full range centered on the base value.

        :param base_value: The default/base value for the parameter
        :param param_range: Tuple of (min, max) for the valid range
        :param diversity: Diversity level (0.0 to 1.0)
        :param rng: Random generator for reproducibility
        :return: Varied parameter value within range
        """
        min_val, max_val = param_range
        # Scale the variation window by diversity
        full_range = max_val - min_val
        range_width = full_range * diversity

        # Center the variation window on the base value
        varied_min = max(min_val, base_value - range_width / 2)
        varied_max = min(max_val, base_value + range_width / 2)

        return rng.uniform(varied_min, varied_max)

    def _get_varied_config(
        self,
        archetype: str,
        forecaster_idx: int,
    ) -> dict[str, Any]:
        """Create per-forecaster config with diversity-based variation.

        Returns a copy of the archetype config with parameters varied
        based on the diversity setting. Each forecaster gets a deterministic
        but unique variation based on its index.

        :param archetype: Archetype name from ARCHETYPE_CONFIGS
        :param forecaster_idx: Index of the forecaster (for seed offset)
        :return: Config dict with potentially varied parameters
        """
        base = ARCHETYPE_CONFIGS[archetype].copy()

        if self.diversity == 0:
            return base

        # Create a deterministic RNG for this forecaster
        rng = np.random.default_rng(self.seed + forecaster_idx * 1000 + 500)

        # Parameters that can be varied (if they have a *_range entry)
        varying_params = [
            "noise_std",
            "bias",
            "interval_scale",
            "dropout_prob",
            "outlier_prob",
            "outlier_magnitude",
            "lag_hours",
            "base_noise_std",
            "daily_variation",
            "monthly_drift",
        ]

        for param in varying_params:
            range_key = f"{param}_range"
            if range_key in base and base.get(range_key) is not None:
                original = base[param]
                base[param] = self._apply_diversity(
                    base[param],
                    base[range_key],
                    self.diversity,
                    rng,
                )
                # For integer parameters like lag_hours, round to int
                if param == "lag_hours":
                    base[param] = int(round(base[param]))

                logger.debug(
                    f"Forecaster {forecaster_idx}: {param} "
                    f"{original:.4f} -> {base[param]:.4f}"
                )

        return base

    def generate_measurements(
        self,
        n_days: int = 30,
        base_capacity: float = 1000.0,
        start_date: str = "2023-01-15",
    ) -> pd.DataFrame:
        """Generate realistic power measurements.

        Creates synthetic power measurements based on use_case:

        Wind Power Pattern:
        - Base load with diurnal variation (slightly lower at night)
        - High variability (wind gusts, calm periods)
        - Autocorrelation to simulate weather persistence
        - Occasional ramp events

        Solar Power Pattern:
        - Clear daily cycle (zero at night)
        - Peak around midday (bell curve)
        - Cloud cover effects (random dips during daylight)
        - Seasonal variation based on day of year

        :param n_days: Number of days to generate (96 values per day)
        :param base_capacity: Base power capacity in MW
        :param start_date: Start date in YYYY-MM-DD format
        :return: DataFrame with datetime and target columns
        """
        # Generate timestamps (15-minute resolution)
        n_points = n_days * 96  # 96 values per day
        start = pd.Timestamp(start_date, tz="UTC")
        timestamps = pd.date_range(start=start, periods=n_points, freq="15min")

        if self.use_case == "solar_power":
            values = self._generate_solar_pattern(timestamps, base_capacity)
        else:
            values = self._generate_wind_pattern(timestamps, base_capacity)

        # Ensure non-negative values
        values = np.maximum(values, 0)

        df = pd.DataFrame(
            {
                "datetime": timestamps,
                "target": values,
            }
        )

        # Remove timezone for consistency with existing datasets
        df["datetime"] = df["datetime"].dt.tz_localize(None)

        return df

    def _generate_wind_pattern(
        self,
        timestamps: pd.DatetimeIndex,
        base_capacity: float,
    ) -> np.ndarray:
        """Generate wind power pattern with realistic characteristics.

        Wind power characteristics modeled:
        - Mean capacity factor ~35-40%
        - High autocorrelation (weather persistence)
        - Occasional calm periods and high wind events
        - Mild diurnal variation
        - Minimum output floor to avoid excessive zero periods

        :param timestamps: DatetimeIndex of timestamps
        :param base_capacity: Base power capacity in MW
        :return: Array of power values
        """
        n_points = len(timestamps)

        # Base capacity factor (around 40%)
        base_cf = 0.40 * base_capacity

        # Minimum output floor (5% of capacity - turbines rarely produce zero)
        min_output = 0.05 * base_capacity

        # Generate autocorrelated noise using AR(1) process
        # High persistence (phi=0.98) to simulate weather patterns
        phi = 0.98
        noise = np.zeros(n_points)
        # Low innovation std to avoid excessive low-wind periods
        innovation_std = 0.04 * base_capacity
        noise[0] = self.rng.normal(0, innovation_std)
        for i in range(1, n_points):
            noise[i] = phi * noise[i - 1] + self.rng.normal(0, innovation_std)

        # Add diurnal variation (wind often stronger in afternoon)
        hours = timestamps.hour + timestamps.minute / 60.0
        diurnal = 0.05 * base_capacity * np.sin(2 * np.pi * (hours - 14) / 24)

        # Add random ramp events (sudden changes)
        n_ramps = int(n_points / 500)  # ~1 ramp event per 5 days
        ramp_locations = self.rng.choice(n_points, size=n_ramps, replace=False)
        ramp_magnitudes = self.rng.normal(0, 0.15 * base_capacity, size=n_ramps)
        ramps = np.zeros(n_points)
        for loc, mag in zip(ramp_locations, ramp_magnitudes):
            # Ramp persists for several hours
            ramp_duration = self.rng.integers(4, 24)  # 1-6 hours
            end_loc = min(loc + ramp_duration, n_points)
            ramps[loc:end_loc] = mag

        # Combine components
        values = base_cf + noise + diurnal + ramps

        # Add some random high-frequency noise
        values += self.rng.normal(0, 0.02 * base_capacity, size=n_points)

        # Apply minimum output floor (wind turbines rarely produce exactly zero)
        values = np.maximum(values, min_output)

        return values

    def _generate_solar_pattern(
        self,
        timestamps: pd.DatetimeIndex,
        base_capacity: float,
    ) -> np.ndarray:
        """Generate solar power pattern with realistic characteristics.

        Solar power characteristics modeled:
        - Clear daily cycle (zero at night)
        - Bell curve peaking around solar noon
        - Cloud cover effects (random dips during daylight)
        - Day length variation (simplified, based on day of year)

        :param timestamps: DatetimeIndex of timestamps
        :param base_capacity: Base power capacity in MW
        :return: Array of power values
        """
        n_points = len(timestamps)

        # Solar hour angle (peak at ~12:00-13:00 local time)
        hours = timestamps.hour + timestamps.minute / 60.0

        # Simplified sunrise/sunset (assumes ~CET timezone)
        # Day length varies from ~8h (winter) to ~16h (summer)
        day_of_year = timestamps.dayofyear
        day_length = 12 + 4 * np.sin(2 * np.pi * (day_of_year - 80) / 365)
        sunrise = 12 - day_length / 2
        sunset = 12 + day_length / 2

        # Generate bell curve for solar irradiance
        # Peak at solar noon (midpoint between sunrise and sunset)
        daylight_hours = sunset - sunrise

        # Normalized hour position (0 at sunrise, 1 at sunset)
        hour_position = (hours - sunrise) / daylight_hours

        # Bell curve with peak at 0.5 (solar noon)
        # Using a sine wave for simplicity
        irradiance = np.zeros(n_points)
        is_daylight = (hours >= sunrise) & (hours <= sunset)
        irradiance[is_daylight] = np.sin(np.pi * hour_position[is_daylight])

        # Scale by base capacity and seasonal factor
        # Capacity factor peaks ~20-25% on average
        seasonal_factor = 0.8 + 0.2 * np.sin(2 * np.pi * (day_of_year - 80) / 365)
        values = base_capacity * 0.7 * irradiance * seasonal_factor

        # Add cloud cover effects (random dips during daylight)
        # Cloud events are autocorrelated
        cloud_factor = np.ones(n_points)
        cloud_state = 1.0  # 1.0 = clear, 0.3 = cloudy
        for i in range(n_points):
            if is_daylight[i]:
                # Random transition probability
                if cloud_state > 0.5:  # Currently clear
                    if self.rng.random() < 0.02:  # 2% chance of clouds
                        cloud_state = 0.3 + self.rng.random() * 0.4
                else:  # Currently cloudy
                    if self.rng.random() < 0.05:  # 5% chance of clearing
                        cloud_state = 0.9 + self.rng.random() * 0.1
            cloud_factor[i] = cloud_state

        values *= cloud_factor

        # Add small random noise
        noise = self.rng.normal(0, 0.02 * base_capacity, size=n_points)
        values = values + noise * (irradiance > 0)

        return values

    def _generate_variable_noise(
        self,
        n_points: int,
        base_noise_std: float,
        daily_variation: float,
        monthly_drift: float,
        forecaster_seed_offset: int = 0,
    ) -> np.ndarray:
        """Generate time-varying noise for variable archetype.

        Creates noise that varies both day-to-day and month-to-month to simulate
        realistic forecaster skill variation:
        - Daily variation: Some days the forecaster performs better/worse
        - Monthly drift: Overall skill level shifts from month to month

        :param n_points: Total number of data points to generate
        :param base_noise_std: Average noise level (standard deviation)
        :param daily_variation: Std of daily noise multiplier (higher = more day-to-day variation)
        :param monthly_drift: Std of monthly multiplier (higher = more skill drift over time)
        :param forecaster_seed_offset: Offset for random seed to auto-stagger multiple forecasters
        :return: Array of noise values with time-varying standard deviation
        """
        # Use offset seed for this forecaster (auto-stagger)
        rng = np.random.default_rng(self.seed + forecaster_seed_offset * 1000)

        n_days = n_points // 96
        n_months = max(1, n_days // 30)

        # Generate monthly skill levels
        monthly_multipliers = 1 + rng.normal(0, monthly_drift, size=n_months)
        monthly_multipliers = np.maximum(monthly_multipliers, 0.2)  # Floor at 0.2x

        # Generate daily skill levels within each month
        daily_noise_stds = []
        for month_idx in range(n_months):
            days_in_month = min(30, n_days - month_idx * 30)
            monthly_base = base_noise_std * monthly_multipliers[month_idx]
            daily_multipliers = 1 + rng.normal(0, daily_variation, size=days_in_month)
            daily_multipliers = np.maximum(daily_multipliers, 0.2)
            daily_noise_stds.extend([monthly_base * dm for dm in daily_multipliers])

        # Handle any remaining days (partial month or rounding)
        while len(daily_noise_stds) < n_days:
            # Use the last monthly multiplier for remaining days
            last_monthly_base = base_noise_std * monthly_multipliers[-1]
            daily_mult = max(0.2, 1 + rng.normal(0, daily_variation))
            daily_noise_stds.append(last_monthly_base * daily_mult)

        # Generate noise for each timestep
        noise = np.zeros(n_points)
        for day_idx in range(min(len(daily_noise_stds), n_days)):
            daily_std = daily_noise_stds[day_idx]
            start_idx = day_idx * 96
            end_idx = min(start_idx + 96, n_points)
            noise[start_idx:end_idx] = rng.normal(
                0, daily_std, size=end_idx - start_idx
            )

        # Handle any remaining points (partial day)
        remaining_start = n_days * 96
        if remaining_start < n_points:
            last_std = daily_noise_stds[-1] if daily_noise_stds else base_noise_std
            noise[remaining_start:] = rng.normal(
                0, last_std, size=n_points - remaining_start
            )

        return noise

    def generate_forecaster(
        self,
        measurements: pd.DataFrame,
        archetype: str = "skilled",
        forecaster_id: str = "forecaster_1",
        forecaster_idx: int = 0,
    ) -> pd.DataFrame:
        """Generate synthetic forecaster predictions.

        Creates predictions based on the specified archetype configuration.
        Each archetype has predefined characteristics that determine forecast
        quality and behavior.

        Available archetypes:
        - skilled: Low noise, no bias, well-calibrated intervals
        - noisy: High random error, no systematic bias
        - biased: Systematic over-prediction (+10%)
        - biased_low: Systematic under-prediction (-10%)
        - lagged: Uses 6-hour old information
        - overconfident: Narrow prediction intervals (poor coverage)
        - underconfident: Wide prediction intervals (conservative)
        - adversarial: Inverted predictions (deliberately wrong)
        - intermittent: Randomly missing submissions (~15% dropout)
        - variable: Time-varying skill (daily fluctuations + monthly drift)
        - outlier: Occasionally produces outlier predictions (~10% of days)
        - regime_high: Excellent when output is high, poor when low
        - regime_low: Excellent when output is low, poor when high

        :param measurements: DataFrame with datetime and target columns
        :param archetype: Archetype name (see ARCHETYPE_CONFIGS)
        :param forecaster_id: Unique identifier for the forecaster
        :param forecaster_idx: Index of forecaster (used for auto-staggering variable archetype)
        :return: DataFrame with datetime and q10, q50, q90 columns
        """
        if archetype not in ARCHETYPE_CONFIGS:
            logger.warning(
                f"Unknown archetype '{archetype}'. Using 'skilled' as default."
            )
            archetype = "skilled"

        # Get config with diversity-based parameter variation
        config = self._get_varied_config(archetype, forecaster_idx)
        truth = measurements["target"].values.copy()
        n_points = len(truth)

        # Apply lag if specified
        if config.get("lag_hours", 0) > 0:
            lag_points = config["lag_hours"] * 4  # 4 points per hour
            lagged_truth = np.roll(truth, lag_points)
            # Fill first lag_points with first value to avoid edge effects
            lagged_truth[:lag_points] = truth[:lag_points]
            truth = lagged_truth

        # Generate Q50 (point forecast)
        # Handle variable archetype with time-varying noise
        if archetype == "variable":
            noise = self._generate_variable_noise(
                n_points=n_points,
                base_noise_std=config["base_noise_std"],
                daily_variation=config["daily_variation"],
                monthly_drift=config["monthly_drift"],
                forecaster_seed_offset=forecaster_idx,
            )
            q50 = truth * (1 + config.get("bias", 0.0) + noise)
        elif archetype in ("regime_high", "regime_low"):
            # Regime-dependent noise and bias: good in one regime, bad in the other
            threshold = np.percentile(truth, config["threshold_percentile"])

            # Determine which regime is "good" for this archetype
            if archetype == "regime_high":
                good_regime = truth >= threshold
            else:  # regime_low
                good_regime = truth < threshold

            # Generate noise with regime-dependent std
            noise = np.zeros(n_points)
            n_good = good_regime.sum()
            n_bad = (~good_regime).sum()
            noise[good_regime] = self.rng.normal(
                0, config["noise_std_good"], size=n_good
            )
            noise[~good_regime] = self.rng.normal(
                0, config["noise_std_bad"], size=n_bad
            )

            # Generate regime-dependent bias
            bias = np.zeros(n_points)
            bias[good_regime] = config.get("bias_good", 0.0)
            bias[~good_regime] = config.get("bias_bad", 0.0)

            # Apply noise and bias
            q50 = truth * (1 + bias + noise)
        else:
            noise = self.rng.normal(0, config["noise_std"], size=n_points)
            q50 = truth * (1 + config.get("bias", 0.0) + noise)

        # Invert if adversarial
        if config.get("invert", False):
            # Invert around the mean
            mean_val = truth.mean()
            q50 = 2 * mean_val - q50

        # Generate prediction intervals (Q10, Q90)
        # Base interval width proportional to forecast uncertainty
        base_interval_width = 0.15 * truth  # ~15% of truth as base width
        scaled_width = base_interval_width * config.get("interval_scale", 1.0)

        # Add some randomness to interval width
        interval_noise = self.rng.normal(1.0, 0.1, size=n_points)
        scaled_width = scaled_width * np.abs(interval_noise)

        q10 = q50 - scaled_width
        q90 = q50 + scaled_width

        # Apply dropout if intermittent
        if config.get("dropout_prob", 0) > 0:
            # Generate dropout mask at daily level
            n_days = n_points // 96
            dropout_days = self.rng.random(n_days) < config["dropout_prob"]
            dropout_mask = np.repeat(dropout_days, 96)
            # Truncate or pad to match n_points
            dropout_mask = dropout_mask[:n_points]

            q10 = np.where(dropout_mask, np.nan, q10)
            q50 = np.where(dropout_mask, np.nan, q50)
            q90 = np.where(dropout_mask, np.nan, q90)

        # Apply outliers if configured
        if config.get("outlier_prob", 0) > 0:
            n_days = n_points // 96
            outlier_prob = config["outlier_prob"]
            outlier_magnitude = config.get("outlier_magnitude", 3.0)

            # Determine which days are outliers
            outlier_days = self.rng.random(n_days) < outlier_prob

            # Generate random direction for each outlier day (+1 or -1)
            outlier_directions = self.rng.choice([-1, 1], size=n_days)

            # Apply outlier deviation to each outlier day
            for day_idx in range(n_days):
                if outlier_days[day_idx]:
                    start_idx = day_idx * 96
                    end_idx = min(start_idx + 96, n_points)
                    day_slice = slice(start_idx, end_idx)

                    # Calculate outlier offset based on truth values for that day
                    day_truth = truth[day_slice]
                    outlier_offset = (
                        outlier_directions[day_idx]
                        * outlier_magnitude
                        * day_truth.mean()
                    )

                    # Apply offset to all quantiles
                    q10[day_slice] = q10[day_slice] + outlier_offset
                    q50[day_slice] = q50[day_slice] + outlier_offset
                    q90[day_slice] = q90[day_slice] + outlier_offset

        # Ensure physical constraints
        q10 = np.maximum(q10, 0)
        q50 = np.maximum(q50, 0)
        q90 = np.maximum(q90, 0)

        # Ensure q10 <= q50 <= q90
        q10 = np.minimum(q10, q50)
        q90 = np.maximum(q90, q50)

        df = pd.DataFrame(
            {
                "datetime": measurements["datetime"],
                f"{forecaster_id}_q10": q10,
                f"{forecaster_id}_q50": q50,
                f"{forecaster_id}_q90": q90,
            }
        )

        return df

    def _parse_archetypes_spec(
        self,
        archetypes: str | None,
        n_forecasters: int,
    ) -> list[tuple[str, str]]:
        """Parse archetype specification string.

        :param archetypes: Specification like "skilled:2,noisy:2,biased:1"
        :param n_forecasters: Total number of forecasters (used as fallback)
        :return: List of (forecaster_id, archetype) tuples
        """
        if not archetypes:
            # Default: all skilled
            return [(f"s{i + 1}", "skilled") for i in range(n_forecasters)]

        result = []
        forecaster_idx = 1

        for spec in archetypes.split(","):
            spec = spec.strip()
            if ":" in spec:
                archetype_name, count_str = spec.split(":", 1)
                count = int(count_str.strip())
            else:
                archetype_name = spec
                count = 1

            archetype_name = archetype_name.strip().lower()
            if archetype_name not in ARCHETYPE_CONFIGS:
                logger.warning(
                    f"Unknown archetype '{archetype_name}'. Using 'skilled'."
                )
                archetype_name = "skilled"

            for _ in range(count):
                result.append((f"s{forecaster_idx}", archetype_name))
                forecaster_idx += 1

        return result

    def _apply_scenario(
        self,
        measurements: pd.DataFrame,
        forecasters_df: pd.DataFrame,
        scenario: str,
        **kwargs: Any,
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Apply a scenario template to modify the generated data.

        Available scenarios:
        - regime_change: Forecaster performance changes at a specific point
        - dropout: Some forecasters stop participating at specific dates
        - distribution_shift: Underlying data distribution changes

        :param measurements: Original measurements DataFrame
        :param forecasters_df: Original forecasters DataFrame
        :param scenario: Scenario name
        :param kwargs: Scenario-specific parameters
        :return: Modified (measurements, forecasters_df) tuple
        """
        if scenario == "regime_change":
            return self._apply_regime_change(measurements, forecasters_df, **kwargs)
        elif scenario == "dropout":
            return self._apply_dropout(measurements, forecasters_df, **kwargs)
        elif scenario == "distribution_shift":
            return self._apply_distribution_shift(
                measurements, forecasters_df, **kwargs
            )
        else:
            logger.warning(f"Unknown scenario '{scenario}'. No changes applied.")
            return measurements, forecasters_df

    def _apply_regime_change(
        self,
        measurements: pd.DataFrame,
        forecasters_df: pd.DataFrame,
        change_point: str | None = None,
        affected_forecasters: list[str] | None = None,
        new_noise_multiplier: float = 3.0,
        **kwargs: Any,
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Apply regime change scenario.

        After change_point, specified forecasters become much noisier,
        simulating a change in their model's validity.

        :param measurements: Original measurements
        :param forecasters_df: Original forecasters predictions
        :param change_point: Date when regime change occurs (ISO format)
        :param affected_forecasters: List of forecaster IDs to affect
        :param new_noise_multiplier: Factor to multiply noise by after change
        :return: Modified (measurements, forecasters_df) tuple
        """
        if change_point is None:
            # Default to middle of dataset
            mid_idx = len(measurements) // 2
            change_point = str(measurements["datetime"].iloc[mid_idx].date())

        change_ts = pd.Timestamp(change_point)
        after_change = forecasters_df["datetime"] >= change_ts

        if affected_forecasters is None:
            # Affect the first forecaster by default
            cols = [c for c in forecasters_df.columns if c != "datetime"]
            if cols:
                first_id = cols[0].rsplit("_", 1)[0]
                affected_forecasters = [first_id]
            else:
                affected_forecasters = []

        # Add extra noise to affected forecasters after change point
        for fid in affected_forecasters:
            for q in ["q10", "q50", "q90"]:
                col = f"{fid}_{q}"
                if col in forecasters_df.columns:
                    values = forecasters_df[col].values
                    truth = measurements["target"].values
                    extra_noise = self.rng.normal(
                        0, 0.15 * new_noise_multiplier, size=len(values)
                    )
                    values[after_change] = (
                        values[after_change]
                        + truth[after_change] * extra_noise[after_change]
                    )
                    forecasters_df[col] = np.maximum(values, 0)

        logger.info(
            f"Applied regime_change scenario at {change_point} "
            f"affecting {affected_forecasters}"
        )
        return measurements, forecasters_df

    def _apply_dropout(
        self,
        measurements: pd.DataFrame,
        forecasters_df: pd.DataFrame,
        dropout_schedule: dict[str, list[str]] | None = None,
        **kwargs: Any,
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Apply dropout scenario.

        Forecasters stop submitting after their dropout date.

        :param measurements: Original measurements
        :param forecasters_df: Original forecasters predictions
        :param dropout_schedule: Dict mapping dates to list of forecaster IDs
            Example: {"2023-01-20": ["s2", "s3"]}
        :return: Modified (measurements, forecasters_df) tuple
        """
        if dropout_schedule is None:
            # Default: one forecaster drops out at 2/3 of the dataset
            cols = [c for c in forecasters_df.columns if c != "datetime"]
            if cols:
                first_id = cols[0].rsplit("_", 1)[0]
                dropout_idx = int(len(measurements) * 2 / 3)
                dropout_date = str(measurements["datetime"].iloc[dropout_idx].date())
                dropout_schedule = {dropout_date: [first_id]}
            else:
                dropout_schedule = {}

        for dropout_date, forecaster_ids in dropout_schedule.items():
            dropout_ts = pd.Timestamp(dropout_date)
            after_dropout = forecasters_df["datetime"] >= dropout_ts

            for fid in forecaster_ids:
                for q in ["q10", "q50", "q90"]:
                    col = f"{fid}_{q}"
                    if col in forecasters_df.columns:
                        forecasters_df.loc[after_dropout, col] = np.nan

            logger.info(f"Applied dropout at {dropout_date} for {forecaster_ids}")

        return measurements, forecasters_df

    def _apply_distribution_shift(
        self,
        measurements: pd.DataFrame,
        forecasters_df: pd.DataFrame,
        shift_point: str | None = None,
        mean_offset: float = 100.0,
        variance_multiplier: float = 1.5,
        **kwargs: Any,
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Apply distribution shift scenario.

        After shift_point, the underlying measurements distribution changes,
        but forecasters don't adapt immediately.

        :param measurements: Original measurements
        :param forecasters_df: Original forecasters predictions
        :param shift_point: Date when distribution shifts (ISO format)
        :param mean_offset: Offset to add to mean after shift
        :param variance_multiplier: Factor to multiply variance by
        :return: Modified (measurements, forecasters_df) tuple
        """
        if shift_point is None:
            # Default to middle of dataset
            mid_idx = len(measurements) // 2
            shift_point = str(measurements["datetime"].iloc[mid_idx].date())

        shift_ts = pd.Timestamp(shift_point)
        after_shift = measurements["datetime"] >= shift_ts

        # Shift measurements
        shifted_values = measurements["target"].values.copy()

        # Add mean offset and increase variance
        after_shift_mask = after_shift.values
        noise = self.rng.normal(
            0, variance_multiplier - 1.0, size=after_shift_mask.sum()
        )
        shifted_values[after_shift_mask] = (
            shifted_values[after_shift_mask]
            + mean_offset
            + shifted_values[after_shift_mask] * noise * 0.1
        )
        measurements["target"] = np.maximum(shifted_values, 0)

        logger.info(
            f"Applied distribution_shift at {shift_point}: "
            f"offset={mean_offset}, variance_mult={variance_multiplier}"
        )
        return measurements, forecasters_df

    def generate_dataset(
        self,
        name: str,
        n_forecasters: int = 5,
        n_days: int = 30,
        archetypes: str | None = None,
        scenario: str | None = None,
        base_capacity: float = 1000.0,
        start_date: str = "2023-01-15",
        output_dir: str | None = None,
        plot: bool = False,
        **scenario_kwargs: Any,
    ) -> Path:
        """Generate a complete synthetic dataset.

        Creates a dataset directory with:
        - config.json: Dataset configuration
        - measurements.csv: Synthetic power measurements
        - forecasts.csv: Synthetic forecaster predictions
        - generation_log.json: Full generation metadata for reproducibility

        :param name: Dataset name (will be directory name)
        :param n_forecasters: Number of forecasters to generate (default: 5)
        :param n_days: Number of days of data (default: 30)
        :param archetypes: Forecaster archetype specification
            Format: "archetype:count,archetype:count,..."
            Example: "skilled:2,noisy:2,biased:1"
            If not specified, all forecasters will be "skilled"
        :param scenario: Optional scenario template to apply:
            - "regime_change": Performance changes mid-dataset
            - "dropout": Some forecasters stop participating
            - "distribution_shift": Data distribution changes
        :param base_capacity: Base power capacity in MW (default: 1000)
        :param start_date: Start date in YYYY-MM-DD format (default: "2023-01-15")
        :param output_dir: Custom output directory (default: input/)
        :param plot: Display plot of individual forecasts vs observed (default: False)
        :param scenario_kwargs: Additional parameters for the scenario
        :return: Path to the created dataset directory

        :Example:
            >>> generator = SyntheticGenerator(seed=42)
            >>> path = generator.generate_dataset(
            ...     name="mixed_skill",
            ...     n_forecasters=5,
            ...     archetypes="skilled:2,noisy:2,biased:1",
            ... )

            >>> # With regime change scenario
            >>> path = generator.generate_dataset(
            ...     name="regime_test",
            ...     scenario="regime_change",
            ...     change_point="2023-02-01",
            ... )
        """
        # Determine output path
        if output_dir:
            datasets_dir = Path(output_dir)
        else:
            # Default to input/ directory in community examples
            datasets_dir = Path(__file__).parent.parent / "input"

        dataset_path = datasets_dir / name

        if dataset_path.exists():
            logger.warning(f"Dataset already exists: {dataset_path}")
            logger.info("Remove it first or use a different name.")
            return dataset_path

        logger.info("=" * 60)
        logger.info(f"Generating synthetic dataset: {name}")
        logger.info("=" * 60)
        logger.info(f"Seed: {self.seed}")
        logger.info(f"Use case: {self.use_case}")
        logger.info(f"Days: {n_days}, Forecasters: {n_forecasters}")

        # Create dataset directory
        dataset_path.mkdir(parents=True, exist_ok=True)

        # Generate measurements
        logger.info("Generating measurements...")
        measurements = self.generate_measurements(
            n_days=n_days,
            base_capacity=base_capacity,
            start_date=start_date,
        )

        # Parse archetype specification
        forecaster_specs = self._parse_archetypes_spec(archetypes, n_forecasters)
        logger.info(f"Forecaster archetypes: {forecaster_specs}")

        # Generate forecasters
        logger.info("Generating forecaster predictions...")
        forecasters_dfs = []
        archetype_info = []

        for idx, (forecaster_id, archetype) in enumerate(forecaster_specs):
            # Get the varied config for this forecaster (for logging/metadata)
            varied_config = self._get_varied_config(archetype, idx)

            forecaster_df = self.generate_forecaster(
                measurements=measurements,
                archetype=archetype,
                forecaster_id=forecaster_id,
                forecaster_idx=idx,
            )
            # Keep only forecast columns (not datetime which will be merged)
            forecast_cols = [c for c in forecaster_df.columns if c != "datetime"]
            forecasters_dfs.append(forecaster_df[forecast_cols])

            # Store varied config (excluding *_range keys for cleaner output)
            config_for_log = {
                k: v for k, v in varied_config.items() if not k.endswith("_range")
            }
            archetype_info.append(
                {
                    "forecaster_id": forecaster_id,
                    "archetype": archetype,
                    "config": config_for_log,
                }
            )

        # Combine all forecasters
        forecasts = pd.concat([measurements[["datetime"]]] + forecasters_dfs, axis=1)

        # Apply scenario if specified
        scenario_params = {}
        if scenario:
            logger.info(f"Applying scenario: {scenario}")
            scenario_params = scenario_kwargs
            measurements, forecasts = self._apply_scenario(
                measurements, forecasts, scenario, **scenario_kwargs
            )

        # Save config.json
        config = {
            "timezone": "UTC",
            "use_case": self.use_case,
            "synthetic": True,
            "seed": self.seed,
            "diversity": self.diversity,
        }
        config_path = dataset_path / "config.json"
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
        logger.info(f"Saved: {config_path.name}")

        # Save measurements.csv
        measurements_path = dataset_path / "measurements.csv"
        measurements["datetime"] = measurements["datetime"].dt.strftime(
            "%Y-%m-%d %H:%M"
        )
        measurements.to_csv(measurements_path, index=False)
        logger.info(f"Saved: {measurements_path.name} ({len(measurements)} rows)")

        # Save forecasts.csv
        forecasts_path = dataset_path / "forecasts.csv"
        forecasts["datetime"] = forecasts["datetime"].dt.strftime("%Y-%m-%d %H:%M")
        forecasts.to_csv(forecasts_path, index=False)
        logger.info(f"Saved: {forecasts_path.name} ({len(forecasts)} rows)")

        # Save generation metadata
        metadata = GenerationMetadata(
            seed=self.seed,
            use_case=self.use_case,
            n_days=n_days,
            n_forecasters=len(forecaster_specs),
            forecaster_archetypes=archetype_info,
            scenario=scenario,
            scenario_params=scenario_params,
            generation_time=datetime.utcnow().isoformat() + "Z",
            data_start=start_date,
            data_end=str(
                (pd.Timestamp(start_date) + pd.Timedelta(days=n_days - 1)).date()
            ),
            diversity=self.diversity,
            extra_params={
                "base_capacity": base_capacity,
            },
        )

        metadata_path = dataset_path / "generation_log.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata.to_dict(), f, indent=2)
        logger.info(f"Saved: {metadata_path.name}")

        logger.success(f"Dataset created: {dataset_path}")
        logger.info("\nTo run a simulation with this dataset:")
        logger.info(f"  python simulate.py run --dataset={name}")

        # Plot individual forecasts vs observed if requested
        if plot:
            self.plot_generated_data(measurements, forecasts, forecaster_specs)

        return dataset_path

    def plot_generated_data(
        self,
        measurements: pd.DataFrame,
        forecasts: pd.DataFrame,
        forecaster_specs: list[tuple[str, str]],
    ) -> None:
        """Plot generated individual forecasts vs observed measurements.

        Creates a visualization showing:
        - Observed measurements (black line)
        - Individual forecaster Q50 predictions (colored lines)
        - Optional: Q10-Q90 prediction intervals as shaded bands

        :param measurements: DataFrame with datetime and target columns
        :param forecasts: DataFrame with datetime and forecaster columns
        :param forecaster_specs: List of (forecaster_id, archetype) tuples
        """
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            logger.warning(
                "matplotlib is required for plotting. "
                "Install with: pip install matplotlib"
            )
            return

        # Color palette for forecasters
        colors = [
            "#e74c3c",
            "#3498db",
            "#2ecc71",
            "#f39c12",
            "#9b59b6",
            "#1abc9c",
            "#e67e22",
            "#34495e",
            "#16a085",
            "#c0392b",
            "#8e44ad",
            "#27ae60",
            "#d35400",
            "#2980b9",
            "#f1c40f",
        ]

        # Parse datetime if string
        if measurements["datetime"].dtype == object:
            measurements = measurements.copy()
            measurements["datetime"] = pd.to_datetime(measurements["datetime"])
        if forecasts["datetime"].dtype == object:
            forecasts = forecasts.copy()
            forecasts["datetime"] = pd.to_datetime(forecasts["datetime"])

        fig, ax = plt.subplots(figsize=(14, 7))

        # Plot observed measurements
        ax.plot(
            measurements["datetime"],
            measurements["target"],
            color="#2c3e50",
            linewidth=2,
            label="Observed",
            zorder=10,
        )

        # Plot each forecaster
        for i, (forecaster_id, archetype) in enumerate(forecaster_specs):
            color = colors[i % len(colors)]
            q50_col = f"{forecaster_id}_q50"
            q10_col = f"{forecaster_id}_q10"
            q90_col = f"{forecaster_id}_q90"

            if q50_col in forecasts.columns:
                # Plot Q50 line
                ax.plot(
                    forecasts["datetime"],
                    forecasts[q50_col],
                    color=color,
                    linewidth=1,
                    alpha=0.7,
                    label=f"{forecaster_id} ({archetype})",
                )

                # Plot prediction interval as shaded band
                if q10_col in forecasts.columns and q90_col in forecasts.columns:
                    ax.fill_between(
                        forecasts["datetime"],
                        forecasts[q10_col],
                        forecasts[q90_col],
                        color=color,
                        alpha=0.1,
                    )

        ax.set_xlabel("Date")
        ax.set_ylabel("Power (MW)")
        ax.set_title("Generated Dataset: Individual Forecasts vs Observed")
        ax.legend(loc="upper right", fontsize=8)
        ax.grid(True, alpha=0.3)

        # Rotate x-axis labels
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha="right")

        fig.tight_layout()
        plt.show()

    @staticmethod
    def list_archetypes() -> dict[str, str]:
        """List available forecaster archetypes with descriptions.

        :return: Dictionary mapping archetype names to descriptions
        """
        return {
            name: config["description"] for name, config in ARCHETYPE_CONFIGS.items()
        }
