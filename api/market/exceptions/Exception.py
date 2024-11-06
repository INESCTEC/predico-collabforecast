from rest_framework.exceptions import APIException


class NoMarketSession(APIException):

    def __init__(self, market_session_id):
        super().__init__(self.default_detail.format(market_session_id))
    status_code = 409
    default_detail = "Market session {} does not exist."
    default_code = 'no_market_session'


class SessionNotOpenForChallenges(APIException):
    def __init__(self, market_session_id):
        super().__init__(self.default_detail.format(market_session_id))
    status_code = 409
    default_detail = "Market session {} is not open for challenges."
    default_code = 'session_not_open_for_challenges'


class UnfinishedSessions(APIException):
    def __init__(self):
        super().__init__(self.default_detail)
    status_code = 409
    default_detail = "Unable to create new session. " \
                     "There are still unfinished sessions."
    default_code = 'unfinished_sessions'


class MoreThanOneSessionOpen(APIException):
    def __init__(self, session_id):
        super().__init__(self.default_detail.format(session_id))
    status_code = 409
    default_detail = "Unable to update session. " \
                     "Only one session must be open at each time, and " \
                     "session '{}' is still in 'open' state."
    default_code = 'more_than_one_session_open'


class ChallengeAlreadyExists(APIException):

    def __init__(self, market_session_id, resource_id):
        super().__init__(self.default_detail.format(market_session_id,
                                                    resource_id))
    status_code = 409
    default_detail = "The user already has created a challenge " \
                     "for session ID {} and resource ID {}."
    default_code = 'challenge_already_exists'


class UserResourceNotRegistered(APIException):

    def __init__(self, user, resource_id):
        super().__init__(self.default_detail.format(resource_id, user))
    status_code = 409
    default_detail = "Resource ID {} is not registered to user '{}'."
    default_code = 'user_resource_not_registered'


class UserChallengeNotRegistered(APIException):

    def __init__(self, user, challenge_id):
        super().__init__(self.default_detail.format(challenge_id, user))
    status_code = 409
    default_detail = "Challenge ID '{}' is not registered to user '{}'."
    default_code = 'user_challenge_not_registered'


class ChallengeNotRegistered(APIException):

    def __init__(self, challenge_id):
        super().__init__(self.default_detail.format(challenge_id))
    status_code = 409
    default_detail = "Challenge ID '{}' is not registered for this resource or user."
    default_code = 'challenge_not_registered'


class ChallengeNotOpen(APIException):

    def __init__(self, challenge_id):
        super().__init__(self.default_detail.format(challenge_id))
    status_code = 409
    default_detail = "Challenge ID '{}' session is not open."
    default_code = 'challenge_not_open'


class ChallengeNotRunning(APIException):

    def __init__(self, challenge_id):
        super().__init__(self.default_detail.format(challenge_id))
    status_code = 409
    default_detail = "Challenge ID '{}' session is not running."
    default_code = 'challenge_not_running'


class InvalidResourceChallenge(APIException):

    def __init__(self):
        super().__init__(self.default_detail)
    status_code = 409
    default_detail = ("It is only possible to create challenges for "
                      "measurements resources.")
    default_code = 'invalid_resource_challenge'


class NoForecastResourceChallenge(APIException):

    def __init__(self):
        super().__init__(self.default_detail)
    status_code = 409
    default_detail = ("It is only possible to create challenges for "
                      "resources with 'to_forecast' field equal to True.")
    default_code = 'no_forecast_resource_challenge'


class NotEnoughDataToChallenge(APIException):

    def __init__(self, resource_id, min_data_count):
        super().__init__(self.default_detail.format(resource_id, min_data_count))
    status_code = 409
    default_detail = ("Resource ID '{}' does not have enough data "
                      "to challenge. It must have at least "
                      "'{}' historical samples.")
    default_code = 'not_enough_data_to_challenge'


class IncompleteSubmission(APIException):

    def __init__(self, f_variable, missing_leadtimes):
        super().__init__(self.default_detail.format(f_variable,
                                                    missing_leadtimes))
    status_code = 409
    default_detail = ("Your submission is incomplete. "
                      "Forecast variable {} is missing "
                      "forecast leadtimes: {}.")
    default_code = 'incomplete_submission'


