from rest_framework import serializers

from .. import exceptions as market_exceptions
from ..models.market_session import (
    MarketSession,
)


class MarketSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketSession
        fields = '__all__'

    def validate(self, attrs):
        request = self.context.get('request')
        if (request.method == 'POST') and (len(self.Meta.model.objects.exclude(status="finished")) > 0):  # noqa
            # Check if there are unfinished sessions
            raise market_exceptions.UnfinishedSessions()

        elif (request.method == "PATCH") and (request.data["status"] == "open"):
            session_id = self.context.get('session_id')
            # Check if there are already sessions open
            # (there can only be 1 session open at each time)
            open_sessions = self.Meta.model.objects \
                .filter(status="open") \
                .exclude(id=session_id)
            if len(open_sessions) > 0:
                raise market_exceptions.MoreThanOneSessionOpen(
                    session_id=session_id
                )
        return attrs
