# ruff: noqa: E501
"""api URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.urls import path, include, re_path
from rest_framework import permissions

from authentication.views.login import MyTokenObtainPairView, MyTokenRefreshView
from users.views.user import TestEndpointView
from .views import front_page_view

from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Predico - Restful-API",
        default_version='v1',
        description="""
#### Description:
Restful API for the INESC TEC Collaborative Forecasting Service. (Predico - Demo Version)

## Main functions:
- **User management**:
    * Register new user
    * User verification / authentication
    * User password reset
    * Manage User Resources (i.e., assets in user portfolio) (create/update/delete)

- **Market management**:
    * Manage (List/Create/Update) Market Sessions
    * Manage (List/Create/Update) forecasting challenges per Market Sessions
    * Manage (List/Create) ensemble forecasts /weights per forecasting challenges
    * Manage (List/Create) user forecast submissions per forecasting challenge

- **Data management**:
    * Raw Data Ingestion (market maker measurements)
    * Historical Forecasts Data Ingestion (individual forecasters data)
    * Data Access based on period and resource params

## Developers // Contacts:
- andre.f.garcia@inesctec.pt
- carla.s.goncalves@inesctec.pt
- giovanni.buroni@inesctec.pt
- jose.r.andrade@inesctec.pt
- ricardo.j.bessa@inesctec.pt
""",
        license=openapi.License(
            name="GNU AFFERO GENERAL PUBLIC LICENSE",
            url="https://github.com/INESCTEC/collabforecast/blob/main/LICENSE"
        ),
    ),
    public=True,
    permission_classes=[permissions.AllowAny, ],
    url=settings.SWAGGER_BASE_URL
)

v1_urlpatterns = [
    # API urls:
    re_path('token/refresh', MyTokenRefreshView.as_view(), name='token_refresh'),
    re_path('token', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    re_path('market/', include('market.urls'), name="market"),
    re_path('user/', include('users.urls'), name="user"),
    re_path('data/', include('data.urls'), name="data"),
    re_path('test/', TestEndpointView.as_view(), name="test-service"),
]

urlpatterns = [
    path('api/v1/', include(v1_urlpatterns)),
    # Auto-Docs
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
