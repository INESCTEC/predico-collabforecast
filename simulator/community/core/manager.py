"""
Simulator Manager for orchestrating forecast simulations.

This module provides the SimulatorManager class which handles:
- Session scheduling and lifecycle management
- Report generation and persistence
- Logging configuration

Example:
    >>> from core import SimulatorManager, SimulatorConfig
    >>> config = SimulatorConfig(
    ...     dataset_path="input/example_elia",
    ...     n_sessions=10,
    ...     first_launch_time="2023-02-15T10:30:00Z",
    ... )
    >>> manager = SimulatorManager(config)
    >>> for session_id, launch_time in manager.sessions:
    ...     # Run simulation for each session
    ...     pass
    >>> manager.save_reports()
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from loguru import logger


@dataclass
class SimulatorConfig:
    """Configuration for SimulatorManager.

    :param dataset_path: Path to the dataset directory containing:
        - measurements.csv
        - forecasts.csv
        - buyers_resources.json
        - sellers_resources.json
    :param n_sessions: Number of market sessions to simulate
    :param first_launch_time: First session launch time in ISO format (UTC)
        Example: "2023-02-15T10:30:00Z"
    :param session_freq_hours: Hours between consecutive sessions (default: 24)
    :param datetime_format: Format string for parsing datetime columns
    :param csv_delimiter: Delimiter used in CSV files
    :param output_dir: Directory for reports (default: auto-generated in output/)
    :param report_suffix: Optional suffix for report directory name
    """

    dataset_path: str
    n_sessions: int
    first_launch_time: str
    session_freq_hours: int = 24
    datetime_format: str = "%Y-%m-%d %H:%M"
    csv_delimiter: str = ","
    output_dir: str | None = None
    report_suffix: str | None = None

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if self.n_sessions < 1:
            raise ValueError("n_sessions must be at least 1")
        if self.session_freq_hours < 1:
            raise ValueError("session_freq_hours must be at least 1")

        # Validate dataset path exists
        if not os.path.isdir(self.dataset_path):
            raise FileNotFoundError(f"Dataset path not found: {self.dataset_path}")

        # Validate first_launch_time format
        try:
            datetime.strptime(self.first_launch_time, "%Y-%m-%dT%H:%M:%SZ")
        except ValueError as e:
            raise ValueError(
                f"Invalid first_launch_time format. Expected ISO format "
                f"(e.g., '2023-02-15T10:30:00Z'): {e}"
            ) from e


class SimulatorManager:
    """Manages simulation lifecycle, reporting, and logging.

    The SimulatorManager orchestrates the simulation process by:
    1. Creating a schedule of market sessions based on configuration
    2. Setting up logging and report directories
    3. Collecting and persisting simulation results

    :param config: SimulatorConfig instance with simulation parameters

    Example:
        >>> config = SimulatorConfig(
        ...     dataset_path="input/example_elia",
        ...     n_sessions=5,
        ...     first_launch_time="2023-02-15T10:30:00Z",
        ... )
        >>> manager = SimulatorManager(config)
        >>> print(f"Running {len(manager.sessions)} sessions")
        >>> for session_id, launch_time in manager.sessions:
        ...     print(f"Session {session_id}: {launch_time}")
    """

    def __init__(self, config: SimulatorConfig) -> None:
        """Initialize the simulator manager.

        :param config: Configuration object with simulation parameters
        """
        self.config = config
        self._dataset_name = os.path.basename(config.dataset_path)
        self._sellers_resources: list[dict] | None = None
        self._sellers_forecasts: dict[str, dict] | None = None
        self._session_reports: dict[int, dict[str, Any]] = {}

        # Initialize components
        self._setup_output_directory()
        self._setup_logger()
        self._create_session_schedule()
        self._init_report_templates()

    @property
    def dataset_path(self) -> str:
        """Return the dataset path."""
        return self.config.dataset_path

    @property
    def dataset_name(self) -> str:
        """Return the dataset name (directory basename)."""
        return self._dataset_name

    @property
    def datetime_format(self) -> str:
        """Return the datetime format string."""
        return self.config.datetime_format

    @property
    def csv_delimiter(self) -> str:
        """Return the CSV delimiter."""
        return self.config.csv_delimiter

    @property
    def output_path(self) -> str:
        """Return the output/reports directory path."""
        return self._output_path

    @property
    def sessions(self) -> list[tuple[int, pd.Timestamp]]:
        """Return list of (session_id, launch_time) tuples."""
        return self._sessions

    def set_sellers_resources(self, sellers_resources: list[dict]) -> None:
        """Store seller resources metadata for reporting.

        :param sellers_resources: List of seller resource dictionaries
        """
        self._sellers_resources = sellers_resources

    def set_sellers_forecasts(self, sellers_forecasts: dict[str, dict]) -> None:
        """Store seller forecasts for submission tracking.

        :param sellers_forecasts: Nested dict {seller -> {resource -> {variable -> DataFrame}}}
        """
        self._sellers_forecasts = sellers_forecasts

    def _setup_output_directory(self) -> None:
        """Create the output directory for reports."""
        if self.config.output_dir:
            self._output_path = self.config.output_dir
        else:
            # Auto-generate output directory
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            dirname = timestamp
            if self.config.report_suffix:
                dirname = f"{timestamp}_{self.config.report_suffix}"

            # Get the community examples root directory
            examples_root = Path(__file__).parent.parent
            self._output_path = str(
                examples_root / "output" / self._dataset_name / dirname
            )

        os.makedirs(self._output_path, exist_ok=True)

    def _setup_logger(self) -> None:
        """Configure loguru logger with file output."""
        log_format = "{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {message}"
        log_path = os.path.join(self._output_path, "simulation.log")

        # Add file handler
        logger.add(
            log_path,
            format=log_format,
            level="INFO",
            backtrace=True,
            diagnose=True,
        )
        logger.info("=" * 79)
        logger.info(f"Simulation started - Output: {self._output_path}")
        logger.info(f"Dataset: {self._dataset_name}")
        logger.info(f"Sessions: {self.config.n_sessions}")

    def _create_session_schedule(self) -> None:
        """Create the list of session launch times."""
        first_lt = datetime.strptime(
            self.config.first_launch_time, "%Y-%m-%dT%H:%M:%SZ"
        )

        # Generate launch times
        launch_times = pd.date_range(
            start=first_lt,
            periods=self.config.n_sessions,
            freq=f"{self.config.session_freq_hours}h",
        )

        self._sessions = [(i, lt) for i, lt in enumerate(launch_times)]

    def _init_report_templates(self) -> None:
        """Initialize report data structures."""
        for session_id, _ in self._sessions:
            self._session_reports[session_id] = {}

        # Define expected columns for sessions.csv
        self._session_columns = [
            "session_id",
            "launch_time",
            "target_day",
            "forecast_start",
            "forecast_end",
            "n_forecasters",
            "elapsed_time",
        ]

    def add_session_report(
        self,
        session_id: int,
        session_lt: pd.Timestamp,
        session_details: dict[str, Any],
        buyers_results: dict[str, Any],
        buyers_forecasts: dict[str, Any],
        elapsed_time: float = 0.0,
    ) -> None:
        """Add results from a completed session.

        :param session_id: The session identifier
        :param session_lt: Session launch timestamp
        :param session_details: Session metadata dictionary
        :param buyers_results: Dictionary of buyer results
        :param buyers_forecasts: Dictionary of buyer forecasts by resource
        :param elapsed_time: Time taken to process session (seconds)
        """
        report = {
            "session_data": {},
            "buyers_forecasts": [],
            "submissions": [],
        }

        # Build simplified session data
        session_data = {
            "session_id": session_id,
            "launch_time": session_lt,
            "elapsed_time": elapsed_time,
        }

        # Extract target_day, forecast_start, forecast_end from challenges
        if "challenges" in session_details and session_details["challenges"]:
            challenge = session_details["challenges"][0]
            start_dt = challenge.get("start_datetime", "")
            end_dt = challenge.get("end_datetime", "")
            session_data["forecast_start"] = start_dt
            session_data["forecast_end"] = end_dt

            # Derive target_day from forecast_end (the day being forecasted)
            # For D+1 forecasts, forecast period ends at 22:45 on the target day
            if end_dt:
                try:
                    end_parsed = pd.to_datetime(end_dt)
                    session_data["target_day"] = end_parsed.strftime("%Y-%m-%d")
                except (ValueError, TypeError):
                    session_data["target_day"] = ""
            else:
                session_data["target_day"] = ""
        else:
            session_data["target_day"] = ""
            session_data["forecast_start"] = ""
            session_data["forecast_end"] = ""

        # Count forecasters from sellers_resources
        n_forecasters = 0
        if self._sellers_resources:
            n_forecasters = len(self._sellers_resources)
        session_data["n_forecasters"] = n_forecasters

        report["session_data"] = session_data

        # Process buyer forecasts (all strategies)
        for resource_id, forecast_data in buyers_forecasts.items():
            strategies = forecast_data.get("strategies", {})
            for strategy_name, strategy_forecasts in strategies.items():
                forecasts = [
                    {
                        **f,
                        "session_id": session_id,
                        "strategy": strategy_name,
                    }
                    for f in strategy_forecasts
                ]
                report["buyers_forecasts"].extend(forecasts)

        # Process individual forecaster submissions
        if self._sellers_forecasts:
            # Get forecast period from challenges
            forecast_start = None
            forecast_end = None
            if "challenges" in session_details and session_details["challenges"]:
                challenge = session_details["challenges"][0]
                start_dt = challenge.get("start_datetime", "")
                end_dt = challenge.get("end_datetime", "")
                if start_dt:
                    forecast_start = pd.to_datetime(start_dt)
                if end_dt:
                    forecast_end = pd.to_datetime(end_dt)

            # Extract submissions from sellers_forecasts
            for seller_user, resources_dict in self._sellers_forecasts.items():
                for resource_id, variables_dict in resources_dict.items():
                    for variable, forecast_df in variables_dict.items():
                        if forecast_df.empty:
                            continue

                        # Filter to forecast period if available
                        filtered_df = forecast_df
                        if forecast_start is not None and forecast_end is not None:
                            try:
                                filtered_df = forecast_df.loc[
                                    forecast_start:forecast_end
                                ]
                            except KeyError:
                                # Index not in range, use available data
                                pass

                        # Add each row as a submission
                        for dt_idx, row in filtered_df.iterrows():
                            # Handle both "value" column and original column names
                            if "value" in row.index:
                                val = row["value"]
                            else:
                                val = row.iloc[0]  # Single-column DataFrame
                            report["submissions"].append(
                                {
                                    "session_id": session_id,
                                    "forecaster_id": seller_user,
                                    "datetime": dt_idx,
                                    "variable": variable,
                                    "value": val,
                                }
                            )

        self._session_reports[session_id] = report

    def save_reports(self) -> None:
        """Save all collected reports to CSV files.

        Creates the following files in the output directory:
        - sessions.csv: Simplified session metadata
        - forecasts.csv: Generated forecasts
        - submissions.csv: Individual forecaster submissions
        """
        all_sessions = []
        all_forecasts = []
        all_submissions = []

        for session_id, report in self._session_reports.items():
            if not report:
                continue

            # Session data
            if report.get("session_data"):
                all_sessions.append(report["session_data"])

            # Forecasts
            all_forecasts.extend(report.get("buyers_forecasts", []))

            # Submissions
            all_submissions.extend(report.get("submissions", []))

        # Standard datetime format (matches input format)
        dt_format = self.config.datetime_format

        # Write sessions.csv (simplified session metadata)
        if all_sessions:
            df = pd.DataFrame(all_sessions)
            # Reorder columns to match expected order
            cols = [c for c in self._session_columns if c in df.columns]
            extra_cols = [c for c in df.columns if c not in cols]
            df = df[cols + extra_cols]
            # Format datetime columns
            for col in ["launch_time", "forecast_start", "forecast_end"]:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col]).dt.strftime(dt_format)
            df.to_csv(os.path.join(self._output_path, "sessions.csv"), index=False)
            logger.info(f"Saved sessions.csv with {len(df)} sessions")

        # Write forecasts.csv
        if all_forecasts:
            df = pd.DataFrame(all_forecasts)
            # Format datetime column
            if "datetime" in df.columns:
                df["datetime"] = pd.to_datetime(df["datetime"]).dt.strftime(dt_format)
            df.to_csv(os.path.join(self._output_path, "forecasts.csv"), index=False)
            logger.info(f"Saved forecasts.csv with {len(df)} records")

        # Write submissions.csv (individual forecaster submissions)
        if all_submissions:
            df = pd.DataFrame(all_submissions)
            # Format datetime column
            if "datetime" in df.columns:
                df["datetime"] = pd.to_datetime(df["datetime"]).dt.strftime(dt_format)
            df.to_csv(os.path.join(self._output_path, "submissions.csv"), index=False)
            logger.info(f"Saved submissions.csv with {len(df)} records")

        logger.success(f"Reports saved to: {self._output_path}")

    def plot_results(
        self,
        resource_id: str | None = None,
        plot_individuals: bool = False,
    ) -> None:
        """Generate and display forecast visualization plots.

        Creates time-series plots comparing forecasts from different strategies
        against observed values, plus a metrics summary.

        :param resource_id: Optional resource ID to filter (default: first available)
        :param plot_individuals: If True, also plot individual forecaster
            submissions vs observed (default: False)

        Note:
            Requires matplotlib to be installed. Plots are displayed interactively.
        """

        from .plots import ForecastPlotter

        # Collect all forecasts from session reports
        all_forecasts = []
        all_submissions = []
        for session_id, report in self._session_reports.items():
            forecasts = report.get("buyers_forecasts", [])
            all_forecasts.extend(forecasts)
            submissions = report.get("submissions", [])
            all_submissions.extend(submissions)

        if not all_forecasts:
            logger.warning("No forecasts available for plotting")
            return

        forecasts_df = pd.DataFrame(all_forecasts)
        submissions_df = pd.DataFrame(all_submissions) if all_submissions else None

        # Default resource_id to "target" if not provided
        if resource_id is None:
            resource_id = "target"

        # Load observed data from dataset
        measurements_path = os.path.join(self.config.dataset_path, "measurements.csv")
        if not os.path.exists(measurements_path):
            logger.error(f"Measurements file not found: {measurements_path}")
            return

        observed_df = pd.read_csv(measurements_path)
        observed_df["datetime"] = pd.to_datetime(
            observed_df["datetime"],
            format=self.config.datetime_format,
        )
        observed_df["datetime"] = observed_df["datetime"].dt.tz_localize("UTC")
        observed_df = observed_df.set_index("datetime")

        # Rename resource column to 'observed' if needed
        if resource_id and resource_id in observed_df.columns:
            observed_df = observed_df.rename(columns={resource_id: "observed"})

        logger.info(f"Plotting results for resource: {resource_id}")

        # Create plotter
        plotter = ForecastPlotter(forecasts_df, observed_df, resource_id)

        # Plot individual forecasters if requested
        if plot_individuals and submissions_df is not None and not submissions_df.empty:
            logger.info("Generating individual forecasters plot...")
            plotter.plot_forecaster_comparison(submissions_df)

        # Show all standard plots
        plotter.show_all()
