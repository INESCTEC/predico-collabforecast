# ruff: noqa: E501
from django.urls import re_path, path

from .views.user import (UserByTokenView,
                         EmailVerificationView,
                         UserListView,
                         UserRegisterView,
                         GenerateRegisterTokenView,
                         UserVerifyEmailView)
from .views.user_reset_password import (PasswordResetRequestView,
                                        PasswordResetView)

from .views.user_resources import (UserResourcesUpdateView,
                                   UserResourcesView)

app_name = "user"
urlpatterns = [
    # Password reset views
    re_path('password-reset/confirm/?$',
            PasswordResetView.as_view(),
            name='password-reset-confirm'),
    re_path('password-reset/?$',
            PasswordResetRequestView.as_view(),
            name='password-reset-request'),
    # re_path('verify-email/(?P<uidb64>[\w-]+)/(?P<token>[\w-]+)/$',
    #         EmailVerificationView.as_view(),
    #         name='verify-email'),
    re_path('user-detail/',
            UserByTokenView.as_view(),
            name='get_user_by_token'),
    re_path('register/?$',
            UserRegisterView.as_view(),
            name="register"),
    re_path('register-invite/?$',
            GenerateRegisterTokenView.as_view(),
            name="admin-register"),
    path('verify/', UserVerifyEmailView.as_view(), name="verify-email"),

    # re_path('verify/(?P<uid>.*)/(?P<token>.*)/?$',
    #         UserVerifyEmailView.as_view(),
    #         name="verify-email"),
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
