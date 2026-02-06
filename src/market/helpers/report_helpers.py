import numpy as np


def aggregated_metrics_json(
    year,
    month,
    resource_id,
    metric,
    track,
    nr_participants,
    participation_type,
    days_wout_submissions,
    n_days_w_penalties,
    month_scores,
    month_scores_w_pen,
    month_ranks,
    daily_ranks,
    daily_scores_w_pen,
    league_assignments,
    month_scores_ranked,
    league_thresholds,
    residual_distributions,
    boxplot_by_power,
):
    forecasters = list(month_scores_w_pen["avg"].index)

    report_json = []

    for user_id in forecasters:
        metadata = {
            "user": user_id,
            "resource": resource_id,
            "year": year,
            "month": month,
            "metric": metric,
            "track": track,
        }

        ########################
        # Participation Stats
        ########################
        participation_stats = {
            "days_with_submissions": int(month_ranks["count"].loc[user_id]),
            "days_in_period": int(month_ranks["count"].max()),
            "participation_rate": (
                month_ranks["count"].loc[user_id] / month_ranks["count"].max()
            )
            * 100,
            "n_days_w_penalties": int(n_days_w_penalties.get(user_id, 0)),
            "nr_participants": nr_participants,
        }

        #########################
        # Monthly Score Stats
        #########################
        # -- Without Penalties
        month_score_stats = {
            "avg_score": float(month_scores["avg"].loc[user_id]),
            "best_score": float(month_scores["min"].loc[user_id]),
            "worst_score": float(month_scores["max"].loc[user_id]),
            "median_score": float(month_scores["median"].loc[user_id]),
            "std_score": float(month_scores["std"].loc[user_id]),
        }
        # -- With Penalties
        month_score_w_pen_stats = {
            "avg_score_w_pen": float(month_scores_w_pen["avg"].loc[user_id]),
            "best_score_w_pen": float(month_scores_w_pen["min"].loc[user_id]),
            "worst_score_w_pen": float(month_scores_w_pen["max"].loc[user_id]),
            "median_score_w_pen": float(month_scores_w_pen["median"].loc[user_id]),
            "std_score_w_pen": float(month_scores_w_pen["std"].loc[user_id]),
            "avg_score_w_pen_rank": int(month_scores_ranked.get(user_id, None)),
        }

        # -- Create month scores JSON (for month comparison):
        # ({"user_id": str, "score": float}, ...)
        month_scores_json = []
        for uid in month_scores_w_pen["avg"].index:
            if n_days_w_penalties.loc[uid] > 5:
                # exclude users with more than 5 penalty days
                # means that they do not have submitted forecasts for a significant
                # portion of the month
                # todo: this value (5) should be centralized
                continue

            month_scores_json.append(
                {
                    "user_id": uid,
                    "score": float(month_scores_w_pen["avg"].loc[uid]),
                }
            )

        # -- Create daily scores with penalties and penalty flag
        # ({"target_day": str, "score": float, "is_penalty": bool}, ...)
        scores_df_ = (
            daily_scores_w_pen.loc[user_id]
            .to_frame()
            .rename(columns={user_id: "score"})
        )
        penalties_df_ = (
            days_wout_submissions.loc[user_id]
            .to_frame()
            .rename(columns={user_id: "is_penalty"})
        )
        aux_ = scores_df_.join(penalties_df_).reset_index()
        aux_["target_day"] = aux_["target_day"].astype(str)
        daily_scores_json = aux_.to_dict(orient="records")

        #########################
        # Daily Ranking Stats
        #########################
        # -- Without Penalties (penalties are only considered in league eval)
        month_rank_stats = {
            "avg_rank": int(month_ranks["avg"].loc[user_id]),
            "best_rank": int(month_ranks["min"].loc[user_id]),
            "worst_rank": int(month_ranks["max"].loc[user_id]),
            "median_rank": float(month_ranks["median"].loc[user_id]),
            "std_rank": float(month_ranks["std"].loc[user_id]),
            "podium_count": int(
                (daily_ranks[daily_ranks["user_id"] == user_id]["rank"] <= 3).sum()
            ),
            "podium_pct": float(
                (daily_ranks[daily_ranks["user_id"] == user_id]["rank"] <= 3).sum()
                / len(daily_ranks[daily_ranks["user_id"] == user_id])
                * 100
            ),
        }
        # -- Rank histogram (currently just considering 3 bins)
        rank_distribution = {
            "rank_1_5": int(
                (daily_ranks[daily_ranks["user_id"] == user_id]["rank"] <= 5).sum()
            ),
            "rank_6_10": int(
                (
                    (daily_ranks[daily_ranks["user_id"] == user_id]["rank"] > 5)
                    & (daily_ranks[daily_ranks["user_id"] == user_id]["rank"] <= 10)
                ).sum()
            ),
            "rank_11_plus": int(
                (daily_ranks[daily_ranks["user_id"] == user_id]["rank"] > 10).sum()
            ),
        }

        # Daily ranks JSON
        # Create list of daily ranks:
        daily_ranks_json = daily_ranks.copy()
        # Convert "target_day" to string for JSON serialization
        daily_ranks_json["target_day"] = daily_ranks_json["target_day"].astype(str)
        daily_ranks_json["total_forecasters"] = len(forecasters)
        daily_ranks_json = daily_ranks_json[daily_ranks_json["user_id"] == user_id][
            ["target_day", "rank", "total_forecasters"]
        ].to_dict(orient="records")

        ###########################
        # Extra Stats:
        ###########################
        avg_score_podium = month_scores_w_pen["avg"].nsmallest(3).mean()
        if avg_score_podium > 0:
            diff_avg_score_podium = float(
                month_scores_w_pen["avg"].loc[user_id] - avg_score_podium
            )
        else:
            diff_avg_score_podium = np.nan

        is_fixed_payment = participation_type[user_id]

        report_json.append(
            {
                **metadata,
                **participation_stats,
                **month_score_stats,
                **month_rank_stats,
                **month_score_w_pen_stats,
                "is_fixed_payment": is_fixed_payment,
                "league_id": league_assignments.get(user_id, "unassigned"),
                "rank_distribution_json": rank_distribution,
                "daily_scores_json": daily_scores_json,
                "daily_ranks_json": daily_ranks_json,
                "month_scores_json": month_scores_json,
                "avg_score_w_pen_podium": avg_score_podium,
                "diff_podium_score_w_pen": diff_avg_score_podium,
                "league_thresholds_json": league_thresholds,
                "residual_distributions_json": residual_distributions.get(user_id, {}),
                "boxplot_by_power_json": boxplot_by_power.get(user_id, {}),
            }
        )
    return report_json
