"""
Forecast visualization module for the community simulator.

Provides plotting capabilities for comparing forecast strategies against
observed values and displaying performance metrics.

Example::

    from simulator.community.core.plots import ForecastPlotter

    plotter = ForecastPlotter(forecasts_df, observed_df)
    plotter.show_all()
"""

from __future__ import annotations

from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from loguru import logger

from .metrics import mae, pinball_loss, rmse, winkler_score


# Strategy display configuration
STRATEGY_STYLES = {
    "weighted_avg": {"color": "#2ecc71", "linestyle": "-", "label": "Weighted Average"},
    "arithmetic_mean": {
        "color": "#3498db",
        "linestyle": "--",
        "label": "Arithmetic Mean",
    },
    "best_forecaster": {
        "color": "#9b59b6",
        "linestyle": ":",
        "label": "Best Forecaster",
    },
}

OBSERVED_STYLE = {
    "color": "#2c3e50",
    "linestyle": "-",
    "linewidth": 2,
    "label": "Observed",
}


class ForecastPlotter:
    """Generate forecast comparison and metrics plots.

    This class provides methods to visualize forecast results from the
    community simulator, comparing different ensemble strategies against
    observed values.

    :param forecasts_df: DataFrame with forecast data containing columns:
        datetime, variable, value, strategy, buyer_resource_id
    :param observed_df: DataFrame with observed values, indexed by datetime
    :param resource_id: Optional resource ID to filter data (default: first available)

    Example::

        plotter = ForecastPlotter(forecasts_df, observed_df)
        plotter.plot_strategy_comparison()
        plotter.plot_prediction_intervals()
        plotter.plot_metrics_summary()
        plotter.show_all()
    """

    def __init__(
        self,
        forecasts_df: pd.DataFrame,
        observed_df: pd.DataFrame,
        resource_id: str | None = None,
    ) -> None:
        """Initialize the plotter with forecast and observed data.

        :param forecasts_df: DataFrame with forecast data
        :param observed_df: DataFrame with observed values
        :param resource_id: Optional resource ID to filter
        """
        self.raw_forecasts = forecasts_df.copy()
        self.raw_observed = observed_df.copy()

        # Determine resource ID
        if resource_id is None and "buyer_resource_id" in forecasts_df.columns:
            resource_id = forecasts_df["buyer_resource_id"].iloc[0]
        self.resource_id = resource_id

        # Prepare data
        self._prepare_data()

    def _prepare_data(self) -> None:
        """Prepare and pivot data for plotting."""
        df = self.raw_forecasts.copy()

        # Filter by resource if specified
        if self.resource_id and "buyer_resource_id" in df.columns:
            df = df[df["buyer_resource_id"] == self.resource_id]

        # Parse datetime
        if "datetime" in df.columns:
            df["datetime"] = pd.to_datetime(df["datetime"])
            df = df.set_index("datetime")

        # Pivot to get strategies as columns for each variable
        # Result: MultiIndex columns (strategy, variable)
        self.forecasts = df.pivot_table(
            index=df.index,
            columns=["strategy", "variable"],
            values="value",
            aggfunc="first",
        )

        # Get list of strategies and variables
        if "strategy" in df.columns:
            self.strategies = df["strategy"].unique().tolist()
        else:
            self.strategies = []

        if "variable" in df.columns:
            self.variables = df["variable"].unique().tolist()
        else:
            self.variables = []

        # Prepare observed data
        obs = self.raw_observed.copy()
        if not isinstance(obs.index, pd.DatetimeIndex) and "datetime" in obs.columns:
            obs["datetime"] = pd.to_datetime(obs["datetime"])
            obs = obs.set_index("datetime")

        # Handle column naming
        if "observed" in obs.columns:
            self.observed = obs["observed"]
        elif "value" in obs.columns:
            self.observed = obs["value"]
        elif self.resource_id and self.resource_id in obs.columns:
            self.observed = obs[self.resource_id]
        else:
            # Use first numeric column
            numeric_cols = obs.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                self.observed = obs[numeric_cols[0]]
            else:
                self.observed = pd.Series(dtype=float)

        logger.info(
            f"Prepared data: {len(self.strategies)} strategies, "
            f"{len(self.variables)} variables, {len(self.forecasts)} time points"
        )

    def plot_strategy_comparison(
        self,
        quantile: str = "q50",
        figsize: tuple[int, int] = (14, 6),
        ax: plt.Axes | None = None,
    ) -> plt.Figure | None:
        """Plot all strategies vs observed for a specific quantile.

        Creates a time-series line chart comparing forecasts from different
        ensemble strategies against observed values.

        :param quantile: Quantile to plot (default: "q50")
        :param figsize: Figure size as (width, height)
        :param ax: Optional matplotlib Axes to plot on

        :return: Figure object if ax was None, else None
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=figsize)
        else:
            fig = None

        # Plot observed
        obs_aligned = self.observed.reindex(self.forecasts.index)
        ax.plot(
            obs_aligned.index,
            obs_aligned.values,
            **OBSERVED_STYLE,
        )

        # Plot each strategy
        for strategy in self.strategies:
            if (strategy, quantile) in self.forecasts.columns:
                style = STRATEGY_STYLES.get(
                    strategy,
                    {"color": "#95a5a6", "linestyle": "-", "label": strategy},
                )
                ax.plot(
                    self.forecasts.index,
                    self.forecasts[(strategy, quantile)],
                    color=style["color"],
                    linestyle=style["linestyle"],
                    label=style["label"],
                    linewidth=1.5,
                )

        ax.set_xlabel("Date")
        ax.set_ylabel("Power (MW)")
        ax.legend(loc="best")
        ax.grid(True, alpha=0.3)

        # Rotate x-axis labels
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha="right")

        if fig:
            fig.canvas.manager.set_window_title(
                f"Forecast Comparison - {quantile.upper()}"
            )
            fig.tight_layout()
        return fig

    def plot_prediction_intervals(
        self,
        strategy: str = "weighted_avg",
        figsize: tuple[int, int] = (14, 6),
        ax: plt.Axes | None = None,
    ) -> plt.Figure | None:
        """Plot prediction interval (Q10-Q90) with Q50 and observed.

        Creates a time-series plot with a shaded band representing the
        80% prediction interval (Q10 to Q90), the median forecast (Q50),
        and observed values.

        :param strategy: Strategy to plot (default: "weighted_avg")
        :param figsize: Figure size as (width, height)
        :param ax: Optional matplotlib Axes to plot on

        :return: Figure object if ax was None, else None
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=figsize)
        else:
            fig = None

        # Check if we have the required quantiles
        has_q10 = (strategy, "q10") in self.forecasts.columns
        has_q50 = (strategy, "q50") in self.forecasts.columns
        has_q90 = (strategy, "q90") in self.forecasts.columns

        if not (has_q10 and has_q90):
            logger.warning(f"Strategy '{strategy}' missing Q10/Q90 for interval plot")
            if fig:
                ax.text(
                    0.5,
                    0.5,
                    f"No interval data for {strategy}",
                    ha="center",
                    va="center",
                    transform=ax.transAxes,
                )
            return fig

        idx = self.forecasts.index
        q10 = self.forecasts[(strategy, "q10")]
        q90 = self.forecasts[(strategy, "q90")]

        # Plot prediction interval band
        ax.fill_between(
            idx,
            q10,
            q90,
            alpha=0.3,
            color="#3498db",
            label="80% Prediction Interval (Q10-Q90)",
        )

        # Plot Q50 if available
        if has_q50:
            q50 = self.forecasts[(strategy, "q50")]
            ax.plot(
                idx,
                q50,
                color="#2980b9",
                linestyle="-",
                linewidth=1.5,
                label="Forecast (Q50)",
            )

        # Plot observed
        obs_aligned = self.observed.reindex(idx)
        ax.plot(
            obs_aligned.index,
            obs_aligned.values,
            **OBSERVED_STYLE,
        )

        style = STRATEGY_STYLES.get(strategy, {"label": strategy})
        ax.set_xlabel("Date")
        ax.set_ylabel("Power (MW)")
        ax.legend(loc="best")
        ax.grid(True, alpha=0.3)

        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha="right")

        if fig:
            fig.canvas.manager.set_window_title(
                f"Prediction Interval - {style.get('label', strategy)}"
            )
            fig.tight_layout()
        return fig

    def compute_metrics(self) -> pd.DataFrame:
        """Compute performance metrics for all strategies.

        Calculates RMSE, MAE, and Winkler score for each strategy.

        :return: DataFrame with metrics per strategy
        """
        metrics_data = []

        # Align observed with forecasts
        obs_aligned = self.observed.reindex(self.forecasts.index).dropna()

        for strategy in self.strategies:
            row = {"strategy": strategy}

            # RMSE and MAE for Q50
            if (strategy, "q50") in self.forecasts.columns:
                q50_forecast = self.forecasts[(strategy, "q50")]
                df_q50 = pd.DataFrame(
                    {
                        "observed": obs_aligned,
                        "forecast": q50_forecast.reindex(obs_aligned.index),
                    }
                ).dropna()

                if len(df_q50) > 0:
                    row["rmse"] = rmse(df_q50)
                    row["mae"] = mae(df_q50)
                    row["pinball_q50"] = pinball_loss(df_q50, "q50")

            # Pinball loss for Q10 and Q90
            for q in ["q10", "q90"]:
                if (strategy, q) in self.forecasts.columns:
                    q_forecast = self.forecasts[(strategy, q)]
                    df_q = pd.DataFrame(
                        {
                            "observed": obs_aligned,
                            "forecast": q_forecast.reindex(obs_aligned.index),
                        }
                    ).dropna()

                    if len(df_q) > 0:
                        row[f"pinball_{q}"] = pinball_loss(df_q, q)

            # Winkler score (needs Q10 and Q90)
            has_q10 = (strategy, "q10") in self.forecasts.columns
            has_q90 = (strategy, "q90") in self.forecasts.columns

            if has_q10 and has_q90:
                df_winkler = pd.DataFrame(
                    {
                        "observed": obs_aligned,
                        "q10": self.forecasts[(strategy, "q10")].reindex(
                            obs_aligned.index
                        ),
                        "q90": self.forecasts[(strategy, "q90")].reindex(
                            obs_aligned.index
                        ),
                    }
                ).dropna()

                if len(df_winkler) > 0:
                    row["winkler"] = winkler_score(df_winkler)

            metrics_data.append(row)

        return pd.DataFrame(metrics_data)

    def plot_metrics_summary(
        self,
        figsize: tuple[int, int] = (12, 8),
    ) -> plt.Figure:
        """Display metrics summary as bar charts.

        Creates a figure with bar charts comparing key metrics across
        strategies: RMSE, MAE, and Winkler Score.

        :param figsize: Figure size as (width, height)

        :return: Figure object
        """
        metrics_df = self.compute_metrics()

        # Metrics to plot
        plot_metrics = []
        if "rmse" in metrics_df.columns:
            plot_metrics.append(("rmse", "RMSE (MW)"))
        if "mae" in metrics_df.columns:
            plot_metrics.append(("mae", "MAE (MW)"))
        if "winkler" in metrics_df.columns:
            plot_metrics.append(("winkler", "Winkler Score"))

        n_metrics = len(plot_metrics)
        if n_metrics == 0:
            fig, ax = plt.subplots(figsize=figsize)
            ax.text(0.5, 0.5, "No metrics available", ha="center", va="center")
            return fig

        fig, axes = plt.subplots(1, n_metrics, figsize=figsize)
        if n_metrics == 1:
            axes = [axes]

        # Get strategy colors
        colors = [
            STRATEGY_STYLES.get(s, {"color": "#95a5a6"})["color"]
            for s in metrics_df["strategy"]
        ]

        # Get strategy labels
        labels = [
            STRATEGY_STYLES.get(s, {"label": s})["label"]
            for s in metrics_df["strategy"]
        ]

        for ax, (metric_col, metric_label) in zip(axes, plot_metrics):
            values = metrics_df[metric_col].fillna(0)
            x = range(len(values))

            bars = ax.bar(x, values, color=colors)
            ax.set_xticks(x)
            ax.set_xticklabels(labels, rotation=45, ha="right")
            ax.set_ylabel(metric_label)
            ax.set_title(metric_label)

            # Add value labels on bars
            for bar, val in zip(bars, values):
                if pd.notna(val) and val > 0:
                    ax.text(
                        bar.get_x() + bar.get_width() / 2,
                        bar.get_height(),
                        f"{val:.1f}",
                        ha="center",
                        va="bottom",
                        fontsize=9,
                    )

            ax.grid(True, alpha=0.3, axis="y")

        fig.canvas.manager.set_window_title("Strategy Performance Metrics")
        fig.tight_layout()
        # Adjust bottom for rotated labels
        fig.subplots_adjust(bottom=0.18)
        return fig

    def print_metrics_table(self) -> None:
        """Print metrics summary as a formatted table to console."""
        metrics_df = self.compute_metrics()

        # Format for display
        display_df = metrics_df.copy()
        display_df["strategy"] = display_df["strategy"].apply(
            lambda s: STRATEGY_STYLES.get(s, {"label": s})["label"]
        )

        print("\n" + "=" * 70)
        print("STRATEGY PERFORMANCE METRICS")
        print("=" * 70)
        print(display_df.to_string(index=False))
        print("=" * 70 + "\n")

    def plot_forecaster_comparison(
        self,
        submissions_df: pd.DataFrame,
        figsize: tuple[int, int] = (14, 6),
        ax: plt.Axes | None = None,
    ) -> plt.Figure | None:
        """Plot individual forecasters vs ensembles vs observed.

        Creates a plot showing:
        - Individual forecaster Q50 predictions in grey
        - Ensemble strategy predictions in color
        - Observed values in black

        :param submissions_df: DataFrame with individual forecaster submissions
            Expected columns: datetime, forecaster_id, variable, value
        :param figsize: Figure size as (width, height)
        :param ax: Optional matplotlib Axes to plot on

        :return: Figure object if ax was None, else None
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=figsize)
        else:
            fig = None

        # Parse datetime in submissions if needed
        subs_df = submissions_df.copy()
        if "datetime" in subs_df.columns:
            subs_df["datetime"] = pd.to_datetime(subs_df["datetime"])

        # Plot individual forecasters in grey (Q50 only)
        q50_submissions = subs_df[subs_df["variable"] == "q50"]
        if not q50_submissions.empty:
            forecaster_ids = q50_submissions["forecaster_id"].unique()
            for i, forecaster_id in enumerate(forecaster_ids):
                fc_data = q50_submissions[
                    q50_submissions["forecaster_id"] == forecaster_id
                ]
                fc_data = fc_data.set_index("datetime").sort_index()

                # Only add label for first forecaster to avoid legend clutter
                label = "Individual Forecasters" if i == 0 else None
                ax.plot(
                    fc_data.index,
                    fc_data["value"],
                    color="#95a5a6",
                    alpha=0.5,
                    linewidth=1,
                    label=label,
                )

        # Plot ensemble strategies in color (Q50 only)
        for strategy in self.strategies:
            if (strategy, "q50") in self.forecasts.columns:
                style = STRATEGY_STYLES.get(
                    strategy,
                    {"color": "#e74c3c", "linestyle": "-", "label": strategy},
                )
                ax.plot(
                    self.forecasts.index,
                    self.forecasts[(strategy, "q50")],
                    color=style["color"],
                    linewidth=2,
                    label=style["label"],
                )

        # Plot observed in black
        obs_aligned = self.observed.reindex(self.forecasts.index)
        if not obs_aligned.empty:
            ax.plot(
                obs_aligned.index,
                obs_aligned.values,
                **OBSERVED_STYLE,
            )

        ax.set_xlabel("Date")
        ax.set_ylabel("Power (MW)")
        ax.set_title("Forecaster Comparison: Individual vs Ensemble")
        ax.legend(loc="best")
        ax.grid(True, alpha=0.3)

        # Rotate x-axis labels
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha="right")

        if fig:
            fig.canvas.manager.set_window_title("Forecaster Comparison")
            fig.tight_layout()
        return fig

    def show_all(self) -> None:
        """Display all plots interactively.

        Generates strategy comparison, prediction interval, and metrics
        summary plots, then displays them using plt.show().
        """
        logger.info("Generating forecast plots...")

        # Strategy comparison for Q50
        if "q50" in self.variables:
            self.plot_strategy_comparison(quantile="q50")

        # Prediction intervals for main strategy
        if "weighted_avg" in self.strategies:
            self.plot_prediction_intervals(strategy="weighted_avg")
        elif len(self.strategies) > 0:
            self.plot_prediction_intervals(strategy=self.strategies[0])

        # Metrics summary
        self.plot_metrics_summary()

        # Print table to console
        self.print_metrics_table()

        logger.info("Displaying plots...")
        plt.show()


def create_plotter_from_session_reports(
    session_reports: dict[int, dict[str, Any]],
    observed_df: pd.DataFrame,
    resource_id: str | None = None,
) -> ForecastPlotter:
    """Create a ForecastPlotter from SimulatorManager session reports.

    Convenience function to extract forecast data from session reports
    and create a plotter instance.

    :param session_reports: Dictionary of session reports from SimulatorManager
    :param observed_df: DataFrame with observed values
    :param resource_id: Optional resource ID to filter

    :return: Configured ForecastPlotter instance
    """
    all_forecasts = []

    for session_id, report in session_reports.items():
        forecasts = report.get("buyers_forecasts", [])
        all_forecasts.extend(forecasts)

    forecasts_df = pd.DataFrame(all_forecasts)

    return ForecastPlotter(forecasts_df, observed_df, resource_id)
