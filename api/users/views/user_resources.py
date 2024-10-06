from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser

from api.renderers.CustomRenderer import CustomRenderer

from ..schemas.query import *
from ..schemas.responses import *
from .. import exceptions as user_exceptions
from ..util.validators import validate_query_params
from ..models.user_resources import UserResources
from ..serializers.user_resources import (
    UserResourcesSerializer,
    UserResourcesCreateSerializer
)


class UserResourcesView(APIView):
    renderer_classes = (CustomRenderer,)
    permission_classes = (IsAdminUser,)
    serializer_class = UserResourcesSerializer
    model_class = UserResources

    def queryset(self, request):
        user = request.user
        resource_id = request.query_params.get('resource', None)
        resource_name = request.query_params.get('name', None)
        validate_query_params(
            resource_id=resource_id,
            resource_name=resource_name
        )
        # user 1 cannot access resources of user 2
        query = self.model_class.objects.filter(user_id=user.id)

        if resource_id is not None:
            query = query.filter(id=resource_id)

        if resource_name is not None:
            query = query.filter(name=resource_name)

        return query

    @swagger_auto_schema(
        operation_summary="List user portfolio resources",
        operation_id="get_user_resources",
        operation_description="Method for market maker to list their "
                              "registered resources",
        manual_parameters=user_resources_query_params(),
        responses={
            200: UserResourcesResponse["GET"],
            400: 'Bad request',
            401: NotAuthenticatedResponse,
            403: ForbiddenAccessResponse,
            500: "Internal Server Error",
        })
    def get(self, request):
        query = self.queryset(request)
        serializer = self.serializer_class(query, many=True)
        return Response(data=serializer.data)

    @swagger_auto_schema(
        operation_summary="Register user portfolio resource",
        operation_id="post_user_resources",
        operation_description="Method for market maker to register a new resource",
        request_body=UserResourcesCreateSerializer,
        responses={
            400: 'Bad request',
            401: NotAuthenticatedResponse,
            403: ForbiddenAccessResponse,
            500: "Internal Server Error",
        })
    def post(self, request):
        request_data = request.data.copy()
        request_data["user"] = request.user.id
        serializer = self.serializer_class(data=request_data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class UserResourcesUpdateView(APIView):
    renderer_classes = (CustomRenderer,)
    permission_classes = (IsAdminUser,)
    serializer_class = UserResourcesSerializer
    model_class = UserResources

    def queryset(self, request):
        user = request.user
        # user 1 cannot access resources of user 2
        query = self.model_class.objects.filter(user_id=user.id)
        return query

    @swagger_auto_schema(
        operation_summary="Delete user portfolio resource",
        operation_id="delete_user_resources",
        operation_description="Method for market maker to delete their "
                              "resources",
        responses={
            400: 'Bad request',
            401: NotAuthenticatedResponse,
            403: ForbiddenAccessResponse,
            500: "Internal Server Error",
        })
    def delete(self, request, resource_id):
        query = self.queryset(request).filter(id=resource_id)
        if query.exists():
            query.delete()
            return Response(data=f"Resource ID {resource_id} "
                                 f"deleted for user {request.user}.",
                            status=status.HTTP_200_OK)
        else:
            raise user_exceptions.ResourceNotFound()

    @swagger_auto_schema(
        operation_summary="Update user portfolio resources",
        operation_id="patch_user_resources",
        operation_description="Method for market maker to update their "
                              "resource details",
        request_body=UserResourcesSerializer,
        responses={
            400: 'Bad request',
            401: NotAuthenticatedResponse,
            403: ForbiddenAccessResponse,
            500: "Internal Server Error",
        })
    def patch(self, request, resource_id):
        try:
            request_data = request.data.copy()
            request_data["user"] = request.user.id
            query = self.queryset(request).filter(id=resource_id).get()
            serializer = self.serializer_class(query, data=request_data,
                                               context={'request': request})
            serializer.is_valid(raise_exception=True)
            serializer.update(query, serializer.validated_data)
            return Response(data=serializer.data, status=status.HTTP_200_OK)
        except UserResources.DoesNotExist as ex:
            raise user_exceptions.ResourceNotFound() from ex
