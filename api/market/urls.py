# ruff: noqa: E501
from django.urls import re_path

from .views.market_session import (
    MarketSessionView,
    MarketSessionUpdateView,
)
from .views.market_session_challenge import (
    MarketSessionChallengeView,
    MarketSessionChallengeUpdateView,
    MarketSessionChallengeSolutionView
)
from .views.market_session_submission import (
    MarketSessionListSubmissionView,
    MarketSessionListSubmissionForecastsView,
    MarketSessionCreateUpdateSubmissionView,
)
from .views.market_session_ensemble_forecasts import (
    MarketSessionListEnsembleForecastsView,
    MarketSessionListEnsembleForecastsMetaView,
    MarketSessionCreateUpdateEnsembleForecastsView,
)
from .views.market_session_ensemble_weights import (
    MarketSessionChallengeWeightsCreateUpdateView,
    MarketSessionChallengesWeightsRetrieveView
)
from .views.market_session_submission_scores import (
    MarketSessionSubmissionScoresCreateView,
    MarketSessionSubmissionScoresRetrieveView
)


app_name = "market"
challenge_id_regex = "?P<challenge_id>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"  # noqa
submission_id_regex = "?P<submission_id>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"  # noqa
urlpatterns = [
    re_path('session/?$',
            MarketSessionView.as_view(),
            name="market-session"),
    re_path('session/(?P<session_id>[0-9]+)$',
            MarketSessionUpdateView.as_view(),
            name="market-session-update"),
    re_path('challenge/?$',
            MarketSessionChallengeView.as_view(),
            name="market-session-challenge"),
    re_path(f'challenge/({challenge_id_regex})$',
            MarketSessionChallengeUpdateView.as_view(),
            name="market-session-challenge-update"),
    re_path('challenge/solution?$',
            MarketSessionChallengeSolutionView.as_view(),
            name="market-session-challenge-solution"),
    re_path('challenge/submission/?$',
            MarketSessionListSubmissionView.as_view(),
            name="market-session-submission-list"),
    re_path('challenge/submission/forecasts?$',
            MarketSessionListSubmissionForecastsView.as_view(),
            name="market-session-submission-forecasts-list"),
    re_path(f'challenge/submission/({challenge_id_regex})$',
            MarketSessionCreateUpdateSubmissionView.as_view(),
            name="market-session-submission-create-update"),
    re_path('challenge/ensemble-forecasts?$',
            MarketSessionListEnsembleForecastsView.as_view(),
            name="market-session-ensemble-list"),
    re_path('challenge/ensemble-forecasts-meta?$',
            MarketSessionListEnsembleForecastsMetaView.as_view(),
            name="market-session-ensemble-meta-list"),
    re_path(f'challenge/({challenge_id_regex})/ensemble-forecasts?$',
            MarketSessionCreateUpdateEnsembleForecastsView.as_view(),
            name="market-session-ensemble-create-update"),
    re_path('challenge/ensemble-weights?$',
            MarketSessionChallengesWeightsRetrieveView.as_view(),
            name="market-session-ensemble-weights-list"),
    re_path(f'challenge/({challenge_id_regex})/ensemble-weights?$',
            MarketSessionChallengeWeightsCreateUpdateView.as_view(),
            name="market-session-ensemble-weights-create-update"),
    re_path('challenge/submission-scores?$',
            MarketSessionSubmissionScoresRetrieveView.as_view(),
            name="market-session-submission-scores-list"),
    re_path(f'challenge/({challenge_id_regex})/submission-scores?$',
            MarketSessionSubmissionScoresCreateView.as_view(),
            name="market-session-submission-scores-create-update")
]
