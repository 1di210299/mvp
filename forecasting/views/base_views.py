"""
Vistas base y utilidades comunes para forecasting
"""

from rest_framework.pagination import PageNumberPagination
from datalens_backend.utils import get_default_company
import logging

logger = logging.getLogger(__name__)


class ForecastPagination(PageNumberPagination):
    """Paginación optimizada para pronósticos"""
    page_size = 50  # Solo 50 pronósticos por página
    page_size_query_param = 'page_size'
    max_page_size = 100  # Máximo 100 items por página


def get_user_company(request):
    """Obtener la empresa del usuario o la empresa por defecto"""
    try:
        if hasattr(request.user, 'company') and request.user.company:
            return request.user.company
        return get_default_company()
    except Exception as e:
        logger.error(f"Error getting user company: {str(e)}")
        return get_default_company()


__all__ = ['ForecastPagination', 'get_user_company']
