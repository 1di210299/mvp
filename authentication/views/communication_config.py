"""
Vistas para gestionar las configuraciones de comunicación por tenant
Permite a los clientes configurar sus preferencias de canal para cada evento
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction
from authentication.models import TenantConfig, TenantCommunicationConfig, TenantAIConfig
from authentication.serializers import (
    TenantCommunicationConfigSerializer, 
    TenantAIConfigSerializer
)
from authentication.auth import TenantJWTAuthentication
import logging

logger = logging.getLogger(__name__)


@api_view(['GET', 'POST'])
@authentication_classes([TenantJWTAuthentication])
@permission_classes([IsAuthenticated])
def tenant_communication_configs(request, tenant_id):
    """
    GET: Obtener todas las configuraciones de comunicación del tenant
    POST: Crear nueva configuración de comunicación
    """
    # Verificar que el tenant existe y coincide con el JWT
    tenant = get_object_or_404(TenantConfig, tenant_id=tenant_id)
    
    # Verificar que el tenant del JWT coincide con el solicitado
    if hasattr(request.user, 'tenant_id') and str(request.user.tenant_id) != str(tenant_id):
        return Response(
            {'error': 'No tienes permisos para acceder a este tenant'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    if request.method == 'GET':
        configs = TenantCommunicationConfig.objects.filter(tenant=tenant)
        serializer = TenantCommunicationConfigSerializer(configs, many=True)
        
        # Agregar información de eventos disponibles
        available_events = TenantCommunicationConfig.EVENT_CHOICES
        configured_events = configs.values_list('event_type', flat=True)
        
        response_data = {
            'tenant_id': str(tenant_id),
            'tenant_name': tenant.name,
            'configurations': serializer.data,
            'available_events': [
                {
                    'key': event[0],
                    'label': event[1],
                    'configured': event[0] in configured_events
                }
                for event in available_events
            ],
            'channel_options': TenantCommunicationConfig.CHANNEL_CHOICES,
            'priority_options': TenantCommunicationConfig.PRIORITY_CHOICES
        }
        
        return Response(response_data)
    
    elif request.method == 'POST':
        # Crear nueva configuración
        data = request.data.copy()
        data['tenant'] = tenant.tenant_id
        
        serializer = TenantCommunicationConfigSerializer(data=data)
        if serializer.is_valid():
            try:
                config = serializer.save()
                logger.info(f"Configuración creada para tenant {tenant.name}: {config.event_type}")
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e:
                logger.error(f"Error creando configuración: {str(e)}")
                return Response(
                    {'error': 'Error interno del servidor'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@authentication_classes([TenantJWTAuthentication])
@permission_classes([IsAuthenticated])
def tenant_communication_config_detail(request, tenant_id, event_type):
    """
    GET: Obtener configuración específica de un evento
    PUT: Actualizar configuración de un evento
    DELETE: Eliminar configuración de un evento
    """
    tenant = get_object_or_404(TenantConfig, tenant_id=tenant_id)
    config = get_object_or_404(
        TenantCommunicationConfig, 
        tenant=tenant, 
        event_type=event_type
    )
    
    if request.method == 'GET':
        serializer = TenantCommunicationConfigSerializer(config)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = TenantCommunicationConfigSerializer(config, data=request.data, partial=True)
        if serializer.is_valid():
            try:
                updated_config = serializer.save()
                logger.info(f"Configuración actualizada para {tenant.name}: {event_type}")
                return Response(serializer.data)
            except Exception as e:
                logger.error(f"Error actualizando configuración: {str(e)}")
                return Response(
                    {'error': 'Error interno del servidor'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        try:
            config.delete()
            logger.info(f"Configuración eliminada para {tenant.name}: {event_type}")
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"Error eliminando configuración: {str(e)}")
            return Response(
                {'error': 'Error interno del servidor'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['POST'])
@authentication_classes([TenantJWTAuthentication])
@permission_classes([IsAuthenticated])
def tenant_bulk_config_setup(request, tenant_id):
    """
    Configuración masiva de eventos para un tenant
    Útil para el onboarding inicial
    """
    tenant = get_object_or_404(TenantConfig, tenant_id=tenant_id)
    configurations = request.data.get('configurations', [])
    
    if not configurations:
        return Response(
            {'error': 'Se requiere al menos una configuración'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        with transaction.atomic():
            created_configs = []
            updated_configs = []
            errors = []
            
            for config_data in configurations:
                config_data['tenant'] = tenant.tenant_id
                event_type = config_data.get('event_type')
                
                if not event_type:
                    errors.append({'error': 'event_type es requerido', 'data': config_data})
                    continue
                
                # Verificar si ya existe la configuración
                existing_config = TenantCommunicationConfig.objects.filter(
                    tenant=tenant, 
                    event_type=event_type
                ).first()
                
                if existing_config:
                    # Actualizar existente
                    serializer = TenantCommunicationConfigSerializer(
                        existing_config, 
                        data=config_data, 
                        partial=True
                    )
                    if serializer.is_valid():
                        updated_config = serializer.save()
                        updated_configs.append(serializer.data)
                    else:
                        errors.append({
                            'event_type': event_type,
                            'errors': serializer.errors
                        })
                else:
                    # Crear nuevo
                    serializer = TenantCommunicationConfigSerializer(data=config_data)
                    if serializer.is_valid():
                        created_config = serializer.save()
                        created_configs.append(serializer.data)
                    else:
                        errors.append({
                            'event_type': event_type,
                            'errors': serializer.errors
                        })
            
            response_data = {
                'tenant_id': str(tenant_id),
                'tenant_name': tenant.name,
                'created_count': len(created_configs),
                'updated_count': len(updated_configs),
                'error_count': len(errors),
                'created_configurations': created_configs,
                'updated_configurations': updated_configs,
                'errors': errors
            }
            
            if errors:
                logger.warning(f"Configuración masiva con errores para {tenant.name}: {len(errors)} errores")
                return Response(response_data, status=status.HTTP_207_MULTI_STATUS)
            else:
                logger.info(f"Configuración masiva exitosa para {tenant.name}")
                return Response(response_data, status=status.HTTP_201_CREATED)
                
    except Exception as e:
        logger.error(f"Error en configuración masiva: {str(e)}")
        return Response(
            {'error': 'Error interno del servidor'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET', 'PUT'])
@authentication_classes([TenantJWTAuthentication])
@permission_classes([IsAuthenticated])
def tenant_ai_config(request, tenant_id):
    """
    GET: Obtener configuración de IA del tenant
    PUT: Actualizar configuración de IA del tenant
    """
    tenant = get_object_or_404(TenantConfig, tenant_id=tenant_id)
    
    if request.method == 'GET':
        try:
            ai_config = TenantAIConfig.objects.get(tenant=tenant)
            serializer = TenantAIConfigSerializer(ai_config)
            return Response(serializer.data)
        except TenantAIConfig.DoesNotExist:
            # Crear configuración por defecto
            ai_config = TenantAIConfig.objects.create(tenant=tenant)
            serializer = TenantAIConfigSerializer(ai_config)
            return Response(serializer.data)
    
    elif request.method == 'PUT':
        try:
            ai_config = TenantAIConfig.objects.get(tenant=tenant)
        except TenantAIConfig.DoesNotExist:
            ai_config = TenantAIConfig(tenant=tenant)
        
        serializer = TenantAIConfigSerializer(ai_config, data=request.data, partial=True)
        if serializer.is_valid():
            try:
                updated_config = serializer.save()
                logger.info(f"Configuración de IA actualizada para {tenant.name}")
                return Response(serializer.data)
            except Exception as e:
                logger.error(f"Error actualizando configuración de IA: {str(e)}")
                return Response(
                    {'error': 'Error interno del servidor'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@authentication_classes([TenantJWTAuthentication])
@permission_classes([IsAuthenticated])
def tenant_config_summary(request, tenant_id):
    """
    Resumen completo de la configuración del tenant
    """
    tenant = get_object_or_404(TenantConfig, tenant_id=tenant_id)
    
    # Configuraciones de comunicación
    comm_configs = TenantCommunicationConfig.objects.filter(tenant=tenant)
    
    # Configuración de IA
    try:
        ai_config = TenantAIConfig.objects.get(tenant=tenant)
    except TenantAIConfig.DoesNotExist:
        ai_config = None
    
    # Estadísticas
    total_events = len(TenantCommunicationConfig.EVENT_CHOICES)
    configured_events = comm_configs.count()
    completion_percentage = (configured_events / total_events) * 100 if total_events > 0 else 0
    
    # Resumen por canal
    channel_summary = {}
    for config in comm_configs:
        channel = config.channel_preference
        if channel not in channel_summary:
            channel_summary[channel] = 0
        channel_summary[channel] += 1
    
    response_data = {
        'tenant_info': {
            'id': str(tenant.tenant_id),
            'name': tenant.name,
            'domain': tenant.domain,
            'is_active': tenant.is_active,
            'verification_status': tenant.verification_status
        },
        'configuration_summary': {
            'total_event_types': total_events,
            'configured_events': configured_events,
            'completion_percentage': round(completion_percentage, 2),
            'channel_distribution': channel_summary
        },
        'ai_configuration': {
            'enabled': ai_config is not None and ai_config.can_use_ai() if ai_config else False,
            'provider': ai_config.ai_provider if ai_config else 'not_configured',
            'personalization_enabled': ai_config.use_ai_personalization if ai_config else False
        } if ai_config else None,
        'communication_configs': TenantCommunicationConfigSerializer(comm_configs, many=True).data,
        'ai_config': TenantAIConfigSerializer(ai_config).data if ai_config else None
    }
    
    return Response(response_data)


@api_view(['POST'])
@authentication_classes([TenantJWTAuthentication])
@permission_classes([IsAuthenticated])
def tenant_default_setup(request, tenant_id):
    """
    Configurar un tenant con valores por defecto para todos los eventos
    Útil para onboarding rápido
    """
    tenant = get_object_or_404(TenantConfig, tenant_id=tenant_id)
    
    # Configuración por defecto
    default_channel = request.data.get('default_channel', 'both_whatsapp_primary')
    default_priority = request.data.get('default_priority', 'normal')
    use_ai = request.data.get('use_ai', True)
    
    try:
        with transaction.atomic():
            created_count = 0
            
            # Crear configuraciones para todos los eventos
            for event_key, event_label in TenantCommunicationConfig.EVENT_CHOICES:
                config, created = TenantCommunicationConfig.objects.get_or_create(
                    tenant=tenant,
                    event_type=event_key,
                    defaults={
                        'channel_preference': default_channel,
                        'priority': default_priority,
                        'use_ai_personalization': use_ai,
                        'send_immediately': True,
                        'respect_business_hours': False,
                        'max_retries': 3,
                        'is_active': True
                    }
                )
                if created:
                    created_count += 1
            
            # Crear configuración de IA por defecto
            ai_config, ai_created = TenantAIConfig.objects.get_or_create(
                tenant=tenant,
                defaults={
                    'ai_provider': 'openai',
                    'default_tone': 'friendly',
                    'max_tokens': 150,
                    'temperature': 0.7,
                    'include_customer_history': True,
                    'include_product_info': True,
                    'daily_ai_limit': 1000,
                    'require_human_approval': False,
                    'is_active': True
                }
            )
            
            logger.info(f"Configuración por defecto creada para {tenant.name}: {created_count} eventos")
            
            return Response({
                'tenant_id': str(tenant_id),
                'tenant_name': tenant.name,
                'created_configurations': created_count,
                'ai_config_created': ai_created,
                'message': f'Configuración por defecto aplicada exitosamente. Se configuraron {created_count} eventos.'
            }, status=status.HTTP_201_CREATED)
            
    except Exception as e:
        logger.error(f"Error creando configuración por defecto: {str(e)}")
        return Response(
            {'error': 'Error interno del servidor'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
