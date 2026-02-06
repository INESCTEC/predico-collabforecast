import os

import pandas as pd

from loguru import logger
from sqlalchemy import text
from dateutil.relativedelta import relativedelta
from conf import settings
from .postgres import PostgresDB


# #############################################################################
# Get Measurements Data for Session Resources:
# #############################################################################


def get_measurements_data(buyers_resources, start_date, end_date):
    db = PostgresDB.get_db_instance(config_name="default")
    logger.info("Querying measurements for resource list ...")
    measurements = {}
    for resource_id in sorted(buyers_resources):
        # Request data for buyer resource:
        logger.debug(f"Querying for resource ID {resource_id} ...")
        query = (
            f"select datetime, value "
            f"from raw_data "
            f"where resource_id='{resource_id}' "
            f"and datetime >= '{start_date}' "
            f"and datetime <= '{end_date}' "
            f"order by datetime asc;"
        )
        data = db.read_query_pandas(query)
        data.drop_duplicates(subset=["datetime"], inplace=True)
        if data.empty:
            logger.warning(f"No historical data for resource ID {resource_id}")
            measurements[resource_id] = data
        else:
            data = data.set_index("datetime")
            measurements[resource_id] = data
        logger.debug(f"Querying for resource ID {resource_id} ... Ok!")
    logger.success("Querying measurements for resource list ... Ok!")
    return measurements


def get_sellers_data(sellers_resources, start_date, end_date):
    db = PostgresDB.get_db_instance(config_name="default")
    logger.info("Querying forecasts for sellers forecasts list ...")
    sellers_users = list(set([x["user"] for x in sellers_resources]))
    forecasts = dict([(x, {}) for x in sellers_users])
    for resource in sellers_resources:
        # Request data for buyer resource:
        challenge_resource_id = resource["market_session_challenge_resource_id"]
        seller_user = resource["user"]
        variable = resource["variable"]
        logger.debug(
            f"Querying data (submissions) ..."
            f"\nchallenge_resource_id: {challenge_resource_id}"
            f"\nseller_user: {seller_user}"
            f"\nvariable: {variable}"
        )
        query_sub = (
            f"SELECT mssf.datetime, mssf.value "
            f"FROM market_session_submission_forecasts as mssf "
            f"INNER JOIN market_session_submission as mss "
            f"ON mssf.submission_id = mss.id "
            f"INNER JOIN market_session_challenge as msc "
            f"ON mss.market_session_challenge_id = msc.id "
            f"WHERE msc.resource_id='{challenge_resource_id}' "
            f"AND mss.user_id='{seller_user}' "
            f"AND mssf.datetime >= '{start_date}' "
            f"AND mssf.datetime <= '{end_date}' "
            f"AND mss.variable = '{variable}' ORDER BY datetime;"
        )
        # Get actual submitted forecasts for past challenges:
        data_submissions = db.read_query_pandas(query_sub)

        # Historical data loading disabled - models train only on submissions
        data_historical = pd.DataFrame()
        data_submissions["data_type"] = "submission"
        # Concat both data sources:
        data = pd.concat([data_submissions, data_historical], axis=0)
        if data.empty:
            logger.warning(
                f"No forecasts data from user {seller_user} to target resource {challenge_resource_id}"
            )
        else:
            data.drop_duplicates(subset=["datetime"], keep="first", inplace=True)
            data.sort_values(by="datetime", inplace=True)
            data = data.set_index("datetime")

        if challenge_resource_id not in forecasts[resource["user"]]:
            forecasts[resource["user"]][challenge_resource_id] = {}

        forecasts[seller_user][challenge_resource_id][variable] = data
        logger.debug("Querying data ... Ok!")
    logger.success("Querying forecasts for sellers forecasts list ... Ok!")
    return forecasts


def get_submissions_by_resource(resource_id, start_date, end_date):
    db = PostgresDB.get_db_instance(config_name="default")
    logger.info(f"Querying submissions for resource {resource_id} ...")

    query = (
        "SELECT mss.user_id as user_id, mss.id as submission_id, msc.id as challenge_id, mss.variable "
        "FROM market_session_submission AS mss "
        "INNER JOIN market_session_challenge as msc "
        "ON mss.market_session_challenge_id = msc.id "
        f"WHERE msc.resource_id='{resource_id}' "
        f"AND msc.target_day >= '{start_date}' "
        f"AND msc.target_day <= '{end_date}';"
    )

    data = db.read_query_pandas(query)
    if data.empty:
        logger.warning(f"No submission data from for resource_id {resource_id}")
    logger.info(f"Querying submissions for resource {resource_id} ... Ok!")
    return data


