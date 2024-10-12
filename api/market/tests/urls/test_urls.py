import uuid

from django.test import TestCase
from django.urls import reverse, resolve

from ...views.market_session import (
    MarketSessionView,
    MarketSessionUpdateView,
)
from ...views.market_session_challenge import (
    MarketSessionChallengeView,
    MarketSessionChallengeUpdateView,
    MarketSessionChallengeSolutionView
)
from ...views.market_session_submission import (
    MarketSessionListSubmissionView,
    MarketSessionListSubmissionForecastsView,
    MarketSessionCreateUpdateSubmissionView,
)
from ...views.market_session_ensemble_forecasts import (
    MarketSessionListEnsembleForecastsView,
    MarketSessionListEnsembleForecastsMetaView,
    MarketSessionCreateUpdateEnsembleForecastsView,
)
from ...views.market_session_ensemble_weights import (
    MarketSessionEnsembleWeightsCreateUpdateView,
    MarketSessionEnsembleWeightsRetrieveView
)
from ...views.market_session_submission_scores import (
    MarketSessionSubmissionScoresCreateView,
    MarketSessionSubmissionScoresRetrieveView
)


class TestUrls(TestCase):

    def test_list_url_is_resolved(self):

        url = reverse('market:market-session')
        self.assertEqual(resolve(url).func.view_class, MarketSessionView)

        url = reverse('market:market-session-update', args=[1])
        self.assertEqual(resolve(url).func.view_class, MarketSessionUpdateView)

        url = reverse('market:market-session-challenge')
        self.assertEqual(resolve(url).func.view_class, MarketSessionChallengeView)

        url = reverse('market:market-session-challenge-update', args=[uuid.uuid4()])
        self.assertEqual(resolve(url).func.view_class, MarketSessionChallengeUpdateView)

        url = reverse('market:market-session-challenge-solution')
        self.assertEqual(resolve(url).func.view_class, MarketSessionChallengeSolutionView)

        url = reverse('market:market-session-submission-list')
        self.assertEqual(resolve(url).func.view_class, MarketSessionListSubmissionView)

        url = reverse('market:market-session-submission-forecasts-list')
        self.assertEqual(resolve(url).func.view_class, MarketSessionListSubmissionForecastsView)

        url = reverse('market:market-session-submission-create-update', args=[uuid.uuid4()])
        self.assertEqual(resolve(url).func.view_class, MarketSessionCreateUpdateSubmissionView)

        url = reverse('market:market-session-ensemble-list')
        self.assertEqual(resolve(url).func.view_class, MarketSessionListEnsembleForecastsView)

        url = reverse('market:market-session-ensemble-meta-list')
        self.assertEqual(resolve(url).func.view_class, MarketSessionListEnsembleForecastsMetaView)

        url = reverse('market:market-session-ensemble-weights-create-update', args=[uuid.uuid4()])
        self.assertEqual(resolve(url).func.view_class, MarketSessionEnsembleWeightsCreateUpdateView)

        url = reverse('market:market-session-ensemble-weights-list')
        self.assertEqual(resolve(url).func.view_class, MarketSessionEnsembleWeightsRetrieveView)

        url = reverse('market:market-session-ensemble-create-update', args=[uuid.uuid4()])
        self.assertEqual(resolve(url).func.view_class, MarketSessionCreateUpdateEnsembleForecastsView)

        url = reverse('market:market-session-submission-scores-list')
        self.assertEqual(resolve(url).func.view_class, MarketSessionSubmissionScoresRetrieveView)

        url = reverse('market:market-session-submission-scores-create', args=[uuid.uuid4()])
        self.assertEqual(resolve(url).func.view_class, MarketSessionSubmissionScoresCreateView)
