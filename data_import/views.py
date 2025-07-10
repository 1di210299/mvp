from django.shortcuts import render
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os
import uuid
from datetime import datetime

from .models import DataImportSession, ColumnMapping, ImportTemplate, FieldDefinition, FIELD_DEFINITIONS
from .serializers import (
    DataImportSessionSerializer, ColumnMappingSerializer, ImportTemplateSerializer,
    FieldDefinitionSerializer, FileUploadSerializer, AnalyzeFileSerializer,
    ColumnMappingCreateSerializer, ProcessImportSerializer, ImportResultSerializer
)
from .services import FileAnalysisService, ColumnMappingService, DataImportService


class DataImportViewSet(viewsets.ModelViewSet):
    """ViewSet para manejo de sesiones de importación"""
    serializer_class = DataImportSessionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return DataImportSession.objects.filter(
            company=self.request.user.company
        ).order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(
            company=self.request.user.company,
            user=self.request.user
        )
    
    @action(detail=False, methods=['post'])
    def upload_file(self, request):
        """Subir archivo y crear sesión de importación"""
        serializer = FileUploadSerializer(data=request.data)
        if serializer.is_valid():
            file = serializer.validated_data['file']
            import_type = serializer.validated_data['import_type']
            header_row = serializer.validated_data['header_row']
            
            try:
                # Generar nombre único para el archivo
                file_extension = os.path.splitext(file.name)[1]
                unique_filename = f"{uuid.uuid4()}{file_extension}"
                
                # Guardar archivo
                file_path = default_storage.save(
                    f"imports/{unique_filename}",
                    ContentFile(file.read())
                )
                
                # Crear sesión de importación
                session = DataImportSession.objects.create(
                    company=request.user.company,
                    user=request.user,
                    import_type=import_type,
                    original_filename=file.name,
                    file_path=default_storage.path(file_path),
                    file_size=file.size,
                    header_row=header_row,
                    status='pending'
                )
                
                return Response({
                    'session_id': session.id,
                    'message': 'Archivo subido exitosamente',
                    'next_step': 'analyze_file'
                }, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                return Response({
                    'error': f'Error al procesar archivo: {str(e)}'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def analyze_file(self, request, pk=None):
        """Analizar archivo y detectar columnas"""
        try:
            session = self.get_object()
            
            if session.status != 'pending':
                return Response({
                    'error': 'La sesión no está en estado pendiente'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Analizar archivo
            analysis = FileAnalysisService.analyze_file(
                session.file_path,
                session.header_row
            )
            
            # Actualizar sesión con información detectada
            session.detected_columns = analysis['detected_columns']
            session.total_rows = analysis['total_rows']
            session.status = 'mapping'
            session.save()
            
            # Obtener campos disponibles para el tipo de importación
            available_fields = FIELD_DEFINITIONS.get(session.import_type, [])
            
            # Sugerir mapeos automáticos
            suggested_mappings = ColumnMappingService.suggest_mappings(
                analysis['detected_columns'],
                session.import_type
            )
            
            return Response({
                'session_id': session.id,
                'detected_columns': analysis['detected_columns'],
                'sample_data': analysis['sample_data'],
                'total_rows': analysis['total_rows'],
                'column_info': analysis['column_info'],
                'available_fields': available_fields,
                'suggested_mappings': suggested_mappings,
                'next_step': 'configure_mapping'
            })
            
        except Exception as e:
            return Response({
                'error': f'Error al analizar archivo: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def configure_mapping(self, request, pk=None):
        """Configurar mapeo de columnas"""
        try:
            session = self.get_object()
            
            if session.status != 'mapping':
                return Response({
                    'error': 'La sesión no está en estado de mapeo'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            serializer = ColumnMappingCreateSerializer(data=request.data)
            if serializer.is_valid():
                mappings = serializer.validated_data['mappings']
                
                # Eliminar mapeos anteriores
                session.column_mappings.all().delete()
                
                # Crear nuevos mapeos
                available_fields = {f['field_name']: f for f in FIELD_DEFINITIONS.get(session.import_type, [])}
                
                for idx, mapping in enumerate(mappings):
                    source_column = mapping['source_column']
                    target_field = mapping.get('target_field')
                    
                    if target_field and target_field in available_fields:
                        field_def = available_fields[target_field]
                        
                        ColumnMapping.objects.create(
                            import_session=session,
                            source_column=source_column,
                            source_index=idx,
                            target_field=target_field,
                            field_type=field_def['field_type'],
                            is_required=field_def.get('is_required', False),
                            default_value=mapping.get('default_value', field_def.get('default_value', ''))
                        )
                
                # Validar mapeos requeridos
                required_fields = [f for f in available_fields.values() if f.get('is_required')]
                mapped_fields = [m['target_field'] for m in mappings if m.get('target_field')]
                missing_required = [f['display_name'] for f in required_fields if f['field_name'] not in mapped_fields]
                
                if missing_required:
                    return Response({
                        'error': 'Faltan campos requeridos',
                        'missing_fields': missing_required
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                return Response({
                    'message': 'Mapeo configurado exitosamente',
                    'mapped_columns': len(mappings),
                    'next_step': 'process_import'
                })
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'error': f'Error al configurar mapeo: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def process_import(self, request, pk=None):
        """Procesar importación de datos"""
        try:
            session = self.get_object()
            
            if session.status != 'mapping':
                return Response({
                    'error': 'La sesión no está lista para procesar'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            serializer = ProcessImportSerializer(data=request.data)
            if serializer.is_valid():
                # Actualizar configuración de sesión
                session.skip_duplicates = serializer.validated_data['skip_duplicates']
                session.update_existing = serializer.validated_data['update_existing']
                session.status = 'processing'
                session.save()
                
                # Procesar importación
                results = DataImportService.process_import(
                    session,
                    serializer.validated_data['start_row'],
                    serializer.validated_data.get('end_row')
                )
                
                return Response({
                    'message': 'Importación completada',
                    'results': {
                        'total_rows': results['total_rows'],
                        'successful_rows': results['successful_rows'],
                        'failed_rows': results['failed_rows'],
                        'completion_percentage': (results['successful_rows'] / results['total_rows']) * 100 if results['total_rows'] > 0 else 0,
                        'errors': results['errors'][:10]  # Solo primeros 10 errores
                    }
                })
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'error': f'Error al procesar importación: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """Obtener estado de la importación"""
        session = self.get_object()
        
        return Response({
            'session_id': session.id,
            'status': session.status,
            'import_type': session.import_type,
            'original_filename': session.original_filename,
            'total_rows': session.total_rows,
            'processed_rows': session.processed_rows,
            'successful_rows': session.successful_rows,
            'failed_rows': session.failed_rows,
            'completion_percentage': (session.processed_rows / session.total_rows) * 100 if session.total_rows > 0 else 0,
            'created_at': session.created_at,
            'completed_at': session.completed_at,
        })
    
    @action(detail=True, methods=['get'])
    def errors(self, request, pk=None):
        """Obtener errores de la importación"""
        session = self.get_object()
        
        return Response({
            'session_id': session.id,
            'error_log': session.error_log,
            'failed_rows': session.failed_rows
        })


class FieldDefinitionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para consultar definiciones de campos disponibles"""
    serializer_class = FieldDefinitionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return FieldDefinition.objects.filter(is_active=True)
    
    @action(detail=False, methods=['get'])
    def by_import_type(self, request):
        """Obtener campos disponibles por tipo de importación"""
        import_type = request.query_params.get('import_type')
        
        if not import_type:
            return Response({
                'error': 'Parámetro import_type requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if import_type not in FIELD_DEFINITIONS:
            return Response({
                'error': 'Tipo de importación no válido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        fields = FIELD_DEFINITIONS[import_type]
        
        return Response({
            'import_type': import_type,
            'fields': fields
        })


class ImportTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet para plantillas de importación"""
    serializer_class = ImportTemplateSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return ImportTemplate.objects.filter(
            company=self.request.user.company
        ).order_by('-usage_count', 'name')
    
    def perform_create(self, serializer):
        serializer.save(
            company=self.request.user.company,
            user=self.request.user
        )
    
    @action(detail=True, methods=['post'])
    def use_template(self, request, pk=None):
        """Usar plantilla para crear mapeo automático"""
        template = self.get_object()
        session_id = request.data.get('session_id')
        
        if not session_id:
            return Response({
                'error': 'session_id requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            session = DataImportSession.objects.get(
                id=session_id,
                company=request.user.company
            )
            
            if session.import_type != template.import_type:
                return Response({
                    'error': 'Tipo de importación no coincide con la plantilla'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Aplicar mapeos de la plantilla
            session.column_mappings.all().delete()
            
            available_fields = {f['field_name']: f for f in FIELD_DEFINITIONS.get(session.import_type, [])}
            
            for source_col, target_field in template.column_mappings.items():
                if source_col in session.detected_columns and target_field in available_fields:
                    field_def = available_fields[target_field]
                    
                    ColumnMapping.objects.create(
                        import_session=session,
                        source_column=source_col,
                        source_index=session.detected_columns.index(source_col),
                        target_field=target_field,
                        field_type=field_def['field_type'],
                        is_required=field_def.get('is_required', False)
                    )
            
            # Incrementar contador de uso
            template.usage_count += 1
            template.save()
            
            return Response({
                'message': 'Plantilla aplicada exitosamente',
                'mapped_columns': len(template.column_mappings)
            })
            
        except DataImportSession.DoesNotExist:
            return Response({
                'error': 'Sesión de importación no encontrada'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': f'Error al aplicar plantilla: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
