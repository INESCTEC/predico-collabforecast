"""
Agents Loader for loading simulation datasets.

This module provides the AgentsLoader class which handles loading:
- Dataset configuration from config.json (timezone, use_case)
- Buyer resource from measurements.csv 'target' column
- Seller resources (auto-derived from forecasts.csv column names: {seller}_{quantile})
- Historical measurements from CSV
- Forecaster predictions from CSV

Example:
    >>> from core import AgentsLoader
    >>> loader = AgentsLoader(
    ...     launch_time=datetime(2023, 2, 15, 10, 30),
    ...     data_path="input/example_elia",
    ... )
    >>> loader.load_datasets()
    >>> print(f"Loaded {len(loader.measurements)} resources")
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from loguru import logger

# Default time resolution for market data
DEFAULT_TIME_RESOLUTION = "15min"

# Type alias for the nested forecasts structure:
# {seller_user -> {resource_id -> {variable -> DataFrame}}}
ForecastsDict = dict[str, dict[str, dict[str, pd.DataFrame]]]


class AgentsLoader:
    """Loads and prepares datasets for simulation.

    The AgentsLoader handles:
    1. Loading resource metadata (buyers, sellers) from JSON
    2. Loading historical measurements (power generation data)
    3. Loading forecaster predictions
    4. Resampling data to consistent time resolution

    :param launch_time: Market session launch time
    :param data_path: Path to dataset directory
    :param datetime_format: Format string for datetime parsing
    :param csv_delimiter: Delimiter used in CSV files
    :param time_resolution: Time resolution for resampling (default: "15min")

    Example:
        >>> loader = AgentsLoader(
        ...     launch_time=datetime(2023, 2, 15, 10, 30),
        ...     data_path="input/example_elia",
        ... )
        >>> loader.load_datasets()
        >>> # Access loaded data
        >>> measurements = loader.measurements
        >>> forecasts = loader.forecasts
        >>> buyers = loader.buyers_resources
        >>> sellers = loader.sellers_resources
    """

    def __init__(
        self,
        launch_time: datetime,
        data_path: str,
        datetime_format: str = "%Y-%m-%d %H:%M",
        csv_delimiter: str = ",",
        time_resolution: str = DEFAULT_TIME_RESOLUTION,
    ) -> None:
        """Initialize the agents loader.

        :param launch_time: Market session launch time
        :param data_path: Path to dataset directory
        :param datetime_format: Format string for datetime parsing
        :param csv_delimiter: Delimiter used in CSV files
        :param time_resolution: Time resolution for resampling
        """
        self.launch_time = launch_time
        self.data_path = Path(data_path)
        self.datetime_format = datetime_format
        self.csv_delimiter = csv_delimiter
        self.time_resolution = time_resolution

        # Data containers
        self.buyers_resources: list[dict[str, Any]] = []
        self.sellers_resources: list[dict[str, Any]] = []
        self.measurements: dict[str, pd.DataFrame] = {}
        self.forecasts: ForecastsDict = {}

        # Derived attributes
        self._buyers_users: list[str] = []
        self._sellers_users: list[str] = []
        self._measurement_ids: list[str] = []

        self._validate_data_path()

    def _validate_data_path(self) -> None:
        """Validate that the data path exists and contains required files."""
        if not self.data_path.exists():
            raise FileNotFoundError(f"Dataset path not found: {self.data_path}")

        # Only config.json and measurements.csv are required
        # - Buyer resources are derived from measurements.csv columns
        # - Seller resources are derived from forecasts.csv columns
        required_files = [
            "config.json",
            "measurements.csv",
        ]

        missing = []
        for f in required_files:
            if not (self.data_path / f).exists():
                missing.append(f)

        if missing:
            raise FileNotFoundError(
                f"Missing required files in {self.data_path}: {missing}"
            )

    def _read_csv(self, filename: str) -> pd.DataFrame:
        """Read and preprocess a CSV file.

        :param filename: Name of CSV file (without path)
        :return: DataFrame with datetime index

        :raises FileNotFoundError: If the file doesn't exist
        """
        filepath = self.data_path / filename
        if not filepath.exists():
            logger.warning(f"File not found: {filepath}")
            return pd.DataFrame()

        df = pd.read_csv(filepath, sep=self.csv_delimiter)

        if "datetime" not in df.columns:
            raise ValueError(f"CSV file {filename} must have a 'datetime' column")

        # Parse datetime and set as index
        df["datetime"] = pd.to_datetime(df["datetime"], format=self.datetime_format)
        df["datetime"] = df["datetime"].dt.tz_localize("UTC")
        df = df.drop_duplicates("datetime")
        df = df.set_index("datetime")
        df = df.dropna(how="all")

        return df

    def _load_json(self, filename: str) -> list[dict[str, Any]]:
        """Load a JSON file.

        :param filename: Name of JSON file (without path)
        :return: Parsed JSON content
        """
        filepath = self.data_path / filename
        with open(filepath, "r") as f:
            return json.load(f)

    def _load_config(self) -> dict[str, str]:
        """Load dataset configuration from config.json.

        :return: Configuration dict with 'timezone' and 'use_case' keys

        :raises FileNotFoundError: If config.json doesn't exist
        :raises ValueError: If required fields are missing
        """
        filepath = self.data_path / "config.json"
        with open(filepath, "r") as f:
            config = json.load(f)

        # Validate required fields
        if "timezone" not in config:
            raise ValueError("config.json must contain 'timezone' field")
        if "use_case" not in config:
            raise ValueError("config.json must contain 'use_case' field")

        return config

    def _derive_buyers_from_measurements(
        self, config: dict[str, str]
    ) -> list[dict[str, Any]]:
        """Derive buyer resource from measurements.csv 'target' column.

        Expects measurements.csv to have a 'target' column containing
        the values being forecasted.

        :param config: Dataset configuration with 'timezone' and 'use_case'
        :return: List with single buyer resource dict
        """
        measurements_file = self.data_path / "measurements.csv"

        # Read just the header (nrows=0 reads only columns)
        df = pd.read_csv(measurements_file, nrows=0)

        # Check for 'target' column
        if "target" not in df.columns:
            raise ValueError(
                "measurements.csv must have a 'target' column "
                "(the values being forecasted)"
            )

        # Return single buyer resource with fixed 'target' ID
        return [
            {
                "user": "buyer",
                "id": "target",
                "timezone": config["timezone"],
                "use_case": config["use_case"],
            }
        ]

    @staticmethod
    def _parse_forecast_column(col_name: str) -> dict[str, str] | None:
        """Parse a forecast column name into seller and variable components.

        Expected format: {seller}_{quantile}
        where quantile is one of: q10, q50, q90

        :param col_name: Column name to parse
        :return: Dict with 'user', 'variable' keys, or None if invalid
        """
        # Split from right to get seller and quantile
        parts = col_name.rsplit("_", 1)
        if len(parts) != 2:
            return None

        seller, variable = parts
        if variable not in ("q10", "q50", "q90"):
            return None

        return {
            "user": seller,
            "variable": variable,
        }

    def _derive_sellers_from_forecasts(self) -> list[dict[str, Any]]:
        """Derive seller resources from forecasts.csv column names.

        Parses columns matching pattern: {seller}_{quantile}
        where quantile is one of: q10, q50, q90

        Uses fixed "target" resource since datasets are single-resource.

        :return: List of seller resource dicts
        """
        forecasts_file = self.data_path / "forecasts.csv"
        if not forecasts_file.exists():
            return []

        # Read just the header (nrows=0 reads only columns)
        df = pd.read_csv(forecasts_file, nrows=0)

        sellers = []
        for col in df.columns:
            if col == "datetime":
                continue
            parsed = self._parse_forecast_column(col)
            if parsed:
                sellers.append(
                    {
                        "user": parsed["user"],
                        "variable": parsed["variable"],
                        "market_session_challenge_resource_id": "target",
                    }
                )

        return sellers

    def load_resources(self) -> "AgentsLoader":
        """Load configuration and derive buyer/seller resources.

        Configuration is loaded from config.json.
        Buyers are derived from measurements.csv column names.
        Sellers are derived from forecasts.csv column names.

        :return: Self for method chaining
        """
        # Load config
        self._config = self._load_config()

        # Derive buyers from measurements columns + config
        self.buyers_resources = self._derive_buyers_from_measurements(self._config)

        # Derive sellers from forecasts.csv columns
        self.sellers_resources = self._derive_sellers_from_forecasts()

        # Extract derived values
        self._buyers_users = [r["user"] for r in self.buyers_resources]
        self._sellers_users = list(set(r["user"] for r in self.sellers_resources))
        self._measurement_ids = [r["id"] for r in self.buyers_resources]

        logger.info(
            f"Loaded config: timezone={self._config['timezone']}, "
            f"use_case={self._config['use_case']}"
        )
        logger.info(
            f"Derived {len(self.buyers_resources)} resources, "
            f"{len(self._sellers_users)} sellers"
        )

        return self

    def load_measurements(self) -> "AgentsLoader":
        """Load historical measurement data.

        Measurements are filtered to only include data before the launch time
        (historical data available at market session start).

        :return: Self for method chaining
        """
        if not self._measurement_ids:
            raise RuntimeError("Call load_resources() before load_measurements()")

        df = self._read_csv("measurements.csv")
        if df.empty:
            raise ValueError("Empty measurements dataset - cannot continue")

        # Resample to target resolution if needed
        inferred_freq = pd.infer_freq(df.index)
        if inferred_freq is None or inferred_freq != self.time_resolution:
            logger.info(f"Resampling measurements to {self.time_resolution}")
            df = df.resample(self.time_resolution).interpolate()

        # Filter to historical data only (before launch time)
        end_date = self.launch_time.strftime("%Y-%m-%d %H:%M:%S")

        for resource_id in self._measurement_ids:
            if resource_id not in df.columns:
                raise ValueError(
                    f"Resource '{resource_id}' not found in measurements.csv"
                )

            values = df.loc[:end_date, resource_id].dropna()
            if values.empty:
                raise ValueError(
                    f"No historical data for resource '{resource_id}' before {end_date}"
                )

            self.measurements[resource_id] = pd.DataFrame(
                {"datetime": values.index, "value": values.values}
            ).set_index("datetime")

        logger.info(f"Loaded measurements for {len(self.measurements)} resources")
        return self

    def load_forecasts(self, horizon_days: int = 3) -> "AgentsLoader":
        """Load forecaster predictions.

        :param horizon_days: Number of days ahead to load forecasts for
        :return: Self for method chaining
        """
        if not self.sellers_resources:
            raise RuntimeError("Call load_resources() before load_forecasts()")

        # Initialize forecast containers
        self.forecasts = {user: {} for user in self._sellers_users}

        # Calculate forecast end date
        end_date = (self.launch_time + pd.DateOffset(days=horizon_days)).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        # Try to load forecasts CSV
        filepath = self.data_path / "forecasts.csv"
        if not filepath.exists():
            logger.warning("No forecasts.csv found - using empty forecasts")
            return self

        df = self._read_csv("forecasts.csv")
        if df.empty:
            logger.warning("Empty forecasts dataset")
            return self

        # Process each seller resource
        for resource in self.sellers_resources:
            user = resource["user"]
            variable = resource["variable"]
            target_resource = resource["market_session_challenge_resource_id"]

            # Build expected column name: {seller}_{quantile}
            col_name = f"{user}_{variable}"

            if col_name not in df.columns:
                logger.warning(f"Forecast column not found: {col_name}")
                continue

            # Extract and resample forecasts
            forecast_series = df.loc[:end_date, col_name].dropna()
            if not forecast_series.empty:
                forecast_series = forecast_series.resample(
                    self.time_resolution
                ).interpolate()

            # Create DataFrame
            if forecast_series.empty:
                forecast_df = pd.DataFrame({"datetime": [], "value": []}).set_index(
                    "datetime"
                )
            else:
                forecast_df = pd.DataFrame(
                    {"datetime": forecast_series.index, "value": forecast_series.values}
                ).set_index("datetime")

            # Store in nested dictionary structure
            if target_resource not in self.forecasts[user]:
                self.forecasts[user][target_resource] = {}
            self.forecasts[user][target_resource][variable] = forecast_df

        logger.info(f"Loaded forecasts for {len(self._sellers_users)} sellers")
        return self

    def load_datasets(self) -> "AgentsLoader":
        """Load all datasets (resources, measurements, forecasts).

        This is a convenience method that calls all load methods in sequence.

        :return: Self for method chaining
        """
        self.load_resources()
        self.load_measurements()
        self.load_forecasts()
        return self

    def get_challenge_measurements(
        self,
        resource_ids: list[str],
        start_date: str | datetime,
        end_date: str | datetime,
    ) -> dict[str, pd.DataFrame]:
        """Load measurements for a specific date range (for evaluation).

        :param resource_ids: List of resource IDs to load
        :param start_date: Start of date range
        :param end_date: End of date range
        :return: Dictionary mapping resource_id to measurement DataFrame
        """
        df = self._read_csv("measurements.csv")
        if df.empty:
            raise ValueError("Empty measurements dataset")

        # Resample if needed
        inferred_freq = pd.infer_freq(df.index)
        if inferred_freq is None or inferred_freq != self.time_resolution:
            df = df.resample(self.time_resolution).interpolate()

        # Convert dates to strings if needed
        if isinstance(start_date, datetime):
            start_date = start_date.strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(end_date, datetime):
            end_date = end_date.strftime("%Y-%m-%d %H:%M:%S")

        measurements = {}
        for resource_id in resource_ids:
            if resource_id not in df.columns:
                raise ValueError(f"Resource '{resource_id}' not found in measurements")

            values = df.loc[start_date:end_date, resource_id].dropna()
            measurements[resource_id] = pd.DataFrame(
                {"datetime": values.index, "value": values.values}
            ).set_index("datetime")

        return measurements
