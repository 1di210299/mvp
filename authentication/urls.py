from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'companies', views.CompanyViewSet)
router.register(r'users', views.UserViewSet)

urlpatterns = [
    # JWT Authentication - using custom login view
    path('login/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', views.CustomTokenRefreshView.as_view(), name='token_refresh'),  # Cambiado a vista personalizada
    path('validate-token/', views.TokenValidationView.as_view(), name='token_validate'),  # NUEVO
    path('register/', views.RegisterView.as_view(), name='register'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change_password'),
    
    # Settings endpoints
    path('settings/', views.UserSettingsView.as_view(), name='user_settings'),
    path('system-info/', views.SystemInfoView.as_view(), name='system_info'),
    
    # ViewSets
    path('', include(router.urls)),
]
