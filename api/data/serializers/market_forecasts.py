from rest_framework import serializers

from market.models.market_session_ensemble_forecasts import MarketSessionEnsembleForecasts  # noqa


class MarketForecastsRetrieveSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketSessionEnsembleForecasts
        fields = ["datetime", "variable", "value"]

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['resource_name'] = instance.ensemble.market_session_challenge.resource.name  # noqa
        rep['ensemble_id'] = instance.ensemble.id
        rep['market_session_id'] = instance.ensemble.market_session_challenge.market_session.id  # noqa
        return rep
