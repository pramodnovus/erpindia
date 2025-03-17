"""
URL configuration for novuscrm project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
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
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from novuscrm import settings
from rest_framework_simplejwt import views as jwt_views
from django.conf.urls.static import static
from rest_framework_simplejwt.views import (TokenObtainPairView, TokenRefreshView,)

from django.views.generic import TemplateView
from rest_framework.schemas import get_schema_view
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.urls import path

def trigger_error(request):
    division_by_zero = 1 / 0

# import yaml
# credentials = yaml.load(open('./testproject/credentials.yml','r'),Loader=yaml.FullLoader)

swaggerurl = [
    path('api/', include('api.urls')),
]

schema_view = get_schema_view(
   openapi.Info(
      title="NovusCRM",
      default_version='v1',
      description="Test description",
      terms_of_service="https://www.novusinsights.com/policies/terms/",
      contact=openapi.Contact(email="contact@novus.helpdesk"),
      license=openapi.License(name="Test License"),
   ),
   
   #url= credentials['HOST_URL']+'api/v1/',
   #url = "http://127.0.0.1:8000/",
   url = "https://uaterpapi.unimrkt.com/",
   public=True,
   permission_classes=[permissions.AllowAny],
   patterns=swaggerurl
)


urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/",include("api.urls")),
    path("api-auth/",include("rest_framework.urls")),
    path('accounts/', include('allauth.urls')),
    path('apis/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('auth/', include('dj_rest_auth.urls')),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('sentry-debug/', trigger_error),
    
]


urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
