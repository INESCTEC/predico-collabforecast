from loguru import logger


def log_session_stats(session_info):
    """
    Log session stats
    :param session_info: dict with session data

    """
    # Log session data:
    log_msg = f"""
    Session:
    ID: {session_info['session_data']['id']}
    Open TS {session_info['session_data']['open_ts']}
    Launch TS {session_info['session_data']['launch_ts']}
    
    Open Challenges:
"""
    for challenge in session_info['challenges_data']:
        log_msg += f"""
        //////////////////////////////////////////////////////////////////////
        Challenge ID: {challenge['id']}
        Use Case: {challenge['use_case']}
        Resource: {challenge['resource']}
        Period: {challenge['start_datetime']} - {challenge['end_datetime']}
        -
        
        Submissions:
    """

        forecasters = dict([(x['user'], []) for x in challenge['submission_list']])

        for submission in challenge['submission_list']:
            forecasters[submission['user']] += [submission['variable']]

        # Add forecasters submissions to log
        for forecaster, submissions in forecasters.items():
            log_msg += f"""
            Forecaster: {forecaster}
            Submissions: {submissions}
            -
        """

        log_msg += f"""
        \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
        """
    logger.info("-" * 79)
    logger.info("Session data:")
    logger.info(log_msg)
    logger.info("-" * 79)