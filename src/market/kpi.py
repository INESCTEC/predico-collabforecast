import numpy as np
import pandas as pd

from ..assessment.skills import mse_boxplot_df


class KpiClass:
    """
    A class to represent an incentive class for market participants.
    """

    def __init__(self):
        # -- Scores:
        self.scores = None
        self.daily_scores = None
        self.daily_scores_w_pen = None
        self.month_scores = None
        self.month_scores_w_pen = None
        self.month_scores_ranked = None
        self.best_forecaster = None
        self.track = None

        # -- Distributions:
        self.residual_distributions = {}
        self.boxplot_by_power = {}

        # -- Ranks:
        self.daily_ranks = None
        self.month_ranks = None

        # -- League assignments:
        self.league = {}
        self.league_thresholds = {}
        self.nr_participants = None
        self.n_days_w_penalties = None
        self.days_wout_submissions = None

    def load_scores(self, scores, track):
        self.scores = scores.copy()
        self.track = track
        return self

    def __check_loaded_scores(self):
        if self.scores is None:
            raise ValueError("Scores data not loaded.")
        if not isinstance(self.scores, pd.DataFrame):
            raise TypeError("Scores should be a pandas DataFrame.")

    def remove_dates(self, date_list):
        """
        Remove entries from scores with target_day in date_list.
        :param date_list: List of date strings to remove from scores.

        :raises ValueError: If scores data is not loaded.
        :raises TypeError: If date_list is not a list of strings.

        """
        self.__check_loaded_scores()
        if not isinstance(date_list, list):
            raise TypeError("date_list should be a list.")

        if len(date_list) == 0:
            return self
        else:
            if not isinstance(date_list[0], str):
                raise TypeError("date_list should be a list of date strings.")

            # Remove entries with target_day in date_list
            self.scores = self.scores[
                ~self.scores["target_day"].astype(str).isin(date_list)
            ]
            return self

    def remove_fixed_payment(self, participation_type):
        self.__check_loaded_scores()
        # Remove users with fixed payment:
        for user, is_fixed_payment in participation_type.items():
            if is_fixed_payment:
                self.scores = self.scores[self.scores["user_id"] != user]

    def daily_ranking(self):
        # Copy month scores to avoid modifying the original DataFrame
        self.daily_ranks = self.scores.copy()
        # Calculate new col with ranking per user and challenge:
        self.daily_ranks["rank"] = (
            self.daily_ranks.groupby(["challenge_id", "target_day"])["value"]
            .rank(method="dense", ascending=True)
            .astype(int)
        )
        self.month_ranks = (
            self.daily_ranks[["user_id", "rank"]]
            .groupby("user_id")
            .mean()["rank"]
            .sort_values()
        )

        self.month_ranks = {
            "avg": self.daily_ranks[["user_id", "rank"]]
            .groupby("user_id")
            .mean()["rank"]
            .sort_values(),
            "min": self.daily_ranks[["user_id", "rank"]]
            .groupby("user_id")
            .min()["rank"]
            .sort_values(),
            "max": self.daily_ranks[["user_id", "rank"]]
            .groupby("user_id")
            .max()["rank"]
            .sort_values(),
            "median": self.daily_ranks[["user_id", "rank"]]
            .groupby("user_id")
            .median()["rank"]
            .sort_values(),
            "std": self.daily_ranks[["user_id", "rank"]]
            .groupby("user_id")
            .std()["rank"]
            .sort_values()
            .fillna(0),  # std of single-value series is NaN,
            "count": self.daily_ranks[["user_id", "rank"]]
            .groupby("user_id")
            .count()["rank"]
            .sort_values(),
        }

        # Number of forecasters submitting forecasts during the month
        self.nr_participants = len(self.month_ranks["avg"].index)

        return self.daily_ranks

    def average_scores(self):
        """
        Calculate average scores for each forecaster over the month,
        applying penalties for missing daily submissions.

        :raises ValueError: If scores data is not loaded.

        """
        self.__check_loaded_scores()
        # Create pivot of scores per day of the month:
        self.daily_scores = pd.pivot_table(
            data=self.scores, index="user_id", columns="target_day", values="value"
        )

        # Calculate average monthly scores (without penalties):
        self.month_scores = {
            "avg": self.daily_scores.mean(axis=1).sort_values(),
            "min": self.daily_scores.min(axis=1).sort_values(),
            "max": self.daily_scores.max(axis=1).sort_values(),
            "median": self.daily_scores.median(axis=1).sort_values(),
            "std": self.daily_scores.std(axis=1)
            .sort_values()
            .fillna(0),  # std of single-value series is NaN
        }

    def average_scores_w_penalty(self):
        # For each user, check which days he will be penalized at:
        self.days_wout_submissions = self.daily_scores.isnull()
        # Convert missing_columns columns to string:
        # self.days_wout_submissions.columns = days_wout_submissions.columns.astype(str)
        self.n_days_w_penalties = self.days_wout_submissions.sum(axis=1)
        # Calculate penalties for missing submissions:
        # Note that we need to calculate this before removing forecasters
        penalties = self.daily_scores.quantile(0.75)

        # Fill missing daily submissions with penalty
        # Note that we'll be using a "bad but not catastrophic" value
        # for missing submissions, specifically the Q75 of daily avg scores
        self.daily_scores_w_pen = self.daily_scores.fillna(penalties).copy()

        # Calculate daily avg scores w/ penalties, per forecaster:
        self.month_scores_w_pen = {
            "avg": self.daily_scores_w_pen.mean(axis=1).sort_values(),
            "min": self.daily_scores_w_pen.min(axis=1).sort_values(),
            "max": self.daily_scores_w_pen.max(axis=1).sort_values(),
            "median": self.daily_scores_w_pen.median(axis=1).sort_values(),
            "std": self.daily_scores_w_pen.std(axis=1)
            .sort_values()
            .fillna(0),  # std of single-value series is NaN
        }

        self.month_scores_ranked = (
            self.month_scores_w_pen["avg"]
            .rank(method="dense", ascending=True)
            .astype(int)
            .sort_values()
            .to_dict()
        )

    def find_forecaster_league(self):
        if self.daily_scores_w_pen is None:
            raise ValueError(
                "Average scores with penalties not calculated. "
                "Run average_scores() first."
            )

        quali_criteria = 5  # minimum days with submissions to be qualified

        # Step 1 - drop forecasters with more than 5 days of non-submissions:
        # Important: we use the original daily_scores (without penalties)
        # to identify forecasters with too many NaNs. Otherwise, it has no
        # nulls due to the penalty filling.
        unqualified_ = list(
            self.n_days_w_penalties[self.n_days_w_penalties > quali_criteria].index
        )

        # Remove forecasters from month scores w/ penalties:
        month_scores_ = self.month_scores_w_pen["avg"][
            ~np.isin(self.month_scores_w_pen["avg"].index, unqualified_)
        ].sort_values()
        # Step 2: Split forecasters into the different leagues:
        elite = (
            list(month_scores_.iloc[:5].index) if len(month_scores_) != 0 else []
        )  # ranks 1-5
        challenger = (
            list(month_scores_.iloc[5:10].index) if len(month_scores_) >= 6 else []
        )  # ranks 6-10
        runner_up = (
            month_scores_.index[10] if len(month_scores_) >= 11 else []
        )  # rank 11
        others = (
            list(month_scores_.iloc[11:].index) if len(month_scores_) >= 12 else []
        )  # rank 12+

        # Store best forecaster info:
        self.best_forecaster = elite[0] if elite != [] else None

        for user_id in elite:
            self.league[user_id] = "elite"
        for user_id in challenger:
            self.league[user_id] = "challenger"
        if runner_up != []:
            self.league[runner_up] = "runner_up"
        for user_id in others:
            self.league[user_id] = "unassigned"
        for user_id in unqualified_:
            self.league[user_id] = "unqualified"

        return self.league

    def calculate_league_thresholds(self):
        elite_thresholds = []
        challenger_thresholds = []
        runner_up_thresholds = []

        # Compute cumulative mean across columns (axis=1) for each row
        cumulative_avg = self.daily_scores_w_pen.T.expanding().mean().T

        for day in cumulative_avg.columns:
            daily_scores_sorted = cumulative_avg[day].sort_values()

            elite_thresholds.append(
                daily_scores_sorted.iloc[4] if len(daily_scores_sorted) >= 5 else np.nan
            )
            challenger_thresholds.append(
                daily_scores_sorted.iloc[9]
                if len(daily_scores_sorted) >= 10
                else np.nan
            )
            runner_up_thresholds.append(
                daily_scores_sorted.iloc[10]
                if len(daily_scores_sorted) >= 11
                else np.nan
            )

        # Create a json with "target_day" and "value" for each league thresholds
        dates_ = self.daily_scores_w_pen.columns.astype(str).tolist()
        elite_thresholds = [
            {"target_day": dates_[i], "value": elite_thresholds[i]}
            for i in range(len(dates_))
        ]
        challenger_thresholds = [
            {"target_day": dates_[i], "value": challenger_thresholds[i]}
            for i in range(len(dates_))
        ]
        runner_up_thresholds = [
            {"target_day": dates_[i], "value": runner_up_thresholds[i]}
            for i in range(len(dates_))
        ]

        self.league_thresholds = {
            "elite": elite_thresholds,
            "challenger": challenger_thresholds,
            "runner_up": runner_up_thresholds,
        }

    def calculate_distributions(self, forecasts, observed):
        """
        Calculate residual distributions and boxplots by power level
        for each forecaster. Per forecaster, establish a comparison with the
        best forecaster. Note that forecasters may have submitted forecasts
        for different time periods, so the distributions and boxplots are
        calculated only for the timestamps where each forecaster has data.

        :param forecasts: DataFrame with forecasts. Expected columns:
                          ["datetime", "user_id", "variable", "value"]
        :param observed: DataFrame with observed values. Expected columns:
                         ["datetime", "value"]
        """

        forecasters_list = forecasts["user_id"].unique()
        # Prepare observed and forecasts dataframes:
        observed = (
            observed.set_index("datetime").copy().rename(columns={"value": "observed"})
        )
        # We just need deterministic forecasts:
        forecasts = (
            forecasts[forecasts["variable"] == "q50"]
            .set_index("datetime")
            .copy()
            .rename(columns={"value": "forecast"})
        )

        self.residual_distributions = {}
        self.boxplot_by_power = {}
        for user_id in forecasters_list:
            if self.track == "probabilistic":
                # Set these plots to empty for probabilistic track:
                self.residual_distributions[str(user_id)] = {}
                self.boxplot_by_power[str(user_id)] = []
                continue

            # Merge forecast and observed:
            data_ = (
                forecasts[forecasts["user_id"] == user_id]
                .join(observed, how="left")
                .dropna()
            )

            if data_.dropna().empty:
                # No overlapping data between forecasts and observed
                self.residual_distributions[str(user_id)] = {}
                self.boxplot_by_power[str(user_id)] = []
                continue

            best_forecaster_ = forecasts[
                forecasts["user_id"].astype(str) == self.best_forecaster
            ].join(observed, how="left")

            # -----------------------
            # Calculate Residuals:
            # -----------------------
            # Deterministic forecast residual:
            # -- Current forecaster:
            data_["residual"] = data_["forecast"] - data_["observed"]
            # -- Best forecaster (month eval):
            best_forecaster_["residual"] = (
                best_forecaster_["forecast"] - best_forecaster_["observed"]
            )

            # Prepare distribution data:
            # -- Current forecaster:
            min_ = data_["residual"].min()
            max_ = data_["residual"].max()
            # -- Best forecaster:
            min_best_ = best_forecaster_["residual"].min()
            max_best_ = best_forecaster_["residual"].max()
            # calculate actual max and min for bins & set bins:
            min_ = min(min_, min_best_)
            max_ = max(max_, max_best_)
            max_abs = max(abs(min_), abs(max_))
            bins = np.linspace(-max_abs, max_abs, num=20)
            # Calculate histograms:
            hist, bin_edges = np.histogram(
                data_["residual"].dropna(), bins=bins, density=False
            )
            hist_best, _ = np.histogram(
                best_forecaster_["residual"].dropna(), bins=bins, density=False
            )
            # Store in dict:
            self.residual_distributions[str(user_id)] = {
                "bin_edges": [round(x, 3) for x in bin_edges.tolist()],
                "selected_user_counts": hist.tolist(),
                "best_forecaster_counts": hist_best.tolist(),
            }

            # --------------------------------
            # Calculate MSE per power level:
            # --------------------------------
            # Get histogram bins:
            range_min = np.floor(data_["observed"].min())
            range_max = np.ceil(data_["observed"].max())
            bins = np.linspace(range_min, range_max, num=5)  # 5 intervals
            # Calculate MSE per bin:
            # -- Current forecaster:
            data_["mse"] = data_["residual"] ** 2
            data_["power_level"] = pd.cut(
                data_["observed"], bins=bins, include_lowest=True
            )
            mse_per_level = (
                data_.groupby("power_level", observed=False)
                .apply(mse_boxplot_df)
                .reset_index()
            )
            mse_per_level.columns = ["bin", "selected_user"]
            # -- Best forecaster:
            best_forecaster_["mse"] = best_forecaster_["residual"] ** 2
            best_forecaster_["power_level"] = pd.cut(
                best_forecaster_["observed"], bins=bins, include_lowest=True
            )
            mse_per_level_best = (
                best_forecaster_.groupby("power_level", observed=False)
                .apply(mse_boxplot_df)
                .reset_index()
            )
            mse_per_level_best.columns = ["bin", "best_forecaster"]

            # merge mse_per_level with mse_per_level_best to include best forecaster scores
            mse_per_level = mse_per_level.merge(
                mse_per_level_best, on="bin", how="inner"
            )

            self.boxplot_by_power[str(user_id)] = [
                {
                    "bin": str(row.bin),
                    "selected_user": row.selected_user,
                    "best_forecaster": row.best_forecaster,
                }
                for row in mse_per_level.itertuples()
            ]
