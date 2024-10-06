# ruff: noqa: E501
from django.urls import re_path, path

from .views.user import (PasswordTokenCheck,
                         RequestPasswordResetEmail,
                         SetNewPassword,
                         UserListView,
                         UserRegisterView,
                         UserVerifyEmailView)

from .views.user_notification import (
    UserNotificationListAPIView,
    UserNotificationTypeDeleteAndUpdateAPIView,
    UserNotificationTypeListAndCreateAPIView,
    UserNotificationUpdateStateAPIView
)
from .views.user_resources import (UserResourcesUpdateView,
                                   UserResourcesView)

app_name = "user"

urlpatterns = [
    re_path('request-reset-email/',
            RequestPasswordResetEmail.as_view(),
            name="request-reset-email"),

    path('password-reset-confirm/<uidb64>/<token>/',
         PasswordTokenCheck.as_view(),
         name='password_reset_confirm'),

    re_path('password-reset-complete/',
            SetNewPassword.as_view(),
            name='password-reset-complete'),

    re_path(r'^notification/$',
            UserNotificationListAPIView.as_view(),
            name='user-notification-list'),

    re_path(r'^notification/(?P<pk>\d+)/$',
            UserNotificationUpdateStateAPIView.as_view(),
            name='user-notification-update'),

    re_path(r'^notification_type/$',
            UserNotificationTypeListAndCreateAPIView.as_view(),
            name='user-notification-type-list-create'),

    re_path(r'^notification_type/(?P<pk>\d+)/$',
            UserNotificationTypeDeleteAndUpdateAPIView.as_view(),
            name='user-notification-type-update-delete'),

    re_path('register/?$',
            UserRegisterView.as_view(),
            name="register"),

    re_path('verify/(?P<uid>.*)/(?P<token>.*)/?$',
            UserVerifyEmailView.as_view(),
            name="verify-email"),

    re_path('resource/?$',
            UserResourcesView.as_view(),
            name="resource-list-create"),

    re_path('resource/(?P<resource_id>[0-9a-f-]+)$',
            UserResourcesUpdateView.as_view(),
            name="resource-update"),

    re_path('list/?$',
            UserListView.as_view(),
            name="user-list"),
]
