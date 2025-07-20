# Views package for authentication - Organized structure

# Import authentication views
from .auth import (
    CustomTokenObtainPairView,
    RegisterView, 
    CustomTokenRefreshView,
    TokenValidationView
)

# Import model viewsets
from .models_viewsets import (
    CompanyViewSet,
    UserViewSet
)

# Import profile views
from .profile import (
    ProfileView,
    ChangePasswordView
)

# Import settings views
from .settings import (
    UserSettingsView,
    SystemInfoView
)

# Import company settings views
from .company_settings import (
    CompanyWhatsAppConfigView, 
    WhatsAppTestView
)

# Make all views available when importing from this package
__all__ = [
    # Authentication
    'CustomTokenObtainPairView',
    'RegisterView',
    'CustomTokenRefreshView', 
    'TokenValidationView',
    
    # Model ViewSets
    'CompanyViewSet',
    'UserViewSet',
    
    # Profile
    'ProfileView',
    'ChangePasswordView',
    
    # Settings
    'UserSettingsView',
    'SystemInfoView',
    
    # Company Settings
    'CompanyWhatsAppConfigView',
    'WhatsAppTestView'
]