class IncorrectSubmission(APIException):

    def __init__(self, f_variable, incorrect_leadtimes):
        super().__init__(self.default_detail.format(f_variable,
                                                    incorrect_leadtimes))
    status_code = 409
    default_detail = ("Your submission is incorrect. "
                      "Forecast variable {} has the following incorrect "
                      "leadtimes that should not be in the "
                      "forecast horizon: {}.")
    default_code = 'incorrect_submission'


class NotEnoughDataToSubmit(APIException):

    def __init__(self, resource_id, min_data_count):
        super().__init__(self.default_detail.format(min_data_count, resource_id))
    status_code = 409
    default_detail = ("Unable to participate. Your user does not fulfil the "
                      "minimum historical forecast samples requirement "
                      "to participate in this challenge. "
                      "To ensure your eligibility, please submit at least "
                      "({}) historical forecast samples for the 40 days "
                      "prior to this challenge start date, to Resource ID "
                      "'{}', via POST request to the "
                      "'/data/individual-forecasts/historical' endpoint.")
    default_code = 'not_enough_data_to_submit'


class NotEnoughPreviousDayDataToSubmit(APIException):

    def __init__(self, resource_id, time_resolution):
        super().__init__(self.default_detail.format(time_resolution, resource_id))
    status_code = 409
    default_detail = ("Unable to participate. Your user does not fulfil the "
                      "minimum historical forecast samples requirement "
                      "to participate in this challenge. "
                      "To ensure your eligibility, please submit a forecast "
                      "for all the {}min periods of the previous day, to "
                      "target Resource ID '{}', via POST request to the "
                      "'/data/individual-forecasts/historical' endpoint.")
    default_code = 'not_enough_previous_day_data_to_submit'


class FailedToInsertSubmission(APIException):

    def __init__(self):
        super().__init__(self.default_detail)
    status_code = 409
    default_detail = ("There was a problem while uploading your submission. "
                      "Please contact the developers.")
    default_code = 'failed_to_insert_submission'



class FailedToInsertRampAlerts(APIException):

    def __init__(self):
        super().__init__(self.default_detail)
    status_code = 409
    default_detail = ("There was a problem while uploading ramp alerts. "
                      "Please contact the developers.")
    default_code = 'failed_to_insert_ramp_alerts'



class SubmissionAlreadyExists(APIException):

    def __init__(self, f_variable):
        super().__init__(self.default_detail.format(f_variable))
    status_code = 409
    default_detail = ("You have already placed a submission for this "
                      "challenge, with variable {}. "
                      "Please use the PUT endpoint for a partial "
                      "or full update of your entry.")
    default_code = 'submission_already_exists'


class SubmissionNotFound(APIException):

    def __init__(self, user_id, f_variable, challenge_id):
        super().__init__(self.default_detail.format(user_id,
                                                    f_variable, challenge_id))
    status_code = 409
    default_detail = ("Submission from user '{}' and variable '{}' "
                      "was not found for challenge ID {}.")
    default_code = 'submission_not_found'


class IncompleteEnsemble(APIException):

    def __init__(self, f_variable, missing_leadtimes):
        super().__init__(self.default_detail.format(f_variable,
                                                    missing_leadtimes))
    status_code = 409
    default_detail = ("Your ensemble forecast is incomplete. "
                      "Forecast variable {} is missing "
                      "forecast leadtimes: {}.")
    default_code = 'incomplete_ensemble'


class FailedToInsertEnsemble(APIException):

    def __init__(self):
        super().__init__(self.default_detail)
    status_code = 409
    default_detail = ("There was a problem while uploading your ensemble "
                      "forecasts. Please contact the developers.")
    default_code = 'failed_to_insert_ensemble'


class EnsembleNotFound(APIException):

    def __init__(self, ensemble_id):
        super().__init__(self.default_detail.format(ensemble_id))
    status_code = 409
    default_detail = ("The ensemble {} was not found.")
    default_code = 'ensemble_not_found'


class EnsembleWeightsAlreadySet(APIException):

    def __init__(self, ensemble_id):
        super().__init__(self.default_detail.format(ensemble_id))
    status_code = 409
    default_detail = ("The ensemble weights are already set for ensemble "
                      "ID '{}'. Please use the PUT endpoint to update it.")
    default_code = 'ensemble_weights_already_set'
