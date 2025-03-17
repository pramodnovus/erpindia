from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.urlpatterns import format_suffix_patterns
from .views import *
from api.user import views


router = DefaultRouter()
router.register(r'register', UserRegistrationViewSet, basename='user-registration')
router.register(r'zone', ZoneViewSet,basename='zone')
router.register(r'region', RegionViewSet,basename='region')
router.register(r'city', CityViewSet,basename='city')
router.register(r'country', CountryViewSet)



urlpatterns = [
    path('', include(router.urls)),
    path('login/', UserLoginViewSet.as_view({'post': 'create'}), name='user-login'),
    path('api/users-list/', UserLists.as_view(), name='user-list'),
    path('change-password/', ChangePasswordViewSet.as_view({'post': 'create'}), name='change-password'),
    path('send_reset_password_email/', SendPasswordResetEmailView.as_view({'post': 'create'}), name='send_reset_password_email'),
    path('confirm-password/<uid>/<token>/', UserPasswordResetView.as_view(), name='reset-password'),
    path('user/status/', UpdateUserStatusAPIView.as_view(), name='update-user-status'),
    path('update-profile/', UpdateProfileAPIView.as_view(), name='update_profile'),
    # path('api/user-reports/<int:user_id>/', UserReportsView.as_view(), name='user-reports'),
    path('entity/<int:pk>/', CompanyDetailAPIView.as_view(), name='company-detail'),
    path('entities/', AllCompaniesAPIView.as_view(), name='all-companies'),

  
]

