"""
Vistas de autenticación organizadas por funcionalidad
"""

# Vistas de autenticación
from .auth import (
    RegisterView,
    LoginView,
    ProfileView,
    ChangePasswordView,
    TokenRefreshView,
    LogoutView
)

# Vistas de gestión de empresa
from .company import (
    CompanyViewSet,
    UserViewSet,
    CompanyWhatsAppConfigView,
    WhatsAppTestView
)

# Vistas de configuraciones
from .settings import (
    UserSettingsView,
    SystemInfoView
)

__all__ = [
    # Autenticación
    'RegisterView',
    'LoginView',
    'ProfileView',
    'ChangePasswordView',
    'TokenRefreshView',
    'LogoutView',
    
    # Empresa
    'CompanyViewSet',
    'UserViewSet',
    'CompanyWhatsAppConfigView',
    'WhatsAppTestView',
    
    # Configuraciones
    'UserSettingsView',
    'SystemInfoView',
]
