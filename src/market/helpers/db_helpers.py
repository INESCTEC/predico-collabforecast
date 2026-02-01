import pandas as pd
import datetime as dt

from loguru import logger
from psycopg2.errors import UniqueViolation, ForeignKeyViolation

from ...database.PostgresDB import PostgresDB


# #############################################################################
# Get Measurements Data for Session Resources:
# #############################################################################


def get_measurements_data_mock(users_resources, market_launch_time):
    resources_id_list = [x["id"] for x in users_resources]
    # todo: Right now working with mock data - replace by DB queries:
    from ..util.mock import MeasurementsGenerator
    logger.info("[MOCK] Querying measurements for resource list ...")
    # Create fictitious measurements data
    mg = MeasurementsGenerator()
    measurements = {}
    for resource_id in sorted(resources_id_list):
        measurements[resource_id] = mg.generate_mock_data_sin(
            start_date=market_launch_time - pd.DateOffset(months=12),
            end_date=market_launch_time,
        ).set_index("datetime")
    logger.info("[MOCK] Querying measurements for resource list ... Ok!")
    return measurements


def get_measurements_data(buyers_resources, start_date, end_date):
    db = PostgresDB.get_db_instance(config_name="default")
    logger.info("Querying measurements for resource list ...")
    measurements = {}
    for resource_id in sorted(buyers_resources):
        # Request data for buyer resource:
        logger.debug(f"Querying for resource ID {resource_id} ...")
        query = f"select datetime, value " \
                f"from raw_data " \
                f"where resource_id='{resource_id}' " \
                f"and datetime >= '{start_date}' " \
                f"and datetime <= '{end_date}' " \
                f"order by datetime asc;"
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
        logger.debug(f"Querying data (submissions) ..."
                     f"\nchallenge_resource_id: {challenge_resource_id}"
                     f"\nseller_user: {seller_user}"
                     f"\nvariable: {variable}")
        query_sub = (f"SELECT mssf.datetime, mssf.value "
                     f"FROM market_session_submission_forecasts as mssf "
                     f"INNER JOIN market_session_submission as mss "
                     f"ON mssf.submission_id = mss.id "
                     f"INNER JOIN market_session_challenge as msc "
                     f"ON mss.market_session_challenge_id = msc.id "
                     f"WHERE msc.resource_id='{challenge_resource_id}' "
                     f"AND mss.user_id='{seller_user}' "
                     f"AND mssf.datetime >= '{start_date}' "
                     f"AND mssf.datetime <= '{end_date}' "
                     f"AND mss.variable = '{variable}' ORDER BY datetime;")
        # Get actual submitted forecasts for past challenges:
        data_submissions = db.read_query_pandas(query_sub)

        logger.debug(f"Querying data (submissions) ..."
                     f"\nchallenge_resource_id: {challenge_resource_id}"
                     f"\nseller_user: {seller_user}"
                     f"\nvariable: {variable}")
        query_hist = (f"SELECT datetime, value "
                      f"FROM individual_forecasts "
                      f"WHERE resource_id='{challenge_resource_id}' "
                      f"AND user_id='{seller_user}' "
                      f"AND datetime >= '{start_date}' "
                      f"AND datetime <= '{end_date}' "
                      f"AND variable = '{variable}' ORDER BY datetime;")
        # Get historical forecasts (not submissions - initial kickoff):
        data_historical = db.read_query_pandas(query_hist)
        # Concat both data sources:
        data = pd.concat([data_submissions, data_historical], axis=0)
        if data.empty:
            logger.warning(f"No forecasts data from user {seller_user} to target resource {challenge_resource_id}")
        else:
            data.drop_duplicates(subset=["datetime"], keep="first", inplace=True)
            data.sort_values(by="datetime", inplace=True)
            data = data.set_index("datetime")

        if challenge_resource_id not in forecasts[resource["user"]]:
            forecasts[resource["user"]][challenge_resource_id] = {}

        forecasts[seller_user][challenge_resource_id][variable] = data
        logger.debug(f"Querying data ... Ok!")
    logger.success("Querying forecasts for sellers forecasts list ... Ok!")
    return forecasts


# #############################################################################
# Upload market forecasts for session resources:
# #############################################################################

