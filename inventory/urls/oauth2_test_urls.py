"""
URLs para testing OAuth2 y configuración
"""
from django.urls import path
from inventory.views import oauth2_test_views, oauth2_admin_views

urlpatterns = [
    # Test OAuth2 Token
    path('test-oauth-token/', oauth2_test_views.test_oauth_token, name='test_oauth_token'),
    
    # Test Client Credentials Grant
    path('test-client-credentials/', oauth2_test_views.test_client_credentials, name='test_client_credentials'),
    
    # Test configuración completa
    path('test-full-config/', oauth2_test_views.test_full_config, name='test_full_config'),
    
    # Admin helpers
    path('create-test-app/', oauth2_admin_views.create_test_oauth_app, name='create_test_oauth_app'),
    path('list-apps/', oauth2_admin_views.get_oauth_apps, name='get_oauth_apps'),
]
