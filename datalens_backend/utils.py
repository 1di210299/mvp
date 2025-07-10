# utils.py - Funciones utilitarias para toda la aplicación
from authentication.models import Company

def get_default_company():
    """
    Obtiene la empresa por defecto para usar en toda la aplicación.
    Prioriza 'Distribuidora San Martín SAC' que tiene los productos peruanos reales.
    """
    try:
        # Intentar obtener la empresa con productos peruanos reales
        company = Company.objects.get(name='Distribuidora San Martín SAC')
        return company
    except Company.DoesNotExist:
        # Fallback a la primera empresa disponible
        return Company.objects.first()

def get_company_for_user(user=None):
    """
    Obtiene la empresa apropiada para un usuario.
    Si no hay usuario autenticado, usa la empresa por defecto.
    """
    if user and hasattr(user, 'company') and user.company:
        return user.company
    return get_default_company()