def get_sellers_submissions(sellers_users, challenge_id):
    db = PostgresDB.get_db_instance(config_name="default")
    logger.info(f"Querying submitted forecasts for challenge {challenge_id} ...")
    dataset = pd.DataFrame()
    for user_id in sellers_users:
        logger.debug(
            f"Querying data (submissions) ..."
            f"\nchallenge_id: {challenge_id}"
            f"\nseller_user: {user_id}"
        )
        query_sub = (
            f"SELECT mss.id as submission_id, mss.variable, mssf.datetime, mssf.value "
            f"FROM market_session_submission_forecasts as mssf "
            f"INNER JOIN market_session_submission as mss "
            f"ON mssf.submission_id = mss.id "
            f"INNER JOIN market_session_challenge as msc "
            f"ON mss.market_session_challenge_id = msc.id "
            f"WHERE mss.user_id='{user_id}' "
            f"AND msc.id = '{challenge_id}';"
        )
        data = db.read_query_pandas(query_sub)
        if data.empty:
            logger.warning(f"No forecasts data from user {user_id}")
            continue
        else:
            data["user_id"] = user_id
            dataset = pd.concat([dataset, data], axis=0)
            logger.debug("Querying data ... Ok!")

    # Convert DataFrame to dictionary (submissions / forecasts):
    submission_forecasts = {}

    if dataset.empty:
        logger.warning(f"No submissions found for challenge {challenge_id}.")
        return submission_forecasts
    else:
        for submission_id, group in dataset.groupby("submission_id"):
            submission_forecasts[submission_id] = group[
                ["variable", "datetime", "value", "user_id"]
            ].set_index("datetime")

    logger.success(f"Querying submitted forecasts for challenge {challenge_id} ... Ok!")
    return submission_forecasts


def get_challenges_for_scoring(start_date=None):
    db = PostgresDB.get_db_instance(config_name="default")
    logger.info(f"Querying challenges for scoring since {start_date} ...")

    # Important - just queries challenges without any submission scores
    # since start_date:
    query = f"""
SELECT
  msc.id AS challenge,
  msc.use_case,
  msc.start_datetime,
  msc.end_datetime,
  msc.resource_id AS resource
FROM market_session_challenge msc
WHERE msc.target_day >= '{start_date}'
  AND NOT EXISTS (
    SELECT 1
    FROM market_session_submission_scores msss
    JOIN market_session_submission mss ON msss.submission_id = mss.id
    WHERE mss.market_session_challenge_id = msc.id
  )
ORDER BY msc.target_day ASC;
    """

    # Query data:
    data = db.read_query_pandas(query)
    if data.empty:
        logger.warning("There are no challenges without weights assigned.")
        return []
    else:
        data["challenge"] = data["challenge"].astype(str)
        data["resource"] = data["resource"].astype(str)
    logger.debug("Querying challenges without weights assigned ... Ok!")

    result = data.to_dict(orient="records")

    return result


def delete_current_month_scores_and_weights(today_date):
    """
    Until the seventh day of the current month force delete of past
    submission scores, ensemble scores and contribution weights from
    the past month. Else only delete current month data.

    Returns the start date used for deletion (data deleted since start_date).

    IMPORTANT:
    Before deletion, a backup of the data is created in the scores directory,
    so data can be restored if needed (see settings.SCORES_DIR).

    :param today_date: datetime
    :return: start_date: str

    """
    db = PostgresDB.get_db_instance(config_name="default")
    today_date = today_date.strftime("%Y-%m-%d")

    if pd.to_datetime(today_date).day <= settings.SCORE_RECALC_GRACE_PERIOD_DAYS:
        # Until the grace period day of the current month - start from the past month
        start_date = (
            (pd.to_datetime(today_date) - relativedelta(months=1))
            .replace(day=1)
            .strftime("%Y-%m-%d")
        )  # noqa
    else:
        # Else only update the current month
        start_date = pd.to_datetime(today_date).replace(day=1).strftime("%Y-%m-%d")

    #####################################
    # Backup past submission scores:
    #####################################
    logger.info(f"Backing up past submission scores since {start_date} ...")
    query = f"""
SELECT 
	msss.*,
	msc.target_day 
FROM market_session_submission_scores AS msss
JOIN market_session_submission AS mss 
	ON mss.id = msss.submission_id 
JOIN market_session_challenge as msc 
	ON msc.id = mss.market_session_challenge_id
WHERE msc.target_day >= '{start_date}' AND msc.target_day <= '{today_date}';
"""
    data = db.read_query_pandas(query)
    submission_ids_to_delete = list(data["submission_id"].unique())  # from uuid to str
    filename = os.path.join(
        settings.SCORES_DIR, f"backup_sub_scores_{start_date}_{today_date}.csv"
    )
    data.to_csv(filename, index=False)
    logger.info(f"Backing up past submission scores since {start_date} ... Ok!")

    #####################################
    # Backup past ensemble scores:
    #####################################
    logger.info(f"Backing up past ensemble scores since {start_date} ...")
    query = f"""
SELECT 
    mses.*,
    msc.target_day 
FROM market_session_ensemble_scores AS mses
JOIN market_session_ensemble AS mse 
    ON mse.id = mses.ensemble_id 
JOIN market_session_challenge as msc 
    ON msc.id = mse.market_session_challenge_id
WHERE msc.target_day >= '{start_date}' AND msc.target_day <= '{today_date}';
    """
    data = db.read_query_pandas(query)
    ensemble_ids_to_delete = list(data["ensemble_id"].unique())  # from uuid to str
    filename = os.path.join(
        settings.SCORES_DIR, f"backup_ens_scores_{start_date}_{today_date}.csv"
    )
    data.to_csv(filename, index=False)
    logger.info(f"Backing up past ensemble scores since {start_date} ... Ok!")

    #####################################
    # Delete past submission scores:
    #####################################
    if len(submission_ids_to_delete) > 0:
        logger.info("Deleting past submission scores ...")
        query = f"""
DELETE FROM market_session_submission_scores 
WHERE submission_id IN ({",".join(f"'{item}'" for item in submission_ids_to_delete)});
        """
        with db.engine.connect() as connection:
            connection.execute(text(query))
            connection.commit()
        logger.success("Deleting past submission scores ... Ok!")

    #####################################
    # Delete past ensemble scores:
    #####################################
    if len(ensemble_ids_to_delete) > 0:
        logger.info("Deleting past ensemble scores ...")
        query = f"""
DELETE FROM market_session_ensemble_scores 
WHERE ensemble_id IN ({",".join(f"'{item}'" for item in ensemble_ids_to_delete)});
        """
        with db.engine.connect() as connection:
            connection.execute(text(query))
            connection.commit()
        logger.success("Deleting past ensemble scores ... Ok!")

    return start_date


