from rest_framework import serializers
from .models import DataImportSession, ColumnMapping, ImportTemplate, FieldDefinition
import pandas as pd
import os
from django.conf import settings


class FieldDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FieldDefinition
        fields = '__all__'


class ColumnMappingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ColumnMapping
        fields = '__all__'


class DataImportSessionSerializer(serializers.ModelSerializer):
    column_mappings = ColumnMappingSerializer(many=True, read_only=True)
    
    class Meta:
        model = DataImportSession
        fields = '__all__'
        read_only_fields = ('company', 'user', 'detected_columns', 'total_rows', 'file_path')


class ImportTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImportTemplate
        fields = '__all__'
        read_only_fields = ('company', 'user', 'usage_count')


class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    import_type = serializers.ChoiceField(choices=DataImportSession.IMPORT_TYPES)
    header_row = serializers.IntegerField(default=1, min_value=1)
    
    def validate_file(self, value):
        """Validar el archivo subido"""
        # Validar extensión
        allowed_extensions = ['.xlsx', '.xls', '.csv']
        file_extension = os.path.splitext(value.name)[1].lower()
        
        if file_extension not in allowed_extensions:
            raise serializers.ValidationError(
                f"Formato de archivo no soportado. Formatos permitidos: {', '.join(allowed_extensions)}"
            )
        
        # Validar tamaño (máximo 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if value.size > max_size:
            raise serializers.ValidationError(
                "El archivo es demasiado grande. Tamaño máximo: 10MB"
            )
        
        return value


class AnalyzeFileSerializer(serializers.Serializer):
    """Serializer para analizar las columnas del archivo"""
    session_id = serializers.IntegerField()
    detected_columns = serializers.ListField(child=serializers.CharField(), read_only=True)
    sample_data = serializers.ListField(read_only=True)
    total_rows = serializers.IntegerField(read_only=True)
    available_fields = serializers.ListField(read_only=True)
    suggested_mappings = serializers.DictField(read_only=True)


class ColumnMappingCreateSerializer(serializers.Serializer):
    """Serializer para crear mapeos de columnas"""
    session_id = serializers.IntegerField()
    mappings = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField()
        )
    )
    
    def validate_mappings(self, value):
        """Validar los mapeos de columnas"""
        for mapping in value:
            required_keys = ['source_column', 'target_field']
            for key in required_keys:
                if key not in mapping:
                    raise serializers.ValidationError(
                        f"Falta la clave '{key}' en el mapeo"
                    )
        return value


class ProcessImportSerializer(serializers.Serializer):
    """Serializer para procesar la importación"""
    session_id = serializers.IntegerField()
    skip_duplicates = serializers.BooleanField(default=True)
    update_existing = serializers.BooleanField(default=False)
    start_row = serializers.IntegerField(default=2, min_value=1)
    end_row = serializers.IntegerField(required=False, min_value=1)


class ImportResultSerializer(serializers.Serializer):
    """Serializer para los resultados de importación"""
    session_id = serializers.IntegerField(read_only=True)
    status = serializers.CharField(read_only=True)
    total_rows = serializers.IntegerField(read_only=True)
    processed_rows = serializers.IntegerField(read_only=True)
    successful_rows = serializers.IntegerField(read_only=True)
    failed_rows = serializers.IntegerField(read_only=True)
    error_log = serializers.ListField(read_only=True)
    completion_percentage = serializers.FloatField(read_only=True)