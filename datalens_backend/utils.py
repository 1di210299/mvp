# utils.py - Funciones utilitarias para toda la aplicación
from authentication.models import Company

def get_default_company():
    """
    Obtiene la empresa por defecto para usar en toda la aplicación.
    Prioriza 'Distribuidora San Martín SAC' que tiene los productos peruanos reales.
    """
    try:
        print(f"🏢 get_default_company() - Buscando empresa por defecto...")
        
        # Intentar obtener la empresa con productos peruanos reales
        company = Company.objects.filter(name='Distribuidora San Martín SAC').first()
        if company:
            print(f"✅ Empresa 'Distribuidora San Martín SAC' encontrada: ID={company.id}, activa={company.is_active}")
            return company
        else:
            print(f"❌ No se encontró 'Distribuidora San Martín SAC'")
        
        # Si no existe, buscar cualquier empresa activa
        company = Company.objects.filter(is_active=True).first()
        if company:
            print(f"✅ Empresa activa alternativa encontrada: {company.name} (ID={company.id})")
            return company
        else:
            print(f"❌ No se encontró ninguna empresa activa")
            
        # Fallback a la primera empresa disponible
        company = Company.objects.first()
        if company:
            print(f"✅ Primera empresa disponible: {company.name} (ID={company.id}, activa={company.is_active})")
            return company
        else:
            print(f"❌ No hay empresas en la base de datos")
            
        return None
        
    except Exception as e:
        # En caso de cualquier error, devolver None
        print(f"❌ Error en get_default_company: {e}")
        return None

def get_company_for_user(user=None):
    """
    Obtiene la empresa apropiada para un usuario.
    Si no hay usuario autenticado, usa la empresa por defecto.
    """
    if user and hasattr(user, 'company') and user.company:
        return user.company
    return get_default_company()