"""
Sistema de campos personalizados para diferentes empresas
"""
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.exceptions import ValidationError
import json


class CustomFieldDefinition(models.Model):
    """Define campos personalizados que cada empresa puede agregar"""
    
    FIELD_TYPES = [
        ('text', 'Texto'),
        ('number', 'Número'),
        ('decimal', 'Decimal'),
        ('date', 'Fecha'),
        ('datetime', 'Fecha y Hora'),
        ('boolean', 'Sí/No'),
        ('choice', 'Lista de opciones'),
        ('email', 'Email'),
        ('url', 'URL'),
        ('phone', 'Teléfono'),
    ]
    
    MODEL_TYPES = [
        ('product', 'Producto'),
        ('supplier', 'Proveedor'),
        ('category', 'Categoría'),
        ('inventory_item', 'Item de Inventario'),
        ('transaction', 'Transacción'),
    ]
    
    company = models.ForeignKey(
        'authentication.Company',
        on_delete=models.CASCADE,
        related_name='custom_field_definitions'
    )
    
    # Para qué modelo se aplica este campo
    model_type = models.CharField(max_length=50, choices=MODEL_TYPES)
    
    # Definición del campo
    field_name = models.CharField(max_length=100, verbose_name="Nombre del campo")
    field_label = models.CharField(max_length=200, verbose_name="Etiqueta mostrada")
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES)
    
    # Opciones adicionales
    is_required = models.BooleanField(default=False, verbose_name="Campo obligatorio")
    default_value = models.TextField(blank=True, verbose_name="Valor por defecto")
    help_text = models.TextField(blank=True, verbose_name="Texto de ayuda")
    
    # Para campos de tipo 'choice'
    choices_json = models.TextField(
        blank=True, 
        verbose_name="Opciones (JSON)",
        help_text="Para campos de tipo 'choice', formato: [{'value': 'val1', 'label': 'Label 1'}]"
    )
    
    # Validaciones
    min_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    min_length = models.IntegerField(null=True, blank=True)
    max_length = models.IntegerField(null=True, blank=True)
    
    # Metadatos
    order = models.IntegerField(default=0, verbose_name="Orden de visualización")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = [['company', 'model_type', 'field_name']]
        ordering = ['model_type', 'order', 'field_name']
    
    def __str__(self):
        return f"{self.company.name} - {self.get_model_type_display()} - {self.field_label}"
    
    def get_choices(self):
        """Obtiene las opciones para campos de tipo choice"""
        if self.field_type == 'choice' and self.choices_json:
            try:
                return json.loads(self.choices_json)
            except json.JSONDecodeError:
                return []
        return []
    
    def clean(self):
        if self.field_type == 'choice' and not self.choices_json:
            raise ValidationError("Los campos de tipo 'choice' requieren opciones definidas")


class CustomFieldValue(models.Model):
    """Almacena los valores de los campos personalizados"""
    
    custom_field = models.ForeignKey(
        CustomFieldDefinition,
        on_delete=models.CASCADE,
        related_name='values'
    )
    
    # Referencia genérica al objeto que tiene este valor
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Valores para diferentes tipos de datos
    text_value = models.TextField(blank=True)
    number_value = models.BigIntegerField(null=True, blank=True)
    decimal_value = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    date_value = models.DateField(null=True, blank=True)
    datetime_value = models.DateTimeField(null=True, blank=True)
    boolean_value = models.BooleanField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = [['custom_field', 'content_type', 'object_id']]
    
    def get_value(self):
        """Obtiene el valor apropiado según el tipo de campo"""
        field_type = self.custom_field.field_type
        
        if field_type == 'text' or field_type == 'choice' or field_type == 'email' or field_type == 'url' or field_type == 'phone':
            return self.text_value
        elif field_type == 'number':
            return self.number_value
        elif field_type == 'decimal':
            return self.decimal_value
        elif field_type == 'date':
            return self.date_value
        elif field_type == 'datetime':
            return self.datetime_value
        elif field_type == 'boolean':
            return self.boolean_value
        
        return None
    
    def set_value(self, value):
        """Establece el valor apropiado según el tipo de campo"""
        field_type = self.custom_field.field_type
        
        # Limpiar valores anteriores
        self.text_value = ''
        self.number_value = None
        self.decimal_value = None
        self.date_value = None
        self.datetime_value = None
        self.boolean_value = None
        
        if field_type in ['text', 'choice', 'email', 'url', 'phone']:
            self.text_value = str(value) if value is not None else ''
        elif field_type == 'number':
            self.number_value = int(value) if value is not None else None
        elif field_type == 'decimal':
            self.decimal_value = float(value) if value is not None else None
        elif field_type == 'date':
            self.date_value = value
        elif field_type == 'datetime':
            self.datetime_value = value
        elif field_type == 'boolean':
            self.boolean_value = bool(value) if value is not None else None


class CustomFieldMixin:
    """Mixin para agregar funcionalidad de campos personalizados a los modelos"""
    
    def get_custom_fields(self):
        """Obtiene todos los campos personalizados definidos para este modelo"""
        if not hasattr(self, '_custom_fields_cache'):
            model_name = self._meta.model_name
            content_type = ContentType.objects.get_for_model(self)
            
            # Mapeo de nombres de modelo
            model_type_map = {
                'product': 'product',
                'supplier': 'supplier',
                'category': 'category',
                'inventoryitem': 'inventory_item',
                'transaction': 'transaction',
            }
            
            model_type = model_type_map.get(model_name)
            if model_type and hasattr(self, 'company'):
                self._custom_fields_cache = CustomFieldDefinition.objects.filter(
                    company=self.company,
                    model_type=model_type,
                    is_active=True
                ).order_by('order', 'field_name')
            else:
                self._custom_fields_cache = CustomFieldDefinition.objects.none()
        
        return self._custom_fields_cache
    
    def get_custom_field_values(self):
        """Obtiene los valores de los campos personalizados para esta instancia"""
        if not self.pk:
            return {}
        
        content_type = ContentType.objects.get_for_model(self)
        values = CustomFieldValue.objects.filter(
            content_type=content_type,
            object_id=self.pk
        ).select_related('custom_field')
        
        return {value.custom_field.field_name: value.get_value() for value in values}
    
    def set_custom_field_value(self, field_name, value):
        """Establece el valor de un campo personalizado"""
        if not self.pk:
            raise ValueError("El objeto debe estar guardado antes de establecer campos personalizados")
        
        try:
            custom_field = self.get_custom_fields().get(field_name=field_name)
        except CustomFieldDefinition.DoesNotExist:
            raise ValueError(f"Campo personalizado '{field_name}' no existe para este modelo")
        
        content_type = ContentType.objects.get_for_model(self)
        
        field_value, created = CustomFieldValue.objects.get_or_create(
            custom_field=custom_field,
            content_type=content_type,
            object_id=self.pk
        )
        
        field_value.set_value(value)
        field_value.save()
        
        return field_value