def get_ensemble_forecasts(ensemble_models, challenge_id):
    db = PostgresDB.get_db_instance(config_name="default")
    logger.info(f"Querying ensemble forecasts for challenge {challenge_id} ...")
    dataset = pd.DataFrame()
    for model_id in ensemble_models:
        logger.debug(
            f"Querying data (ensembles) ..."
            f"\nchallenge_resource_id: {challenge_id}"
            f"\nensemble_model: {model_id}"
        )
        query_sub = (
            f"SELECT mse.id as ensemble_id, mse.variable, msef.datetime, msef.value "
            f"FROM market_session_ensemble_forecasts as msef "
            f"INNER JOIN market_session_ensemble as mse "
            f"ON msef.ensemble_id = mse.id "
            f"INNER JOIN market_session_challenge as msc "
            f"ON mse.market_session_challenge_id = msc.id "
            f"WHERE mse.model='{model_id}' "
            f"AND msc.id = '{challenge_id}';"
        )
        data = db.read_query_pandas(query_sub)
        if data.empty:
            logger.warning(f"No forecasts data from ensemble {model_id}")
            continue
        else:
            data["user_id"] = model_id
            dataset = pd.concat([dataset, data], axis=0)
            logger.debug("Querying data ... Ok!")

    # Convert DataFrame to dictionary (ensemble / forecasts):
    ensemble_forecasts = {}
    if not dataset.empty:
        for ensemble_id, group in dataset.groupby("ensemble_id"):
            ensemble_forecasts[ensemble_id] = group[
                ["variable", "datetime", "value", "user_id"]
            ].set_index("datetime")

    logger.success(f"Querying ensemble forecasts for challenge {challenge_id} ... Ok!")
    return ensemble_forecasts


def get_continuous_forecasts(user_id, resource_id, start_dt, end_dt):
    db = PostgresDB.get_db_instance(config_name="default")
    logger.info(
        f"Querying continuous forecasts for user {user_id} "
        f"and challenge resource {resource_id} ..."
    )

    query = f"""
SELECT datetime, variable, value 
FROM market_continuous_forecasts 
WHERE user_id='{user_id}'
AND resource_id='{resource_id}'
AND datetime >= '{start_dt}'
AND datetime <= '{end_dt}'
ORDER BY datetime ASC;
"""
    data = db.read_query_pandas(query)
    if data.empty:
        logger.warning(f"No continuous forecasts detected for user {user_id}.")
        return data
    else:
        logger.debug(
            f"Querying continuous forecasts for user {user_id} "
            f"and challenge resource {resource_id} ... Ok!"
        )
        return data