def upload_forecasts(market_session_id,
                     user_id,
                     request,
                     resource_id,
                     forecasts,
                     table_name):
    # Create datetime col:
    forecasts.reset_index(drop=False, inplace=True)
    # Create other cols:
    forecasts["request"] = request
    forecasts["market_session_id"] = market_session_id
    forecasts["user_id"] = user_id
    forecasts["registered_at"] = dt.datetime.utcnow()
    forecasts["units"] = "kw"  # Todo: Assure this is dynamic:
    forecasts["resource_id"] = resource_id

    forecasts = forecasts[["datetime", "request", "value", "units",
                           "registered_at", "market_session_id",
                           "resource_id", "user_id"]]

    # Insert data in DB:
    try:
        db = PostgresDB.get_db_instance(config_name="default")
        logger.debug(f"Forecast shape: {forecasts.shape}")
        logger.debug(f"Inserting agent {user_id} forecasts ...")
        db.insert_dataframe(df=forecasts, table=table_name)
        logger.debug(f"Inserting agent {user_id} forecasts ... Ok!")
        return True
    except (UniqueViolation, ForeignKeyViolation) as ex:
        msg = f"Failed to insert agent {user_id} forecasts"
        logger.error(f"{msg} - {ex}")
    except Exception:
        msg = f"Unexpected error while inserting agent {user_id} forecasts"
        logger.exception(msg)
        return False


def update_bid_has_forecast(user_id, bid_id, table_name):
    try:
        db = PostgresDB.get_db_instance(config_name="default")
        logger.debug(f"Updating {user_id} - bid {bid_id} "
                     f"'has_forecast' field ...")
        query = f"UPDATE {table_name} " \
                f"SET has_forecasts = true " \
                f"WHERE id = '{bid_id}';"
        db.execute_query(query=query)
        logger.debug(f"Updating {user_id} - bid {bid_id} "
                     f"'has_forecast' field ... Ok!")
        return True
    except Exception:
        logger.exception(f"Failed update {user_id} - bid {bid_id} "
                         f"'has_forecast' field.")
        return False


def get_sellers_submissions(sellers_users, challenge_id):
    db = PostgresDB.get_db_instance(config_name="default")
    logger.info(f"Querying submitted forecasts for challenge {challenge_id} ...")
    dataset = pd.DataFrame()
    for user_id in sellers_users:
        logger.debug(f"Querying data (submissions) ..."
                     f"\nchallenge_resource_id: {challenge_id}"
                     f"\nseller_user: {user_id}")
        query_sub = (f"SELECT mss.id as submission_id, mss.variable, mssf.datetime, mssf.value "
                     f"FROM market_session_submission_forecasts as mssf "
                     f"INNER JOIN market_session_submission as mss "
                     f"ON mssf.submission_id = mss.id "
                     f"INNER JOIN market_session_challenge as msc "
                     f"ON mss.market_session_challenge_id = msc.id "
                     f"WHERE mss.user_id='{user_id}' "
                     f"AND msc.id = '{challenge_id}';")
        data = db.read_query_pandas(query_sub)
        if data.empty:
            logger.warning(f"No forecasts data from user {user_id}")
            continue
        else:
            dataset = pd.concat([dataset, data], axis=0)
            logger.debug(f"Querying data ... Ok!")

    # Convert DataFrame to dictionary (submissions / forecasts):
    submission_forecasts = {}
    for submission_id, group in dataset.groupby('submission_id'):
        submission_forecasts[submission_id] = group[['variable', 'datetime', 'value']].set_index("datetime")

    logger.success(f"Querying submitted forecasts for challenge {challenge_id} ... Ok!")
    return submission_forecasts


def get_challenges_without_weights():
    db = PostgresDB.get_db_instance(config_name="default")
    logger.info(f"Querying challenges without weights assigned ...")
    query = ("SELECT mse.id AS ensemble_id, mse.model, mse.variable, "
             "msc.id AS challenge, msc.use_case, msc.start_datetime, msc.end_datetime, msc.resource_id AS resource "
             "FROM market_session_ensemble AS mse "
             "JOIN market_session_challenge AS msc "
             "ON mse.market_session_challenge_id = msc.id "
             "WHERE mse.id NOT IN (select ensemble_id from market_session_ensemble_weights);")

    data = db.read_query_pandas(query)
    if data.empty:
        logger.warning(f"There are no challenges without weights assigned.")
        return []
    else:
        data["challenge"] = data["challenge"].astype(str)
        data["resource"] = data["resource"].astype(str)
        data["ensemble_id"] = data["ensemble_id"].astype(str)
    logger.debug(f"Querying challenges without weights assigned ... Ok!")

    # Group the DataFrame by the specified keys
    group_keys = ['challenge', 'use_case', 'start_datetime', 'end_datetime', 'resource']  # noqa
    grouped = data.groupby(group_keys)

    result = []
    for group_values, group_df in grouped:
        # Unpack the group keys
        challenge, use_case, start_datetime, end_datetime, resource = group_values
        # Collect ensemble_data for each group
        ensemble_data = group_df[['ensemble_id', 'model', 'variable']].to_dict(orient='records')
        # Build the data item
        data_item = {
            "challenge": challenge,
            "use_case": use_case,
            "start_datetime": start_datetime,
            "end_datetime": end_datetime,
            "resource": resource,
            "ensemble_data": ensemble_data
        }
        result.append(data_item)

    return result