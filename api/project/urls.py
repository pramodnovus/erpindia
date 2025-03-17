from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *
from api.project.admin import project_autocomplete  # Import custom view


router = DefaultRouter()
router.register(r'clients', ClientViewSet, basename="clients")
router.register(r'project_type', ProjectTypeViewSet, basename="project_type")
router.register(r'userrole', UserRoleViewSet, basename="project-managers")
router.register(r'update', ProjectUpdateView, basename='project-update')

urlpatterns = [
    path('', include(router.urls)),
    path('projects/', ProjectListAPIView.as_view(), name='project-list'),
    path('admin/project-autocomplete/', project_autocomplete, name='project-autocomplete'),  # Add autocomplete URL
    path('dashbord-projects/', DashboardProjectListAPIView.as_view(), name='dashbord-project-list'),
    path('projects/<int:pk>/', ProjectDetailAPIView.as_view(), name='project-detail'),
    path('projects/<int:pk>/custom_action/', ProjectCustomActionAPIView.as_view(), name='project-custom-action'),
    path('userrole/managers/<int:manager_id>/teamleads/', TeamLeadsUnderManagerView.as_view(), name='teamleads-under-manager'),
    path('project-assignments/', ProjectAssignmentAPIView.as_view(), name='project-assignment'),
    path('update-project-status/', UpdateProjectStatusAPIView.as_view(), name='update_project_status'),
    path('interview/samplesize/edit', ProjectEmailView.as_view(), name='edit_project_sample'),
    path('updated-data/<int:project_id>/', ProjectUpdatedDataView.as_view(), name='project-updated-data'),
    path('<int:project_id>/get-update/sow/', ProjectDocumentUpdateView.as_view(), name='project-document-update'),
    path('project_type/update/<int:id>/',ProjectTypeUpdateView.as_view(),name='project-type-update'),
    #path('project-samples/', ProjectSampleListCreateView.as_view(), name='project-sample-list-create'),
    path('project-samples/edit/<int:pk>/',ProjectSampleDetailView.as_view(), name='project-sample-detail'),
    path('reject-samples/<int:project_id>/', ProjectSampleReject.as_view(), name='reject_samples'),
    path('project-samples/<int:pk>/approve/', ApproveSampleRevisionView.as_view(), name='approve-sample'),
    path('notifications/count/', NotificationCountAPIView.as_view(), name='notification-unread-count'),


]
