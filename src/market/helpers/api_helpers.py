import pandas as pd

from loguru import logger


def get_session_data(api_controller):
    """
    Fetch session data from API
    :param api_controller: API Controller instance
    :return: dict with session data
    """
    logger.info("Fetching session data ...")
    # Get current last active session (status='closed'):
    session_data = api_controller.list_last_session(status='closed')
    # Get session_id & fetch data for that session:
    active_session_id = session_data["id"]
    logger.debug(f"Retrieving data for Session ID {active_session_id}")
    # Get session challenges:
    challenges = api_controller.list_challenges(active_session_id)
    buyer_resources = [x["resource"] for x in challenges]
    sellers_resources = []
    # Get submissions for each challenge:
    for challenge in challenges:
        challenge_id = challenge["id"]
        submissions = api_controller.list_challenges_submissions(challenge_id)
        challenge["submission_list"] = submissions

        for sub in submissions:
            sellers_resources.append({
                "user": sub["user"],
                "market_session_challenge_resource_id": challenge["resource"],
                "variable": sub["variable"],
            })

    logger.info("Fetching session data ... Ok!")
    return {
        "session_data": session_data,
        "challenges_data": challenges,
        "buyers_resources": buyer_resources,
        "sellers_resources": sellers_resources,
    }


def get_measurements_data(buyers_resources, api_controller,
                          start_date, end_date):
    """
    Query measurements for a list of resources
    :param buyers_resources: list of resources
    :param api_controller: API Controller instance
    :param start_date: start date
    :param end_date: end date
    :return: dict with measurements data
    """
    logger.info("Querying measurements for resource list ...")
    measurements = {}
    for resource_id in sorted(buyers_resources):
        # Get session challenges:
        response = api_controller.list_resource_measurements_data(
            resource_id=resource_id,
            start_date=start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
            end_date=end_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        )
        data = pd.DataFrame(response)
        if data.empty:
            logger.warning(f"No historical data for resource ID {resource_id}")
            measurements[resource_id] = data
        else:
            # todo: improve data processing pipeline
            data = data.set_index("datetime")
            data = data.resample("h").mean().dropna()
            measurements[resource_id] = data
        logger.debug(f"Querying for resource ID {resource_id} ... Ok!")
    logger.info("Querying measurements for resource list ... Ok!")
    return measurements


def get_challenges_without_weights(api_controller):
    """
    Get challenges without weights
    :param api_controller: API Controller instance
    :return: list of challenges without weights
    """

    return challenges
