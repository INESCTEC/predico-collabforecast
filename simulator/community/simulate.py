#!/usr/bin/env python
"""
Forecast Simulator CLI.

A command-line interface for running standalone forecast simulations
without requiring API or database access.

Usage:
    python simulate.py run --dataset=example_elia --n_sessions=10
    python simulate.py list_datasets
    python simulate.py evaluate output/20250101_120000/
    python simulate.py create_dataset --name=my_dataset --template=example_elia

For help on any command:
    python simulate.py run --help
    python simulate.py --help
"""

from __future__ import annotations

import gc
import json
import shutil
import sys
from copy import deepcopy
from pathlib import Path
from time import time

import fire
import pandas as pd
from loguru import logger
from tqdm import tqdm

# Add parent directories to path for imports
# Use resolve() to get absolute path for cross-platform compatibility
_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# Import simulator components (supports both package and direct execution)
try:
    from core import (
        AgentsLoader,
        SessionGenerator,
        SimulatorConfig,
        SimulatorManager,
        SyntheticGenerator,
        metrics,
    )
except ImportError:
    from simulator.community.core import (  # type: ignore[import-not-found]
        AgentsLoader,
        SessionGenerator,
        SimulatorConfig,
        SimulatorManager,
        SyntheticGenerator,
        metrics,
    )

# Try to import MarketClass from forecast engine
try:
    from src.market import MarketClass

    MARKET_CLASS_AVAILABLE = True
except ImportError as e:
    import traceback

    MarketClass = None  # type: ignore[misc, assignment]
    MARKET_CLASS_AVAILABLE = False
    logger.warning(
        f"MarketClass not available: {e}\n"
        "Install forecast engine dependencies to run full simulations."
    )
    logger.debug(f"Import traceback:\n{traceback.format_exc()}")


def _configure_log_level(level: str) -> None:
    """Configure logging verbosity.

    :param level: Log level - "debug", "info", "warning", "error", or "quiet"
    """
    # Remove default handler
    logger.remove()

    # Map level names to loguru levels
    level_map = {
        "debug": "DEBUG",
        "info": "INFO",
        "warning": "WARNING",
        "error": "ERROR",
        "quiet": "ERROR",  # quiet = only errors
    }

    log_level = level_map.get(level.lower(), "INFO")

    # Add new handler with specified level
    logger.add(
        sys.stderr,
        level=log_level,
        format="<level>{time:YYYY-MM-DD HH:mm:ss.SSS}</level> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>",
        colorize=True,
    )


def _get_datasets_dir() -> Path:
    """Get the input directory path."""
    return Path(__file__).parent / "input"


def _get_output_dir() -> Path:
    """Get the output directory path."""
    return Path(__file__).parent / "output"


