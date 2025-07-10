from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DataImportViewSet, FieldDefinitionViewSet, ImportTemplateViewSet

router = DefaultRouter()
router.register(r'sessions', DataImportViewSet, basename='dataimport')
router.register(r'field-definitions', FieldDefinitionViewSet, basename='fielddefinition')
router.register(r'templates', ImportTemplateViewSet, basename='importtemplate')

urlpatterns = [
    path('api/', include(router.urls)),
]