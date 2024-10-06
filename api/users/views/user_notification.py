from django.http import Http404
from rest_framework import generics, status
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from api.renderers.CustomRenderer import CustomRenderer
from users.models.user import User
from users.models.user_notification import UserNotification, UserNotificationType
from users.serializers.user_notification import (UserGetNotificationSerializer,
                                                 UserNotificationTypeSerializer,
                                                 UserUpdateNotificationSerializer)


# todo the response structure is not being correctly parsed in the swagger documentation
class UserNotificationListAPIView(generics.ListAPIView):
    renderer_classes = (CustomRenderer,)
    queryset = UserNotification.objects.all()
    serializer_class = UserGetNotificationSerializer
    permission_classes = (IsAuthenticated,)

    # Override the get_queryset method to return UserNotification objects
    # filtered by the current user
    def get_queryset(self):
        return UserNotification.objects.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        notifications_by_type = {}

        for notification in serializer.data:
            notification_type = notification['notification_type']
            notification_data = {
                'id': notification['id'],
                'user': notification['user'],
                'notification_title': notification['notification_title'],
                'notification_description': notification['notification_description'],
                'state': notification['state'],
            }

            if notification_type in notifications_by_type:
                notifications_by_type[notification_type].append(notification_data)
            else:
                notifications_by_type[notification_type] = [notification_data]

        return Response(notifications_by_type)


class UserNotificationUpdateStateAPIView(generics.UpdateAPIView):
    renderer_classes = (CustomRenderer,)
    queryset = UserNotification.objects.all()
    serializer_class = UserUpdateNotificationSerializer
    permission_classes = (IsAuthenticated,)

    # Override the update method to update the state of the
    # UserNotification object
    def update(self, request, *args, **kwargs):
        try:
            # Retrieve the UserNotification object
            instance = self.get_object()
        except Http404:
            # Return a 404 response if the object does not exist
            return Response(
                {'message': 'UserNotification matching query not found'},
                status=status.HTTP_404_NOT_FOUND)
        serializer = UserUpdateNotificationSerializer(instance, data=request.data)
        if serializer.is_valid():
            instance.state = serializer.validated_data['state']
            instance.save()
            return Response(self.serializer_class(instance).data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserNotificationTypeListAndCreateAPIView(generics.ListAPIView,
                                               generics.CreateAPIView):
    renderer_classes = (CustomRenderer,)
    queryset = UserNotificationType.objects.all()
    serializer_class = UserNotificationTypeSerializer
    permission_classes = (IsAdminUser,)

    def perform_create(self, serializer):
        instance = serializer.save()
        users = User.objects.all()
        for user in users:
            UserNotification.objects.create(user=user, notification_type=instance)
        return instance


class UserNotificationTypeDeleteAndUpdateAPIView(generics.DestroyAPIView,
                                                 generics.UpdateAPIView):
    renderer_classes = (CustomRenderer,)
    queryset = UserNotificationType.objects.all()
    serializer_class = UserNotificationTypeSerializer
    permission_classes = (IsAdminUser,)

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except Http404:
            return Response(
                {'message': 'UserNotificationType matching query does not exist'},
                status=status.HTTP_400_BAD_REQUEST)
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except Http404:
            return Response(
                {'message': 'UserNotificationType matching query does not exist'},
                status=status.HTTP_400_BAD_REQUEST)
        serializer = self.serializer_class(instance, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