def _resolve_date_range(
    start_date: str | None,
    end_date: str | None,
    n_sessions: int | None,
    session_freq: int,
    first_valid: pd.Timestamp,
    last_valid: pd.Timestamp,
) -> tuple[str, int]:
    """Resolve date range from various input combinations.

    Handles these input scenarios (in order of precedence):
    - start_date + n_sessions: Use as-is
    - start_date + end_date: Calculate n_sessions between them
    - end_date + n_sessions: Calculate start_date backwards
    - start_date only: Run to end of dataset
    - end_date only: Run from start of dataset
    - None: Auto-detect full valid range

    :param start_date: First session launch time in ISO format (optional)
    :param end_date: Last session launch time in ISO format (optional)
    :param n_sessions: Number of sessions to simulate (optional)
    :param session_freq: Hours between sessions
    :param first_valid: Earliest valid start date from dataset
    :param last_valid: Latest valid start date from dataset
    :return: Tuple of (resolved_start_date, resolved_n_sessions)
    """
    session_hours = session_freq

    # Parse provided dates
    start_ts = pd.Timestamp(start_date) if start_date else None
    end_ts = pd.Timestamp(end_date) if end_date else None

    resolved_start = start_date
    resolved_n = n_sessions

    # Determine start_date and n_sessions based on what's provided
    if start_date and end_date:
        # Both dates provided: calculate n_sessions between them
        if resolved_n is None:
            total_hours = (end_ts - start_ts).total_seconds() / 3600
            resolved_n = max(1, int(total_hours // session_hours) + 1)
        logger.info(f"Using date range: {start_date} to {end_date}")

    elif start_date and n_sessions:
        # Start date + n_sessions: use as-is
        logger.info(f"Using start_date with {n_sessions} sessions")

    elif end_date and n_sessions:
        # End date + n_sessions: calculate start_date backwards
        start_ts = end_ts - pd.Timedelta(hours=session_hours * (n_sessions - 1))
        resolved_start = start_ts.strftime("%Y-%m-%dT%H:%M:%SZ")
        resolved_n = n_sessions
        logger.info(
            f"Calculated start_date: {resolved_start} "
            f"(from end_date - {n_sessions} sessions)"
        )

    elif start_date:
        # Only start_date: run to end of dataset
        if resolved_n is None:
            available_hours = (last_valid - start_ts).total_seconds() / 3600
            resolved_n = max(1, int(available_hours // session_hours))
        logger.info(f"Using start_date to end of dataset: {resolved_n} sessions")

    elif end_date:
        # Only end_date: run from start of dataset
        if resolved_n is None:
            available_hours = (end_ts - first_valid).total_seconds() / 3600
            resolved_n = max(1, int(available_hours // session_hours))
        start_ts = first_valid.replace(hour=10, minute=30, second=0, microsecond=0)
        resolved_start = start_ts.strftime("%Y-%m-%dT%H:%M:%SZ")
        logger.info(f"Using start of dataset to end_date: {resolved_n} sessions")

    else:
        # Nothing provided: auto-detect full range
        start_ts = first_valid.replace(hour=10, minute=30, second=0, microsecond=0)
        resolved_start = start_ts.strftime("%Y-%m-%dT%H:%M:%SZ")
        if resolved_n is None:
            available_hours = (last_valid - start_ts).total_seconds() / 3600
            resolved_n = max(1, int(available_hours // session_hours))
        logger.info(f"Auto-detected: {resolved_start}, {resolved_n} sessions")

    # Validate the calculated range fits within dataset
    final_start = pd.Timestamp(resolved_start)
    final_end = final_start + pd.Timedelta(hours=session_hours * (resolved_n - 1))

    if final_start < first_valid:
        logger.warning(
            f"Start date {final_start.date()} is before valid range. "
            f"Adjusting to {first_valid.date()}"
        )
        resolved_start = first_valid.replace(
            hour=10, minute=30, second=0, microsecond=0
        ).strftime("%Y-%m-%dT%H:%M:%SZ")

    if final_end > last_valid:
        available_hours = (
            last_valid - pd.Timestamp(resolved_start)
        ).total_seconds() / 3600
        adjusted_sessions = max(1, int(available_hours // session_hours))
        logger.warning(
            f"End date exceeds valid range. "
            f"Adjusting n_sessions: {resolved_n} -> {adjusted_sessions}"
        )
        resolved_n = adjusted_sessions

    return resolved_start, resolved_n


def _get_dataset_date_range(
    dataset_path: Path,
    datetime_format: str = "%Y-%m-%d %H:%M",
) -> tuple[pd.Timestamp, pd.Timestamp] | None:
    """Determine valid simulation date range from dataset.

    Reads measurements.csv to find the available date range.
    Returns start/end dates that allow for:
    - At least 7 days of historical data before first session
    - Forecast target day within the data range

    :param dataset_path: Path to dataset directory
    :param datetime_format: Format string for datetime parsing
    :return: Tuple of (first_valid_start, last_valid_start) or None if invalid
    """
    measurements_file = dataset_path / "measurements.csv"
    if not measurements_file.exists():
        return None

    try:
        df = pd.read_csv(measurements_file)
        if "datetime" not in df.columns or df.empty:
            return None

        df["datetime"] = pd.to_datetime(df["datetime"], format=datetime_format)
        df["datetime"] = df["datetime"].dt.tz_localize("UTC")

        data_start = df["datetime"].min()
        data_end = df["datetime"].max()

        # Need at least 7 days of historical data before first session
        # Plus 1 day buffer for the forecast target (D+1)
        min_history_days = 8
        first_valid_start = data_start + pd.Timedelta(days=min_history_days)

        # Last session must have forecast target within data range
        # Session at 10:30 generates forecasts for next day
        last_valid_start = data_end - pd.Timedelta(days=1)

        if first_valid_start >= last_valid_start:
            logger.warning(
                f"Dataset too short: {(data_end - data_start).days} days. "
                f"Need at least {min_history_days + 1} days."
            )
            return None

        return (first_valid_start, last_valid_start)

    except Exception as e:
        logger.error(f"Failed to read dataset date range: {e}")
        return None


class SimulatorTasks:
    """CLI commands for forecast simulation.

    This class provides Fire CLI commands for running forecast simulations,
    listing available datasets, and evaluating results.
    """

    @staticmethod
    def run(
        dataset: str = "example_elia",
        n_sessions: int | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        session_freq: int = 24,
        output_dir: str | None = None,
        n_jobs: int = 1,
        run_benchmarks: bool = True,
        strategies: str | tuple | list | None = None,
        datetime_format: str = "%Y-%m-%d %H:%M",
        csv_delimiter: str = ",",
        plot: bool = False,
        plot_individuals: bool = False,
        log_level: str = "info",
        name: str | None = None,
    ) -> None:
        """Run forecast simulation with custom dataset.

        Executes a series of market sessions using the specified dataset,
        generating ensemble forecasts and saving results.

        Date range options (in order of precedence):
        - start_date + n_sessions: Run n sessions starting from start_date
        - start_date + end_date: Run all sessions between dates
        - end_date + n_sessions: Run n sessions ending at end_date
        - start_date only: Run from start_date to end of dataset
        - end_date only: Run from start of dataset to end_date
        - None: Auto-detect full valid range from dataset

        :param dataset: Dataset name in input/ directory (default: example_elia)
        :param n_sessions: Number of sessions to simulate (default: auto from dataset)
        :param start_date: First session launch time in ISO format UTC
            (default: auto-detected from dataset)
        :param end_date: Last session launch time in ISO format UTC
            (default: auto-detected from dataset)
        :param session_freq: Hours between sessions (default: 24)
        :param output_dir: Custom output directory (default: auto-generated)
        :param n_jobs: Number of parallel jobs for MarketClass (default: 1)
        :param run_benchmarks: Run benchmark strategies (default: True)
        :param strategies: Comma-separated list of strategies to run
            (default: weighted_avg). If provided, sets the base strategies.
            Benchmarks are added if run_benchmarks=True.
        :param datetime_format: Format string for parsing CSV datetime columns
            (default: "%Y-%m-%d %H:%M")
        :param csv_delimiter: CSV field delimiter (default: ",")
        :param plot: Display plots at end of simulation (default: False)
        :param plot_individuals: Display individual forecaster submissions vs
            observed values at end of simulation (default: False). Implies plot=True.
        :param log_level: Logging verbosity - debug, info, warning, error, quiet
            (default: info)
        :param name: Custom name for the simulation output directory
            (default: auto-generated timestamp)

        :Example:
            # Run with auto-detected date range (recommended)
            python simulate.py run --dataset=example_elia

            # Run with a custom simulation name
            python simulate.py run --name=baseline_test

            # Run specific strategies
            python simulate.py run --strategies="weighted_avg,median"

            # Run custom strategy with benchmarks
            python simulate.py run --strategies="median" --run_benchmarks=True

            # Run specific date range
            python simulate.py run --start_date="2023-02-01T10:30:00Z" --end_date="2023-02-15T10:30:00Z"

            # Run with custom number of sessions
            python simulate.py run --n_sessions=5

            # Run with minimal output (quiet mode)
            python simulate.py run --log_level=quiet

            # Run with debug output for troubleshooting
            python simulate.py run --log_level=debug

            # Run with individual forecaster plots
            python simulate.py run --plot_individuals
        """
        # Configure logging verbosity
        _configure_log_level(log_level)
        if not MARKET_CLASS_AVAILABLE:
            logger.error(
                "MarketClass not available. Cannot run simulation. "
                "Please install the forecast engine dependencies."
            )
            return

        # Validate dataset parameter
        if not dataset or not isinstance(dataset, str) or not dataset.strip():
            logger.error(
                "Dataset name is required. "
                "Usage: python simulate.py run --dataset=<name>"
            )
            logger.info(f"Available datasets: {SimulatorTasks.list_datasets()}")
            return

        # Resolve dataset path
        datasets_dir = _get_datasets_dir()
        dataset_path = datasets_dir / dataset

        if not dataset_path.exists():
            logger.error(f"Dataset not found: {dataset_path}")
            logger.info(f"Available datasets: {SimulatorTasks.list_datasets()}")
            return

        logger.info("=" * 79)
        logger.info("FORECAST SIMULATOR")
        logger.info("=" * 79)

        # Get dataset date range for validation and auto-detection
        date_range = _get_dataset_date_range(dataset_path)
        if date_range is None:
            logger.error(
                "Could not determine valid date range from dataset. "
                "Please check that measurements.csv exists and has sufficient data."
            )
            return

        first_valid, last_valid = date_range
        logger.info(f"Dataset valid range: {first_valid.date()} to {last_valid.date()}")

        # Resolve date range from provided inputs
        start_date, n_sessions = _resolve_date_range(
            start_date=start_date,
            end_date=end_date,
            n_sessions=n_sessions,
            session_freq=session_freq,
            first_valid=first_valid,
            last_valid=last_valid,
        )

        # Resolve output directory from name parameter
        resolved_output_dir = output_dir
        if name and isinstance(name, str):
            # Use custom name for output directory
            output_root = Path(__file__).parent / "output" / dataset
            resolved_output_dir = str(output_root / name)

        # Create configuration
        try:
            config = SimulatorConfig(
                dataset_path=str(dataset_path),
                n_sessions=n_sessions,
                first_launch_time=start_date,
                session_freq_hours=session_freq,
                output_dir=resolved_output_dir,
                datetime_format=datetime_format,
                csv_delimiter=csv_delimiter,
            )
        except (ValueError, FileNotFoundError) as e:
            logger.error(f"Configuration error: {e}")
            return

        # Initialize manager
        manager = SimulatorManager(config)
        logger.info(f"Output directory: {manager.output_path}")

        # Run sessions with progress bar
        # Disable progress bar in quiet mode
        show_progress = log_level.lower() != "quiet"
        session_iterator = tqdm(
            manager.sessions,
            desc="Running sessions",
            unit="session",
            disable=not show_progress,
            ncols=80,
            bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]",
        )

        for session_id, launch_time in session_iterator:
            logger.info("-" * 79)
            logger.info(f"Session {session_id + 1}/{len(manager.sessions)}")
            session_t0 = time()

            try:
                # Load data
                loader = AgentsLoader(
                    launch_time=launch_time.to_pydatetime(),
                    data_path=str(dataset_path),
                    datetime_format=config.datetime_format,
                    csv_delimiter=config.csv_delimiter,
                )
                loader.load_datasets()

                # Store seller resources and forecasts for reporting
                manager.set_sellers_resources(loader.sellers_resources)
                manager.set_sellers_forecasts(loader.forecasts)

                # Create session
                generator = SessionGenerator()
                generator.create_session(
                    session_id=session_id,
                    launch_time=launch_time.to_pydatetime(),
                    buyers_data=loader.buyers_resources,
                )
                generator.create_challenges()
                generator.create_submissions(loader.sellers_resources)

                # Prepare session data
                session_data = {
                    "id": session_id,
                    "status": "open",
                    "registered_at": launch_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                }

                # Parse strategies list if provided
                strategies_list = None
                if strategies:
                    # Handle both string (comma-separated) and tuple (Fire parsing)
                    if isinstance(strategies, str):
                        strategies_list = [s.strip() for s in strategies.split(",")]
                    elif isinstance(strategies, (list, tuple)):
                        strategies_list = [s.strip() for s in strategies]
                    else:
                        strategies_list = [str(strategies)]

                # Run market session
                mc = MarketClass(
                    n_jobs=n_jobs,
                    run_benchmarks=run_benchmarks,
                    strategies=strategies_list,
                )
                mc.init_session(
                    session_data=session_data,
                    launch_time=launch_time.to_pydatetime(),
                )
                mc.show_session_details()

                try:
                    mc.load_challenges(challenges=generator.challenges)
                except Exception as e:
                    logger.warning(f"Failed to load challenges: {e}")
                    continue

                mc.load_buyer_measurements(measurements=loader.measurements)
                mc.load_forecasters(
                    sellers_resources=loader.sellers_resources,
                    sellers_forecasts=loader.forecasts,
                )

                # Run ensemble forecast
                mc.ensemble_forecast()
                mc.save_session_results(save_forecasts=True)

                # Collect results
                elapsed = time() - session_t0
                manager.add_session_report(
                    session_id=session_id,
                    session_lt=launch_time,
                    session_details=deepcopy(mc.mkt_sess.details),
                    buyers_results=deepcopy(mc.mkt_sess.buyers_results),
                    buyers_forecasts=deepcopy(mc.mkt_sess.buyers_forecasts),
                    elapsed_time=elapsed,
                )

                logger.success(f"Session {session_id} completed in {elapsed:.2f}s")

            except Exception as e:
                logger.exception(f"Session {session_id} failed: {e}")
            finally:
                # Clean up memory
                gc.collect()

        # Save final reports
        manager.save_reports()

        # Run evaluation automatically
        output_path = Path(manager.output_path)
        SimulatorTasks.evaluate(
            results_dir=str(output_path),
            dataset=dataset,
            datetime_format=datetime_format,
        )

        # Display results summary
        print("\n" + "=" * 70)
        print("SIMULATION COMPLETE")
        print("=" * 70)
        print(f"\nResults saved to: {output_path}")
        print("\nOutput files:")

        # List generated files
        if output_path.exists():
            for f in sorted(output_path.iterdir()):
                size_kb = f.stat().st_size / 1024
                print(f"  - {f.name} ({size_kb:.1f} KB)")

        print("\nNext steps:")
        print("  # Plot results")
        print(f"  python simulate.py plot {output_path}")
        print("\n  # Plot with individual forecasters")
        print(f"  python simulate.py plot {output_path} --plot_individuals")
        print("\n  # Re-run evaluation")
        print(f"  python simulate.py evaluate {output_path}")
        print("\n  # Preview forecasts")
        print(f"  head {output_path}/forecasts.csv")
        print("=" * 70 + "\n")

        # Display plots if enabled (plot_individuals implies plot)
        if plot or plot_individuals:
            manager.plot_results(plot_individuals=plot_individuals)

    @staticmethod
    def list_datasets() -> list[str]:
        """List available datasets in the input/ directory.

        :return: List of dataset directory names

        :Example:
            python simulate.py list_datasets
        """
        datasets_dir = _get_datasets_dir()

        if not datasets_dir.exists():
            logger.warning(f"Input directory not found: {datasets_dir}")
            return []

        datasets = [
            d.name
            for d in datasets_dir.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        ]

        if datasets:
            logger.info("Available datasets:")
            for ds in sorted(datasets):
                ds_path = datasets_dir / ds
                # Check for required files
                has_measurements = (ds_path / "measurements.csv").exists()
                has_forecasts = (ds_path / "forecasts.csv").exists()
                has_config = (ds_path / "config.json").exists()

                status = (
                    "complete"
                    if all([has_measurements, has_forecasts, has_config])
                    else "incomplete"
                )

                logger.info(f"  - {ds} ({status})")
        else:
            logger.info("No datasets found.")

        return sorted(datasets)

    @staticmethod
    def create_dataset(name: str, template: str = "example_elia") -> None:
        """Create a new dataset from a template.

        Copies an existing dataset to create a new one that you can customize.

        :param name: Name for the new dataset
        :param template: Template dataset to copy from (default: example_elia)

        :Example:
            python simulate.py create_dataset --name=my_wind_farm

            python simulate.py create_dataset --name=solar_plant --template=example_elia
        """
        # Validate name parameter
        if not isinstance(name, str) or not name:
            logger.error("Dataset name is required. Usage: --name=<dataset_name>")
            return

        datasets_dir = _get_datasets_dir()
        template_path = datasets_dir / template
        new_path = datasets_dir / name

        if not template_path.exists():
            logger.error(f"Template dataset not found: {template}")
            logger.info(f"Available: {SimulatorTasks.list_datasets()}")
            return

        if new_path.exists():
            logger.error(f"Dataset already exists: {name}")
            return

        try:
            shutil.copytree(template_path, new_path)
            logger.success(f"Created dataset: {name}")
            logger.info(f"Location: {new_path}")
            logger.info("Edit the following files to customize:")
            logger.info(f"  - {new_path}/config.json (timezone and use_case)")
            logger.info(
                f"  - {new_path}/measurements.csv (resources derived from columns)"
            )
            logger.info(f"  - {new_path}/forecasts.csv (sellers derived from columns)")
        except Exception as e:
            logger.error(f"Failed to create dataset: {e}")

    @staticmethod
    def evaluate(
        results_dir: str,
        dataset: str | None = None,
        output_format: str = "csv",
        save_to: str | None = None,
        datetime_format: str = "%Y-%m-%d %H:%M",
    ) -> None:
        """Evaluate simulation results and compute skill scores.

        Computes forecast accuracy metrics by comparing ensemble forecasts
        against actual measurements:
        - RMSE (Root Mean Square Error) for Q50
        - MAE (Mean Absolute Error) for Q50
        - Pinball Loss for all quantiles
        - Winkler Score for prediction intervals (Q10-Q90)

        :param results_dir: Path to simulation results directory
        :param dataset: Dataset name for loading observations (default: auto-detect from path)
        :param output_format: Output format - csv, json, or print (default: csv)
        :param save_to: Custom output path (default: results_dir/evaluation.csv)
        :param datetime_format: Format for datetime parsing

        :Example:
            python simulate.py evaluate output/example_elia/20250101_120000/

            python simulate.py evaluate output/run1/ --dataset=example_elia

            python simulate.py evaluate output/run1/ --output_format=print
        """
        results_path = Path(results_dir)

        if not results_path.exists():
            logger.error(f"Results directory not found: {results_dir}")
            return

        forecasts_file = results_path / "forecasts.csv"
        if not forecasts_file.exists():
            logger.error(f"Forecasts file not found: {forecasts_file}")
            return

        # Auto-detect dataset from path if not provided
        # Expected path: output/<dataset>/<timestamp>/
        if dataset is None:
            try:
                dataset = results_path.parent.name
            except Exception:
                logger.error(
                    "Could not auto-detect dataset. Please provide --dataset parameter."
                )
                return

        # Load observations
        datasets_dir = _get_datasets_dir()
        dataset_path = datasets_dir / dataset
        measurements_file = dataset_path / "measurements.csv"

        if not measurements_file.exists():
            logger.error(f"Measurements file not found: {measurements_file}")
            logger.info("Please specify the correct dataset with --dataset=<name>")
            return

        logger.info(f"Evaluating results from: {results_dir}")
        logger.info(f"Using dataset: {dataset}")

        # Load forecasts and measurements
        forecasts_df = pd.read_csv(forecasts_file)
        measurements_df = pd.read_csv(measurements_file)

        if forecasts_df.empty:
            logger.warning("No forecasts to evaluate.")
            return

        # Parse datetime columns (ensure both are tz-naive for joining)
        forecasts_df["datetime"] = pd.to_datetime(
            forecasts_df["datetime"]
        ).dt.tz_localize(None)
        measurements_df["datetime"] = pd.to_datetime(
            measurements_df["datetime"], format=datetime_format
        )
        measurements_df = measurements_df.set_index("datetime")

        # Get unique strategies and variables
        strategies = (
            forecasts_df["strategy"].unique()
            if "strategy" in forecasts_df.columns
            else ["unknown"]
        )
        variables = (
            forecasts_df["variable"].unique()
            if "variable" in forecasts_df.columns
            else ["q50"]
        )
        # Single resource per simulation (always "target")
        resource_id = "target"

        logger.info(f"Strategies: {list(strategies)}")
        logger.info(f"Variables: {list(variables)}")

        # Compute skill scores per strategy
        all_scores = []

        # Get observations for the target resource
        if resource_id not in measurements_df.columns:
            logger.warning(f"Resource {resource_id} not found in measurements")
            return

        observations = measurements_df[[resource_id]].rename(
            columns={resource_id: "observed"}
        )

        for strategy in strategies:
            strategy_df = forecasts_df[forecasts_df["strategy"] == strategy]

            # Compute scores for each quantile
            for variable in variables:
                var_df = strategy_df[strategy_df["variable"] == variable].copy()
                if var_df.empty:
                    continue

                var_df = var_df.set_index("datetime")

                # Merge forecasts with observations
                eval_df = var_df[["value"]].join(observations, how="inner")
                eval_df = eval_df.rename(columns={"value": "forecast"})
                eval_df = eval_df.dropna()

                if eval_df.empty:
                    continue

                score_row = {
                    "strategy": strategy,
                    "variable": variable,
                    "n_observations": len(eval_df),
                }

                # Compute metrics
                if variable == "q50":
                    score_row["rmse"] = metrics.rmse(eval_df)
                    score_row["mae"] = metrics.mae(eval_df)

                score_row["pinball"] = metrics.pinball_loss(eval_df, variable)

                all_scores.append(score_row)

            # Compute Winkler score (needs Q10 and Q90)
            q10_df = strategy_df[strategy_df["variable"] == "q10"].set_index("datetime")
            q90_df = strategy_df[strategy_df["variable"] == "q90"].set_index("datetime")

            if not q10_df.empty and not q90_df.empty:
                winkler_df = (
                    pd.DataFrame(
                        {
                            "q10": q10_df["value"],
                            "q90": q90_df["value"],
                        }
                    )
                    .join(observations, how="inner")
                    .dropna()
                )

                if not winkler_df.empty:
                    winkler_val = metrics.winkler_score(winkler_df)
                    all_scores.append(
                        {
                            "strategy": strategy,
                            "variable": "interval",
                            "n_observations": len(winkler_df),
                            "winkler": winkler_val,
                        }
                    )

        # Create results DataFrame
        scores_df = pd.DataFrame(all_scores)

        if scores_df.empty:
            logger.warning(
                "No scores computed. Check that forecasts overlap with measurements."
            )
            return

        # Print summary
        print("\n" + "=" * 70)
        print("FORECAST SKILL SCORES")
        print("=" * 70)

        # Summary by strategy
        summary_cols = ["strategy", "variable"]
        metric_cols = [
            c for c in ["rmse", "mae", "pinball", "winkler"] if c in scores_df.columns
        ]

        if metric_cols:
            summary = scores_df.groupby(summary_cols)[metric_cols].mean().round(3)
            print("\nScores by Strategy and Variable:")
            print(summary.to_string())

        # Overall statistics
        print(f"\nTotal observations evaluated: {scores_df['n_observations'].sum()}")
        print(f"Strategies evaluated: {len(strategies)}")
        print("=" * 70 + "\n")

        # Save evaluation
        output_path = save_to or str(results_path / "evaluation.csv")

        if output_format == "print":
            print(scores_df.to_string(index=False))
        elif output_format == "json":
            output_path = save_to or str(results_path / "evaluation.json")
            scores_df.to_json(output_path, orient="records", indent=2)
            logger.success(f"Saved evaluation to: {output_path}")
        else:  # csv
            scores_df.to_csv(output_path, index=False)
            logger.success(f"Saved evaluation to: {output_path}")

    @staticmethod
    def plot(
        results_dir: str,
        dataset: str | None = None,
        session_id: int | str | None = None,
        strategy: str = "weighted_avg",
        plot_individuals: bool = False,
        datetime_format: str = "%Y-%m-%d %H:%M",
        save_to: str | None = None,
        log_level: str = "info",
    ) -> None:
        """Generate plots from simulation results.

        Creates visualizations comparing ensemble forecasts against
        observed measurements:
        - Strategy comparison (Q50 time series)
        - Prediction intervals (Q10-Q90 band)
        - Metrics summary (bar charts)
        - Individual forecaster comparison (optional, with --plot_individuals)

        :param results_dir: Path to simulation results directory
        :param dataset: Dataset name for loading observations (default: auto-detect)
        :param session_id: Session ID to plot, "all" for all sessions,
            or None for all (default: all)
        :param strategy: Strategy for prediction interval plot (default: weighted_avg)
        :param plot_individuals: Plot individual forecaster submissions vs
            observed values (default: False)
        :param datetime_format: Format for datetime parsing
        :param save_to: Optional path to save plots as PNG (e.g., "plots.png").
            If not specified, displays plots interactively.
        :param log_level: Logging verbosity (default: info)

        :Example:
            # Plot results interactively
            python simulate.py plot output/example_elia/20250101_120000/

            # Plot specific strategy's prediction intervals
            python simulate.py plot output/run1/ --strategy=arithmetic_mean

            # Plot with individual forecaster comparison
            python simulate.py plot output/run1/ --plot_individuals

            # Save plots to file
            python simulate.py plot output/run1/ --save_to=my_plots.png
        """
        _configure_log_level(log_level)

        results_path = Path(results_dir)

        if not results_path.exists():
            logger.error(f"Results directory not found: {results_dir}")
            return

        # Check required files
        forecasts_file = results_path / "forecasts.csv"
        if not forecasts_file.exists():
            logger.error(f"Forecasts file not found: {forecasts_file}")
            return

        # Auto-detect dataset from path if not provided
        # Expected path: output/<dataset>/<timestamp>/
        if dataset is None:
            try:
                dataset = results_path.parent.name
            except Exception:
                logger.error(
                    "Could not auto-detect dataset. Please provide --dataset parameter."
                )
                return

        # Load observations from original dataset
        datasets_dir = _get_datasets_dir()
        dataset_path = datasets_dir / dataset
        measurements_file = dataset_path / "measurements.csv"

        if not measurements_file.exists():
            logger.error(f"Measurements file not found: {measurements_file}")
            logger.info("Please specify the correct dataset with --dataset=<name>")
            return

        logger.info(f"Plotting results from: {results_dir}")
        logger.info(f"Using dataset: {dataset}")

        # Load data
        forecasts_df = pd.read_csv(forecasts_file)
        measurements_df = pd.read_csv(measurements_file)

        if forecasts_df.empty:
            logger.warning("No forecasts to plot.")
            return

        logger.info(f"Loaded {len(forecasts_df)} forecast records")
        logger.info(f"Loaded {len(measurements_df)} measurement records")

        # Parse datetime columns
        forecasts_df["datetime"] = pd.to_datetime(
            forecasts_df["datetime"]
        ).dt.tz_localize(None)
        measurements_df["datetime"] = pd.to_datetime(
            measurements_df["datetime"], format=datetime_format
        )

        # Filter by session if specified
        if session_id is not None and session_id != "all":
            if "session_id" in forecasts_df.columns:
                available_sessions = sorted(forecasts_df["session_id"].unique())
                if session_id not in available_sessions:
                    logger.error(
                        f"Session {session_id} not found. "
                        f"Available: {available_sessions[:10]}..."
                    )
                    return
                forecasts_df = forecasts_df[forecasts_df["session_id"] == session_id]
                logger.info(
                    f"Filtered to session {session_id}: {len(forecasts_df)} forecasts"
                )

        # Prepare measurements for plotting
        # Rename 'target' column to 'observed' for ForecastPlotter
        if "target" in measurements_df.columns:
            measurements_df = measurements_df.rename(columns={"target": "observed"})

        # Import plotting module
        try:
            from core.plots import ForecastPlotter
        except ImportError:
            from simulator.community.core.plots import ForecastPlotter

        # Import matplotlib
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            logger.error(
                "matplotlib is required for plotting. "
                "Install with: pip install matplotlib"
            )
            return

        logger.info("Generating plots...")

        # Create plotter
        plotter = ForecastPlotter(forecasts_df, measurements_df)

        # Generate plots
        figures = []

        # Plot 1: Strategy comparison (Q50)
        if "q50" in plotter.variables:
            fig = plotter.plot_strategy_comparison(quantile="q50")
            if fig:
                figures.append(fig)

        # Plot 2: Prediction intervals for specified strategy
        if strategy in plotter.strategies:
            fig = plotter.plot_prediction_intervals(strategy=strategy)
            if fig:
                figures.append(fig)
        elif len(plotter.strategies) > 0:
            # Fallback to first available strategy
            fig = plotter.plot_prediction_intervals(strategy=plotter.strategies[0])
            if fig:
                figures.append(fig)

        # Plot 3: Metrics summary
        fig = plotter.plot_metrics_summary()
        if fig:
            figures.append(fig)

        # Plot 4: Forecaster comparison (individual forecasters in grey, ensembles in color)
        if plot_individuals:
            submissions_file = results_path / "submissions.csv"
            if submissions_file.exists():
                submissions_df = pd.read_csv(submissions_file)
                if "datetime" in submissions_df.columns:
                    submissions_df["datetime"] = pd.to_datetime(
                        submissions_df["datetime"]
                    )
                logger.info(f"Loaded {len(submissions_df)} submission records")

                if not submissions_df.empty:
                    fig = plotter.plot_forecaster_comparison(submissions_df)
                    if fig:
                        figures.append(fig)
            else:
                logger.warning(
                    "No submissions.csv found. "
                    "Re-run simulation to generate individual forecaster data."
                )

        # Print metrics table to console
        plotter.print_metrics_table()

        # Save or display
        if save_to:
            # Save all figures to a single file or multiple files
            if len(figures) == 1:
                figures[0].savefig(save_to, dpi=150, bbox_inches="tight")
                logger.success(f"Plot saved to: {save_to}")
            else:
                # Save each figure with numbered suffix
                base_path = Path(save_to)
                for i, fig in enumerate(figures, 1):
                    out_path = (
                        base_path.parent / f"{base_path.stem}_{i}{base_path.suffix}"
                    )
                    fig.savefig(out_path, dpi=150, bbox_inches="tight")
                    logger.success(f"Plot saved to: {out_path}")
            plt.close("all")
        else:
            # Display interactively
            logger.info("Displaying plots...")
            plt.show()

    @staticmethod
    def validate_dataset(
        name: str,
        datetime_format: str = "%Y-%m-%d %H:%M",
    ) -> bool:
        """Validate dataset structure and content.

        Performs comprehensive checks on a dataset:
        - All required files exist (measurements.csv, forecasts.csv, JSON configs)
        - CSV columns match JSON resource definitions
        - Date ranges are sufficient (min 9 days for 8 days history + 1 forecast)
        - No missing values in required columns

        :param name: Dataset name in input/ directory
        :param datetime_format: Format string for datetime parsing
        :return: True if valid, False otherwise

        :Example:
            python simulate.py validate_dataset --name=example_elia

            python simulate.py validate_dataset --name=my_dataset
        """
        # Validate name parameter
        if not isinstance(name, str) or not name:
            logger.error("Dataset name is required. Usage: --name=<dataset_name>")
            return False

        datasets_dir = _get_datasets_dir()
        dataset_path = datasets_dir / name

        logger.info(f"Validating dataset: {name}")
        logger.info("=" * 60)

        errors = []
        warnings = []

        # Check 1: Dataset directory exists
        if not dataset_path.exists():
            logger.error(f"Dataset directory not found: {dataset_path}")
            return False

        # Check 2: Required files exist
        required_files = {
            "config.json": "Dataset configuration (timezone, use_case)",
            "measurements.csv": "Historical power measurements",
            "forecasts.csv": "Forecaster predictions",
        }

        logger.info("Checking required files...")
        for filename, description in required_files.items():
            filepath = dataset_path / filename
            if filepath.exists():
                logger.info(f"  [OK] {filename}")
            else:
                errors.append(f"Missing file: {filename} ({description})")
                logger.error(f"  [MISSING] {filename}")

        if errors:
            logger.error(f"\nValidation failed with {len(errors)} error(s)")
            return False

        # Load config.json
        try:
            with open(dataset_path / "config.json") as f:
                config = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config.json: {e}")
            return False

        # Validate config has required fields
        logger.info("\nChecking config.json...")
        if "timezone" not in config:
            errors.append("config.json missing 'timezone' field")
        else:
            logger.info(f"  [OK] timezone: {config['timezone']}")

        if "use_case" not in config:
            errors.append("config.json missing 'use_case' field")
        else:
            valid_use_cases = ["wind_power", "wind_power_ramp", "solar_power", "load"]
            if config["use_case"] not in valid_use_cases:
                warnings.append(
                    f"use_case '{config['use_case']}' not in standard list: {valid_use_cases}"
                )
            logger.info(f"  [OK] use_case: {config['use_case']}")

        # Check for 'target' column in measurements.csv
        try:
            measurements_df = pd.read_csv(dataset_path / "measurements.csv", nrows=0)
            has_target = "target" in measurements_df.columns
        except Exception as e:
            errors.append(f"Cannot read measurements.csv: {e}")
            has_target = False

        # Derive sellers from forecasts.csv columns
        sellers = []
        try:
            forecasts_df = pd.read_csv(dataset_path / "forecasts.csv", nrows=0)
            for col in forecasts_df.columns:
                if col == "datetime":
                    continue
                parts = col.rsplit("_", 1)
                if len(parts) == 2:
                    seller, variable = parts
                    if variable in ("q10", "q50", "q90"):
                        sellers.append(
                            {
                                "user": seller,
                                "variable": variable,
                            }
                        )
        except Exception as e:
            errors.append(f"Cannot parse forecasts.csv columns: {e}")

        # Check 3: Validate measurements.csv has 'target' column
        logger.info("\nChecking resource definitions...")
        if has_target:
            logger.info("  [OK] measurements.csv has 'target' column")
        else:
            errors.append(
                "measurements.csv must have a 'target' column "
                "(the values being forecasted)"
            )
        logger.info(
            f"  Found {len(sellers)} seller submission(s) (derived from forecasts.csv)"
        )

        # Check 4: Validate forecasts.csv columns follow naming convention
        logger.info("\nChecking forecasts.csv column format...")
        try:
            forecasts_df = pd.read_csv(dataset_path / "forecasts.csv", nrows=5)
            if "datetime" not in forecasts_df.columns:
                errors.append("forecasts.csv missing 'datetime' column")
            else:
                csv_columns = set(forecasts_df.columns) - {"datetime"}
                valid_columns = 0
                invalid_columns = []
                for col in csv_columns:
                    parts = col.rsplit("_", 1)
                    if len(parts) == 2 and parts[1] in ("q10", "q50", "q90"):
                        valid_columns += 1
                    else:
                        invalid_columns.append(col)

                if invalid_columns:
                    warnings.append(
                        f"Columns not matching {{seller}}_{{quantile}} format: "
                        f"{invalid_columns[:3]}..."
                    )
                if valid_columns > 0:
                    logger.info(f"  [OK] Found {valid_columns} valid forecast columns")
                    logger.info(f"  [OK] Derived {len(sellers)} seller submissions")
                else:
                    errors.append(
                        "No valid forecast columns found (expected format: seller_q50)"
                    )
        except Exception as e:
            errors.append(f"Cannot read forecasts.csv: {e}")

        # Check 5: Validate date range
        logger.info("\nChecking date range...")
        date_range = _get_dataset_date_range(dataset_path, datetime_format)
        if date_range is None:
            errors.append(
                "Insufficient date range. Need at least 9 days "
                "(8 days history + 1 day forecast target)"
            )
        else:
            first_valid, last_valid = date_range
            available_days = (last_valid - first_valid).days
            logger.info(
                f"  Valid simulation range: {first_valid.date()} to {last_valid.date()}"
            )
            logger.info(f"  Available days for simulation: {available_days}")
            if available_days < 1:
                errors.append("Date range too short for simulation")
            else:
                logger.info("  [OK] Date range sufficient")

        # Check 6: Check for missing values in measurements
        logger.info("\nChecking data quality...")
        try:
            full_measurements = pd.read_csv(dataset_path / "measurements.csv")
            full_measurements["datetime"] = pd.to_datetime(
                full_measurements["datetime"], format=datetime_format
            )
            if "target" in full_measurements.columns:
                missing_count = full_measurements["target"].isna().sum()
                total_count = len(full_measurements)
                if missing_count > 0:
                    missing_pct = (missing_count / total_count) * 100
                    if missing_pct > 10:
                        warnings.append(
                            f"High missing value rate in target: "
                            f"{missing_count}/{total_count} ({missing_pct:.1f}%)"
                        )
                    else:
                        logger.info(
                            f"  [WARN] target: {missing_count} missing values "
                            f"({missing_pct:.1f}%)"
                        )
                else:
                    logger.info("  [OK] target: no missing values")
        except Exception as e:
            warnings.append(f"Could not check data quality: {e}")

        # Summary
        logger.info("\n" + "=" * 60)
        if errors:
            logger.error(f"Validation FAILED with {len(errors)} error(s):")
            for err in errors:
                logger.error(f"  - {err}")
            return False

        if warnings:
            logger.warning(f"Validation passed with {len(warnings)} warning(s):")
            for warn in warnings:
                logger.warning(f"  - {warn}")
        else:
            logger.success("Validation PASSED - all checks OK")

        return True

    @staticmethod
    def generate_dataset(log_level: str = "info", plot: bool = False) -> None:
        """Generate a synthetic dataset for testing ensemble strategies.

        Launches an interactive wizard that guides you through creating
        a synthetic dataset with custom measurements and forecaster
        predictions. Useful for benchmarking strategies against known
        optimal solutions and testing edge cases.

        :param log_level: Logging verbosity (default: info)
        :param plot: Plot individual forecasts vs observed after generation
            (default: False). If True, skips the plot prompt in the wizard.

        :Example:
            python simulate.py generate_dataset

            # Generate and plot immediately
            python simulate.py generate_dataset --plot
        """
        _configure_log_level(log_level)

        print("\n" + "=" * 60)
        print("SYNTHETIC DATASET GENERATOR")
        print("=" * 60)
        print("\nThis wizard will help you create a synthetic dataset for")
        print("testing ensemble forecasting strategies.\n")

        # Helper function for prompting with validation
        def prompt(
            message: str,
            default: str | None = None,
            valid_options: list[str] | None = None,
            input_type: type = str,
            min_value: int | float | None = None,
            validate_date: bool = False,
        ) -> str:
            """Prompt user for input with optional validation."""
            prompt_str = message
            if default is not None:
                prompt_str += f" [{default}]"
            prompt_str += ": "

            while True:
                response = input(prompt_str).strip()
                if not response and default is not None:
                    response = str(default)

                if not response:
                    print("  This field is required.")
                    continue

                if valid_options and response.lower() not in [
                    o.lower() for o in valid_options
                ]:
                    print(f"  Invalid option. Choose from: {', '.join(valid_options)}")
                    continue

                if input_type is int:
                    try:
                        val = int(response)
                        if min_value is not None and val < min_value:
                            print(f"  Value must be at least {min_value}.")
                            continue
                    except ValueError:
                        print("  Please enter a valid integer.")
                        continue

                if input_type is float:
                    try:
                        val = float(response)
                        if min_value is not None and val < min_value:
                            print(f"  Value must be at least {min_value}.")
                            continue
                    except ValueError:
                        print("  Please enter a valid number.")
                        continue

                if validate_date:
                    import re
                    from datetime import datetime as dt

                    if not re.match(r"^\d{4}-\d{2}-\d{2}$", response):
                        print(
                            "  Invalid date format. Use YYYY-MM-DD (e.g., 2023-01-15)."
                        )
                        continue
                    # Validate it's a real date using datetime
                    try:
                        dt.strptime(response, "%Y-%m-%d")
                    except ValueError:
                        print(
                            "  Invalid date. Please enter a valid date (e.g., 2023-01-15)."
                        )
                        continue

                return response

        def prompt_yes_no(message: str, default: bool = False) -> bool:
            """Prompt for yes/no response."""
            default_str = "Y/n" if default else "y/N"
            response = input(f"{message} [{default_str}]: ").strip().lower()
            if not response:
                return default
            return response in ("y", "yes", "true", "1")

        # Step 1: Dataset name
        print("-" * 60)
        print("STEP 1: Basic Information")
        print("-" * 60)

        datasets_dir = _get_datasets_dir()
        while True:
            name = prompt("Dataset name (no spaces)")
            if not name:
                print("  Dataset name is required.")
                continue
            if " " in name:
                print("  Dataset name cannot contain spaces.")
                continue
            if (datasets_dir / name).exists():
                print(f"  Dataset '{name}' already exists. Choose a different name.")
                continue
            break

        # Step 2: Use case
        print("\n" + "-" * 60)
        print("STEP 2: Power Generation Type")
        print("-" * 60)
        print("\nAvailable use cases:")
        print("  1. wind_power  - Offshore/onshore wind generation")
        print("  2. solar_power - Photovoltaic solar generation")

        use_case = prompt(
            "\nUse case",
            default="wind_power",
            valid_options=["wind_power", "solar_power", "1", "2"],
        )
        if use_case == "1":
            use_case = "wind_power"
        elif use_case == "2":
            use_case = "solar_power"

        # Step 3: Dataset size
        print("\n" + "-" * 60)
        print("STEP 3: Dataset Size")
        print("-" * 60)

        n_days = int(
            prompt(
                "\nNumber of days of data",
                default="30",
                input_type=int,
                min_value=10,
            )
        )

        base_capacity = float(
            prompt(
                "Base power capacity in MW",
                default="1000",
                input_type=float,
                min_value=1,
            )
        )

        # Step 4: Forecasters
        print("\n" + "-" * 60)
        print("STEP 4: Forecaster Configuration")
        print("-" * 60)
        print("\nAvailable forecaster archetypes:")
        archetypes_info = SyntheticGenerator.list_archetypes()
        valid_archetypes = list(archetypes_info.keys())
        for i, (arch_name, description) in enumerate(archetypes_info.items(), 1):
            print(f"  {i}. {arch_name:15} - {description}")

        print("\nYou can specify how many forecasters of each type to include.")
        print("Example: 'skilled:2,noisy:1,biased:1' creates 4 forecasters total.\n")

        use_custom = prompt_yes_no("Configure custom forecaster mix?", default=False)

        archetypes_spec = None
        if use_custom:
            print("\nEnter forecaster specification (archetype:count,...):")
            print("Leave blank for default (5 skilled forecasters)")

            while True:
                user_input = input("> ").strip()
                if not user_input:
                    archetypes_spec = None
                    break

                # Validate the specification format
                is_valid = True
                total_forecasters = 0
                parsed_specs = []

                for spec in user_input.split(","):
                    spec = spec.strip()
                    if ":" not in spec:
                        print(
                            f"  Invalid format: '{spec}'. Expected 'archetype:count'."
                        )
                        is_valid = False
                        break

                    parts = spec.split(":", 1)
                    arch_name = parts[0].strip().lower()
                    count_str = parts[1].strip()

                    if arch_name not in valid_archetypes:
                        print(f"  Unknown archetype: '{arch_name}'.")
                        print(f"  Valid options: {', '.join(valid_archetypes)}")
                        is_valid = False
                        break

                    try:
                        count = int(count_str)
                        if count < 1:
                            print(f"  Count must be at least 1, got: {count}")
                            is_valid = False
                            break
                        total_forecasters += count
                        parsed_specs.append(f"{arch_name}:{count}")
                    except ValueError:
                        print(f"  Invalid count: '{count_str}'. Must be an integer.")
                        is_valid = False
                        break

                if is_valid:
                    archetypes_spec = ",".join(parsed_specs)
                    print(
                        f"  Configured {total_forecasters} forecaster(s): {archetypes_spec}"
                    )
                    break
                else:
                    print("  Please try again or leave blank for default.\n")
        else:
            n_forecasters = int(
                prompt(
                    "Number of forecasters (all skilled)",
                    default="5",
                    input_type=int,
                    min_value=1,
                )
            )
            archetypes_spec = f"skilled:{n_forecasters}"

        # Step 4b: Forecaster Diversity
        print("\n" + "-" * 60)
        print("STEP 4b: Forecaster Diversity")
        print("-" * 60)
        print("\nDiversity controls how much each forecaster's parameters")
        print("deviate from archetype defaults:")
        print("  0.0 = Identical parameters (only random sequences differ)")
        print("  0.5 = Moderate variation in noise, bias, interval scale")
        print("  1.0 = Maximum variation within archetype ranges")

        diversity = float(
            prompt(
                "\nDiversity level",
                default="0.0",
                input_type=float,
                min_value=0.0,
            )
        )
        diversity = min(1.0, diversity)  # Cap at 1.0

        # Step 5: Scenarios
        print("\n" + "-" * 60)
        print("STEP 5: Test Scenarios (Optional)")
        print("-" * 60)
        print("\nScenarios add specific test conditions to your dataset:")
        print("  1. none              - No special scenario")
        print("  2. regime_change     - Forecaster performance degrades mid-dataset")
        print("  3. dropout           - Some forecasters stop submitting")
        print("  4. distribution_shift - Underlying data distribution changes")

        scenario_choice = prompt(
            "\nSelect scenario",
            default="none",
            valid_options=[
                "none",
                "regime_change",
                "dropout",
                "distribution_shift",
                "1",
                "2",
                "3",
                "4",
            ],
        )

        scenario_map = {
            "1": "none",
            "2": "regime_change",
            "3": "dropout",
            "4": "distribution_shift",
        }
        scenario = scenario_map.get(scenario_choice, scenario_choice)
        if scenario == "none":
            scenario = None

        scenario_kwargs = {}
        if scenario:
            print(f"\nConfiguring '{scenario}' scenario...")
            # Calculate default change point (middle of dataset)
            mid_day = 15 + n_days // 2
            # Handle month overflow
            if mid_day > 28:
                default_change = (
                    f"2023-02-{mid_day - 31:02d}"
                    if mid_day > 31
                    else f"2023-01-{mid_day:02d}"
                )
            else:
                default_change = f"2023-01-{mid_day:02d}"

            change_point = prompt(
                "Change point date (YYYY-MM-DD)",
                default=default_change,
                validate_date=True,
            )
            scenario_kwargs["change_point"] = change_point

        # Step 6: Advanced options
        print("\n" + "-" * 60)
        print("STEP 6: Advanced Options")
        print("-" * 60)

        show_advanced = prompt_yes_no("Configure advanced options?", default=False)

        seed = 42
        start_date = "2023-01-15"
        show_plot = plot  # Use CLI flag if provided

        if show_advanced:
            seed = int(
                prompt(
                    "Random seed (for reproducibility)", default="42", input_type=int
                )
            )
            start_date = prompt(
                "Start date (YYYY-MM-DD)",
                default="2023-01-15",
                validate_date=True,
            )
            if not plot:  # Only ask if not already set via CLI
                show_plot = prompt_yes_no(
                    "Plot forecasts vs observed after generation?", default=True
                )

        # Summary and confirmation
        print("\n" + "=" * 60)
        print("CONFIGURATION SUMMARY")
        print("=" * 60)
        print(f"\n  Dataset name:    {name}")
        print(f"  Use case:        {use_case}")
        print(f"  Days of data:    {n_days}")
        print(f"  Base capacity:   {base_capacity} MW")
        print(f"  Forecasters:     {archetypes_spec or 'skilled:5 (default)'}")
        print(f"  Diversity:       {diversity:.2f}")
        print(f"  Scenario:        {scenario or 'None'}")
        if scenario:
            print(f"  Change point:    {scenario_kwargs.get('change_point', 'N/A')}")
        print(f"  Random seed:     {seed}")
        print(f"  Start date:      {start_date}")
        print(f"  Plot results:    {'Yes' if show_plot else 'No'}")
        print()

        if not prompt_yes_no("Generate this dataset?", default=True):
            print("\nDataset generation cancelled.")
            return

        # Generate the dataset
        print()
        generator = SyntheticGenerator(
            seed=seed, use_case=use_case, diversity=diversity
        )
        generator.generate_dataset(
            name=name,
            n_forecasters=5,  # Ignored when archetypes_spec is provided
            n_days=n_days,
            archetypes=archetypes_spec,
            scenario=scenario,
            base_capacity=base_capacity,
            start_date=start_date,
            plot=show_plot,
            **scenario_kwargs,
        )

    @staticmethod
    def quickstart(log_level: str = "info") -> None:
        """Run a complete quickstart demo: generate dataset and run simulation.

        Creates a synthetic dataset called 'quickstart_demo' with sensible defaults,
        then runs a 30-session simulation with plots enabled. This is the fastest
        way to see the simulator in action.

        The quickstart uses a mix of biased and skilled forecasters to demonstrate
        how ensemble methods can outperform individual predictors:
        - biased: Systematic over-prediction
        - biased_low: Systematic under-prediction
        - skilled: High accuracy, well-calibrated

        Dataset parameters (fixed):
        - 15 forecasters: biased:5, biased_low:5, skilled:5
        - 60 days of wind power data
        - Seed: 42 (reproducible)
        - Base capacity: 2000 MW
        - Diversity: 0.5 (moderate parameter variation)

        Simulation parameters (fixed):
        - 30 sessions
        - Strategies: weighted_avg, arithmetic_mean, median, best_forecaster
        - Plots shown at end (evaluation + individual forecasters)

        :param log_level: Logging verbosity (default: info)

        :Example:
            python simulate.py quickstart
        """
        _configure_log_level(log_level)

        # Fixed quickstart parameters
        DATASET_NAME = "quickstart_demo"
        ARCHETYPES = "biased:5,biased_low:5,skilled:5"
        N_FORECASTERS = 15
        N_DAYS = 60
        USE_CASE = "wind_power"
        SEED = 42
        BASE_CAPACITY = 2000.0
        START_DATE = "2026-01-01"
        N_SESSIONS = 30
        DIVERSITY = 0.5
        STRATEGIES = "weighted_avg,arithmetic_mean,median,best_forecaster"

        print("\n" + "=" * 60)
        print("QUICKSTART")
        print("=" * 60)

        datasets_dir = _get_datasets_dir()
        dataset_path = datasets_dir / DATASET_NAME

        # Step 1: Generate dataset (overwrite if exists)
        print("\n[1/2] Generating dataset...")
        print(f"      Name: {DATASET_NAME}")
        print(f"      Forecasters: {N_FORECASTERS} ({ARCHETYPES})")
        print(f"      Data: {N_DAYS} days of {USE_CASE}")
        print(f"      Seed: {SEED}")

        # Remove existing dataset if present
        if dataset_path.exists():
            shutil.rmtree(dataset_path)
            logger.info(f"Removed existing dataset: {DATASET_NAME}")

        # Generate the dataset
        generator = SyntheticGenerator(
            seed=SEED, use_case=USE_CASE, diversity=DIVERSITY
        )
        generator.generate_dataset(
            name=DATASET_NAME,
            n_forecasters=N_FORECASTERS,
            n_days=N_DAYS,
            archetypes=ARCHETYPES,
            scenario=None,
            base_capacity=BASE_CAPACITY,
            start_date=START_DATE,
            plot=False,  # Don't plot during generation
        )

        print(f"      Dataset saved to: input/{DATASET_NAME}/")

        # Step 2: Run simulation
        print(f"\n[2/2] Running simulation ({N_SESSIONS} sessions)...")

        SimulatorTasks.run(
            dataset=DATASET_NAME,
            n_sessions=N_SESSIONS,
            plot=True,
            plot_individuals=True,
            log_level=log_level,
            strategies=STRATEGIES,
        )

    @staticmethod
    def list_archetypes() -> None:
        """List available forecaster archetypes for synthetic data generation.

        Shows all available archetype names with their descriptions.
        Use these when configuring forecasters in generate_dataset.

        :Example:
            python simulate.py list_archetypes
        """
        archetypes = SyntheticGenerator.list_archetypes()

        print("\nAvailable Forecaster Archetypes")
        print("=" * 60)
        print("\nUse these when configuring forecasters in generate_dataset.")
        print()

        for name, description in archetypes.items():
            print(f"  {name:15} - {description}")

        print()
        print("Specification format: archetype:count,archetype:count,...")
        print("Examples:")
        print("  skilled:3,noisy:2")
        print("  skilled:2,biased:1,intermittent:1")
        print("=" * 60 + "\n")

    @staticmethod
    def info() -> None:
        """Display information about the simulator.

        Shows version, available commands, and configuration.

        :Example:
            python simulate.py info
        """
        print("""
Forecast Simulator v1.1.0
=========================

A standalone simulation environment for testing collaborative
forecasting algorithms without API or database access.

Commands:
  quickstart        Generate demo dataset and run simulation (fastest start)
  run               Run forecast simulation
  list_datasets     List available datasets
  create_dataset    Create new dataset from template
  generate_dataset  Generate synthetic dataset (interactive wizard)
  list_archetypes   List available forecaster archetypes
  validate_dataset  Validate dataset structure and content
  evaluate          Evaluate simulation results
  plot              Generate plots from simulation results
  info              Show this information

Quick Start:
  1. Fastest way - run quickstart:
     python simulate.py quickstart

  2. Or generate your own dataset:
     python simulate.py generate_dataset

  3. Then run simulation:
     python simulate.py run --n_sessions=10

   4. Evaluate results:
     python simulate.py evaluate output/<dataset>/<timestamp>/

   5. Plot results:
     python simulate.py plot output/<dataset>/<timestamp>/

   6. Plot with individual forecasters:
     python simulate.py plot output/<dataset>/<timestamp>/ --plot_individuals

Synthetic Data Generation:
  Generate controlled test datasets for benchmarking using
  the interactive wizard:

  python simulate.py generate_dataset

  The wizard will guide you through:
  - Choosing power type (wind/solar)
  - Setting dataset size and capacity
  - Configuring forecaster archetypes
  - Adding test scenarios (regime change, dropout, etc.)

  # List available forecaster archetypes
  python simulate.py list_archetypes

Verbosity:
  Control output verbosity with --log_level:
    --log_level=quiet    Only errors and final summary
    --log_level=warning  Warnings and above
    --log_level=info     Default - session progress
    --log_level=debug    Detailed debugging info

For detailed help on any command:
  python simulate.py <command> --help
        """)


if __name__ == "__main__":
    fire.Fire(SimulatorTasks)
