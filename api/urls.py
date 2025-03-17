from django.urls import path, include
from .views import home

urlpatterns = [
    path('', home, name="api.home"),
    path('user/', include("api.user.urls")),
    path('project/', include("api.project.urls")),
    path('operation/', include("api.operation.urls")),
    path('finance/', include("api.finance.urls")),

]
