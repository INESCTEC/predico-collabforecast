from loguru import logger


def get_session_data(api_controller):
    """
    Fetch session data from API
    :param api_controller: API Controller instance
    :return: dict with session data
    """
    logger.info("Fetching session data ...")
    # Get current last active session (status='closed'):
    session_data = api_controller.list_last_session(status="closed")
    # Get session_id & fetch data for that session:
    active_session_id = session_data["id"]
    logger.debug(f"Retrieving data for Session ID {active_session_id}")
    # Get session challenges:
    challenges = api_controller.list_challenges(session_id=active_session_id)
    buyer_resources = [x["resource"] for x in challenges]
    sellers_resources = []
    # Get submissions for each challenge:
    for challenge in challenges:
        challenge_id = challenge["id"]
        submissions = api_controller.list_challenges_submissions(challenge_id)
        challenge["submission_list"] = submissions

        for sub in submissions:
            sellers_resources.append(
                {
                    "user": sub["user"],
                    "market_session_challenge_resource_id": challenge["resource"],
                    "variable": sub["variable"],
                }
            )

    logger.info("Fetching session data ... Ok!")
    return {
        "session_data": session_data,
        "challenges_data": challenges,
        "buyers_resources": buyer_resources,
        "sellers_resources": sellers_resources,
    }