def get_scores_per_resource(
    resource_id, start_dt, end_dt, evaluation_metrics: list, remove_fixed_payment=True
):
    db = PostgresDB.get_db_instance(config_name="default")
    logger.info(f"Querying scores for resource '{resource_id}' challenges ...")

    evaluation_metrics_ = ", ".join(f"'{metric}'" for metric in evaluation_metrics)

    query = f"""
SELECT msss.metric, msss.value, mss.user_id, mss.variable, msc.target_day, msc.id AS challenge_id
FROM market_session_submission_scores AS msss
JOIN market_session_submission AS mss ON msss.submission_id = mss.id
JOIN market_session_challenge AS msc ON msc.id = mss.market_session_challenge_id
JOIN user_resource_participation AS urp
  ON urp.user_id = mss.user_id AND urp.resource_id = msc.resource_id
WHERE target_day >= '{start_dt}' AND target_day <= '{end_dt}'
AND msss.metric IN ({evaluation_metrics_})
AND msc.resource_id = '{resource_id}'
    """

    if remove_fixed_payment:
        query += " AND urp.is_fixed_payment = false "

    query += "ORDER BY target_day ASC;"

    data = db.read_query_pandas(query)
    if data.empty:
        logger.warning(f"No scores data found for resource '{resource_id}'.")
        return data
    else:
        logger.debug(f"Querying scores for resource '{resource_id}' challenges ... Ok!")
        data["user_id"] = data["user_id"].astype(str)
        return data


def get_ensemble_runs_per_resource(resource_id, start_dt, end_dt):
    db = PostgresDB.get_db_instance(config_name="default")
    logger.info(f"Querying ensemble runs for resource '{resource_id}' ...")
    query = f"""
SELECT DISTINCT mse.market_session_challenge_id, msc.resource_id, msc.target_day
FROM market_session_ensemble AS mse 
JOIN market_session_challenge AS msc 
ON msc.id = mse.market_session_challenge_id 
WHERE msc.resource_id='{resource_id}' 
AND target_day >= '{start_dt}' AND target_day <= '{end_dt}' 
ORDER BY target_day ASC;
    """
    data = db.read_query_pandas(query)
    if data.empty:
        logger.warning(f"No ensemble runs found for resource '{resource_id}'.")
        return data
    else:
        logger.debug(f"Querying ensemble runs for resource '{resource_id}'  ... Ok!")
        return data


def get_sellers_forecasts_by_resource(resource_id, start_date, end_date):
    db = PostgresDB.get_db_instance(config_name="default")
    logger.info(f"Querying submitted forecasts for resource {resource_id} ...")

    logger.debug(f"Querying data (submissions) ...\nresource_id: {resource_id}")
    query_sub = (
        f"SELECT mss.user_id as user_id, mss.variable, mssf.datetime, mssf.value "
        f"FROM market_session_submission_forecasts as mssf "
        f"INNER JOIN market_session_submission as mss "
        f"ON mssf.submission_id = mss.id "
        f"INNER JOIN market_session_challenge as msc "
        f"ON mss.market_session_challenge_id = msc.id "
        f"WHERE msc.resource_id='{resource_id}' "
        f"AND msc.target_day >= '{start_date}' "
        f"AND msc.target_day <= '{end_date}';"
    )
    data = db.read_query_pandas(query_sub)
    if data.empty:
        logger.warning(f"No forecasts data from for resource_id {resource_id}")
    else:
        logger.debug("Querying data ... Ok!")
    return data


def get_measurements_data_by_resource(resource_id, start_date, end_date):
    db = PostgresDB.get_db_instance(config_name="default")
    logger.info(f"Querying measurements for resource {resource_id} ...")

    # Request data for buyer resource:
    logger.debug(f"Querying for resource ID {resource_id} ...")
    query = (
        f"select datetime, value "
        f"from raw_data "
        f"where resource_id='{resource_id}' "
        f"and datetime >= '{start_date}' "
        f"and datetime <= '{end_date}' "
        f"order by datetime asc;"
    )
    data = db.read_query_pandas(query)
    data.drop_duplicates(subset=["datetime"], inplace=True)
    if data.empty:
        logger.warning(f"No historical data for resource ID {resource_id}")
        return data
    else:
        logger.debug(f"Querying for resource ID {resource_id} ... Ok!")
        return data


def get_resource_participation_type(resource_id):
    db = PostgresDB.get_db_instance(config_name="default")
    logger.info(f"Querying participation type for resource '{resource_id}' ...")

    query = f"""
SELECT user_id, is_fixed_payment  
FROM user_resource_participation 
WHERE resource_id = '{resource_id}';
"""
    data = db.read_query_pandas(query)
    if data.empty:
        logger.warning(f"No participation type found for resource '{resource_id}'.")
        return {}
    else:
        logger.debug(
            f"Querying participation type for resource '{resource_id}' ... Ok!"
        )
        data["user_id"] = data["user_id"].astype(str)
        participation_dict = data.set_index("user_id")["is_fixed_payment"].to_dict()
        return participation_dict
