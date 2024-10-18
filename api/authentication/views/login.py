from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from ..serializers.login import MyTokenObtainPairSerializer
from ..schemas.responses import LoginResponse, RefreshResponse
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from rest_framework.response import Response


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

    @swagger_auto_schema(
        operation_summary="Obtain JWT token pair",
        operation_description="Endpoint to obtain a JWT access and refresh token by providing user credentials.",  # noqa
        responses={200: LoginResponse["POST"],
                   400: 'Bad request'},
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='User email'),  # noqa
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='User password'),  # noqa
            },
            required=['email', 'password'],
        ),
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class MyTokenRefreshView(TokenRefreshView):
    @swagger_auto_schema(
        operation_summary="Refresh JWT token",
        operation_description="Takes a refresh type JSON web token and returns an access type JSON web token if the refresh token is valid.",  # noqa
        responses={200: RefreshResponse["POST"],
                   400: 'Bad request'},
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='User refresh token'),  # noqa
            },
            required=['refresh'],
        ),
    )
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        response = {
            "access": response.data["access"]
        }
        return Response(response)
