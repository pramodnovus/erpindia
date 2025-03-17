from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *


router = DefaultRouter()


urlpatterns = [
    # path('', include(router.urls)),
    path('projects/add/man-days/', ProjectUpdateBulkAPIView.as_view(), name='project-update-bulk'),
    path('projects/man-days/perday/', OperationTeamListView.as_view(), name='operation-team-list'),
    path('project/perday/list/', OperationTeamProjectListView.as_view(), name='project-update-list'),
    path('project/man-days/edit', ProjectUpdateBatchEditView.as_view(), name='project-update-edit'),
    path('project/perday/list/', OperationTeamProjectListView.as_view(), name='project-update-list')
   

]
