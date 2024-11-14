# ruff: noqa: E501
from django.conf import settings
from django.urls import path, include, re_path
from rest_framework import permissions

from authentication.views.login import MyTokenObtainPairView, MyTokenRefreshView
from users.views.user import TestEndpointView
from users.views.admin_user import AdminTokenObtainPairView

from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Predico - Restful-API",
        default_version='v1',
        description="""
#### Description:
Restful API for **Predico - Collaborative Forecasting Service** (Proof of Concept Version).

### Visit the [Official Landing Page](https://predico-elia.inesctec.pt/)

## Main functions:
- **Market management**:
    * List market sessions and challenges
    * List ensemble forecasts / weights / contributions per forecasting challenges
    * Manage (List/Create/Update) user forecast submissions per forecasting challenge

- **Data management**:
    * Upload and access your historical forecasts data
    * Access raw measurements data, published by the Market Maker

## Developers // Contacts:
- andre.f.garcia@inesctec.pt
- carla.s.goncalves@inesctec.pt
- giovanni.buroni@inesctec.pt
- jose.r.andrade@inesctec.pt
- ricardo.j.bessa@inesctec.pt

By: INESC TEC - Centre for Power and Energy Systems (2024)

""",
        license=openapi.License(
            name="GNU AFFERO GENERAL PUBLIC LICENSE",
            url="https://github.com/INESCTEC/predico-collabforecast/blob/main/LICENSE"
        ),
    ),
    public=True,
    permission_classes=[permissions.AllowAny, ],
    url=settings.SWAGGER_BASE_URL
)

v1_urlpatterns = [
    # Authentication endpoint for private admin access (superuser)
    re_path('admin/token', AdminTokenObtainPairView.as_view(), name='admin_token_obtain_pair'),
    re_path('token', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    re_path('token/refresh', MyTokenRefreshView.as_view(), name='token_refresh'),

    re_path('market/', include('market.urls'), name="market"),
    re_path('user/', include('users.urls'), name="user"),
    re_path('data/', include('data.urls'), name="data"),
    re_path('test/', TestEndpointView.as_view(), name="test-service"),
]

urlpatterns = [
    path('api/v1/', include(v1_urlpatterns)),
    # Auto-Docs
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'), # noqa
    re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'), # noqa
    re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'), # noqa
]
