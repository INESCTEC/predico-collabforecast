from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, exceptions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from api.utils.permissions import method_permission_classes
from api.utils.custom_schema import conditional_swagger_auto_schema
from api.renderers.CustomRenderer import CustomRenderer

from ..schemas.query import *
from ..schemas.responses import *
from ..util.validators import validate_query_params

from ..models.market_session import (
    MarketSession,
)

from ..serializers.market_session import (
    MarketSessionSerializer,
)


class MarketSessionView(APIView):
    permission_classes = (IsAuthenticated,)
    renderer_classes = [CustomRenderer]
    serializer_class = MarketSessionSerializer

    @staticmethod
    def queryset(request):
        session_status = request.query_params.get('status', None)
        market_session_id = request.query_params.get('market_session', None)
        latest_only = request.query_params.get('latest_only', None)
        validate_query_params(
            market_session_id=market_session_id,
            market_session_status=session_status,
            latest_only=latest_only
        )

        # initial query:
        sessions = MarketSession.objects.all()

        # Get session by ID
        if market_session_id is not None:
            sessions = sessions.filter(id=market_session_id)

        # Get session by Status:
        if session_status is not None:
            sessions = sessions.filter(status=session_status)

        # Default latest_only query param to False if not declared
        latest_only = 'false' if latest_only is None else latest_only.lower()
        if latest_only != "false":
            last_sess = sessions.order_by('id').last()
            sessions = [] if last_sess is None else [last_sess]
        return sessions

    @swagger_auto_schema(
        operation_id="get_market_session",
        operation_description="List market sessions",
        manual_parameters=market_session_query_params(),
        responses={
            200: MarketSessionResponse["GET"],
            400: 'Bad request',
            401: NotAuthenticatedResponse,
            403: ForbiddenAccessResponse,
            500: "Internal Server Error",
        })
    def get(self, request):
        sessions = self.queryset(request)
        serializer = self.serializer_class(sessions, many=True)
        return Response(serializer.data)

    @conditional_swagger_auto_schema(
        operation_id="post_market_session",
        operation_description="[AdminOnly] Method to register market session",
        request_body=serializer_class,
        responses={
            400: 'Bad request',
            401: NotAuthenticatedResponse,
            403: ForbiddenAccessResponse,
            409: ConflictResponse,
            500: "Internal Server Error",
        })
    @method_permission_classes((IsAdminUser,))
    def post(self, request):
        # Only allow admin users w/ session management permissions
        if not request.user.is_session_manager:
            return Response(data="You do not have permission to perform this "
                                 "action.", status=status.HTTP_403_FORBIDDEN)

        serializer = self.serializer_class(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)


class MarketSessionUpdateView(APIView):
    permission_classes = (IsAdminUser,)
    renderer_classes = [CustomRenderer]
    serializer_class = MarketSessionSerializer

    @conditional_swagger_auto_schema(
        operation_id="patch_market_session",
        operation_description="Update market session details",
        request_body=serializer_class,
        responses={
            400: 'Bad request',
            401: NotAuthenticatedResponse,
            403: ForbiddenAccessResponse,
            409: ConflictResponse,
            500: "Internal Server Error",
        })
    def patch(self, request, session_id=None):

        # Only allow admin users w/ session management permissions to
        # create or update market sessions
        if not request.user.is_session_manager:
            return Response(data="You do not have permission to perform this "
                                 "action.",
                            status=status.HTTP_403_FORBIDDEN)

        if session_id is None:
            raise exceptions.ValidationError("Missing 'session_id' url "
                                             "parameter.")

        try:
            market_session = MarketSession.objects.get(id=session_id)
            serializer = self.serializer_class(
                market_session,
                data=request.data,
                partial=True,
                context={'request': request, "session_id": session_id})
            serializer.is_valid(raise_exception=True)
            serializer.update(market_session, serializer.validated_data)
            return Response(data=serializer.data)
        except MarketSession.DoesNotExist:
            return Response(data="That market session ID does not exist.",
                            status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
            return Response(data={e.args[0]: ["This field is required"]},
                            status=status.HTTP_400_BAD_REQUEST)
