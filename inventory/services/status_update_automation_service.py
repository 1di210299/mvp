"""
Status Update Automation Service
Automatiza cambios de estado basados en emails y análisis de PDFs
"""
import json
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict

from django.conf import settings
from django.utils import timezone
from django.db import transaction
from django.core.cache import cache

from inventory.services.pdf_analysis_service import get_pdf_analysis_service, PDFAnalysisResult
from inventory.services.email_tracking_service import get_email_tracking_service
from inventory.models import TrackedEmail, EmailPattern, EmailInsight

logger = logging.getLogger(__name__)

@dataclass
class StatusUpdateRule:
    """Regla para automatización de actualizaciones de estado"""
    name: str
    trigger_type: str  # 'email_pattern', 'pdf_analysis', 'keyword_match'
    conditions: Dict[str, Any]
    actions: List[Dict[str, Any]]
    priority: int  # 1 = alta, 2 = media, 3 = baja
    is_active: bool = True

@dataclass
class StatusUpdateLog:
    """Log de cambios de estado automáticos"""
    rule_name: str
    trigger_data: Dict[str, Any]
    action_taken: str
    success: bool
    error_message: Optional[str] = None
    timestamp: datetime = None
    metadata: Dict[str, Any] = None

class StatusUpdateAutomationService:
    """
    Servicio principal para automatización de actualizaciones de estado
    """
    
    def __init__(self):
        """Inicializar el servicio"""
        self.pdf_service = get_pdf_analysis_service()
        self.email_service = get_email_tracking_service()
        
        # Reglas predefinidas para automatización
        self.predefined_rules = self._load_predefined_rules()
        
        # Cache para logs recientes
        self.log_cache_key = "status_update_logs"
    
    def _load_predefined_rules(self) -> List[StatusUpdateRule]:
        """Cargar reglas predefinidas de automatización"""
        rules = [
            # Regla 1: Factura recibida
            StatusUpdateRule(
                name="invoice_received",
                trigger_type="pdf_analysis",
                conditions={
                    "document_type": "invoice",
                    "confidence_threshold": 0.7,
                    "has_invoice_number": True
                },
                actions=[
                    {
                        "type": "update_purchase_order_status",
                        "status": "invoiced",
                        "add_note": "Factura recibida automáticamente via email"
                    },
                    {
                        "type": "create_alert",
                        "alert_type": "invoice_received",
                        "severity": "medium",
                        "message": "Nueva factura procesada automáticamente"
                    }
                ],
                priority=1
            ),
            
            # Regla 2: Confirmación de envío
            StatusUpdateRule(
                name="shipping_confirmation",
                trigger_type="pdf_analysis",
                conditions={
                    "document_type": "shipping_confirmation",
                    "confidence_threshold": 0.7,
                    "has_tracking_number": True
                },
                actions=[
                    {
                        "type": "update_purchase_order_status",
                        "status": "shipped",
                        "add_note": "Envío confirmado automáticamente"
                    },
                    {
                        "type": "create_tracking_record",
                        "source": "email_automation"
                    }
                ],
                priority=1
            ),
            
            # Regla 3: Email de confirmación de orden
            StatusUpdateRule(
                name="order_confirmation_email",
                trigger_type="email_pattern",
                conditions={
                    "subject_keywords": ["confirmed", "confirmado", "orden aprobada"],
                    "sender_domain_whitelist": ["proveedor.com", "supplier.com"],
                    "confidence_threshold": 0.6
                },
                actions=[
                    {
                        "type": "update_purchase_order_status",
                        "status": "confirmed",
                        "add_note": "Orden confirmada via email automático"
                    }
                ],
                priority=2
            ),
            
            # Regla 4: Email de cancelación
            StatusUpdateRule(
                name="order_cancellation_email",
                trigger_type="email_pattern",
                conditions={
                    "subject_keywords": ["cancelled", "cancelado", "orden cancelada"],
                    "content_keywords": ["unable to fulfill", "no podemos procesar"],
                    "confidence_threshold": 0.8
                },
                actions=[
                    {
                        "type": "update_purchase_order_status",
                        "status": "cancelled",
                        "add_note": "Orden cancelada automáticamente por email del proveedor"
                    },
                    {
                        "type": "create_alert",
                        "alert_type": "order_cancelled",
                        "severity": "high",
                        "message": "Orden cancelada por proveedor - revisar inmediatamente"
                    }
                ],
                priority=1
            ),
            
            # Regla 5: Delay notification
            StatusUpdateRule(
                name="delivery_delay_notification",
                trigger_type="email_pattern",
                conditions={
                    "subject_keywords": ["delay", "retraso", "postponed"],
                    "content_keywords": ["delayed", "retrasado", "nueva fecha"],
                    "confidence_threshold": 0.7
                },
                actions=[
                    {
                        "type": "update_delivery_date",
                        "extend_days": 7,  # Por defecto extender 7 días
                        "add_note": "Retraso reportado automáticamente por proveedor"
                    },
                    {
                        "type": "create_alert",
                        "alert_type": "delivery_delay",
                        "severity": "medium",
                        "message": "Retraso en entrega reportado por proveedor"
                    }
                ],
                priority=2
            )
        ]
        
        return rules
    
    def process_email_for_status_updates(self, tracked_email_id: str) -> List[StatusUpdateLog]:
        """
        Procesar un email para detectar actualizaciones de estado automáticas
        
        Args:
            tracked_email_id: ID del email tracked
        
        Returns:
            Lista de logs de actualizaciones realizadas
        """
        logs = []
        
        try:
            # Obtener email tracked
            try:
                from inventory.models import TrackedEmail
                tracked_email = TrackedEmail.objects.get(tracking_id=tracked_email_id)
            except TrackedEmail.DoesNotExist:
                logger.warning(f"TrackedEmail no encontrado: {tracked_email_id}")
                return logs
            
            # Preparar datos del email para análisis
            email_data = {
                'subject': tracked_email.subject,
                'content': tracked_email.content_preview,
                'sender': tracked_email.recipient_email,  # En este contexto, el "recipient" es quien nos envía
                'received_at': tracked_email.created_at,
                'tracking_id': tracked_email.tracking_id
            }
            
            # Aplicar reglas de automatización
            for rule in self.predefined_rules:
                if not rule.is_active:
                    continue
                
                # Verificar si la regla aplica al email
                if self._rule_matches_email(rule, email_data):
                    # Ejecutar acciones de la regla
                    rule_logs = self._execute_rule_actions(rule, email_data, tracked_email)
                    logs.extend(rule_logs)
            
            # Análisis de patrones con IA si está disponible
            if hasattr(self.email_service, 'analyze_email_patterns'):
                pattern_logs = self._analyze_email_patterns(email_data, tracked_email)
                logs.extend(pattern_logs)
            
            # Guardar logs en cache y base de datos
            self._save_logs(logs)
            
        except Exception as e:
            logger.error(f"Error procesando email para status updates: {e}")
            logs.append(StatusUpdateLog(
                rule_name="error",
                trigger_data={"error": str(e)},
                action_taken="none",
                success=False,
                error_message=str(e),
                timestamp=timezone.now()
            ))
        
        return logs
    
    def process_pdf_attachment_for_status_updates(self, pdf_path: str, email_context: Dict[str, Any]) -> List[StatusUpdateLog]:
        """
        Procesar adjunto PDF para detectar actualizaciones de estado
        
        Args:
            pdf_path: Ruta al archivo PDF
            email_context: Contexto del email que contenía el PDF
        
        Returns:
            Lista de logs de actualizaciones realizadas
        """
        logs = []
        
        try:
            # Analizar PDF
            pdf_result = self.pdf_service.analyze_pdf(pdf_path, email_context)
            
            if pdf_result.confidence < 0.5:
                logger.info(f"PDF analysis confidence too low: {pdf_result.confidence}")
                return logs
            
            # Aplicar reglas basadas en análisis de PDF
            for rule in self.predefined_rules:
                if not rule.is_active or rule.trigger_type != "pdf_analysis":
                    continue
                
                if self._rule_matches_pdf(rule, pdf_result):
                    # Ejecutar acciones de la regla
                    rule_logs = self._execute_pdf_rule_actions(rule, pdf_result, email_context)
                    logs.extend(rule_logs)
            
            # Procesar status updates sugeridos por el análisis de PDF
            for update in pdf_result.status_updates:
                update_log = self._execute_suggested_status_update(update, pdf_result, email_context)
                if update_log:
                    logs.append(update_log)
            
            # Guardar logs
            self._save_logs(logs)
            
        except Exception as e:
            logger.error(f"Error procesando PDF para status updates: {e}")
            logs.append(StatusUpdateLog(
                rule_name="pdf_analysis_error",
                trigger_data={"pdf_path": pdf_path, "error": str(e)},
                action_taken="none",
                success=False,
                error_message=str(e),
                timestamp=timezone.now()
            ))
        
        return logs
    
    def _rule_matches_email(self, rule: StatusUpdateRule, email_data: Dict[str, Any]) -> bool:
        """Verificar si una regla aplica a un email específico"""
        if rule.trigger_type != "email_pattern":
            return False
        
        conditions = rule.conditions
        
        # Verificar palabras clave en el asunto
        if 'subject_keywords' in conditions:
            subject = email_data.get('subject', '').lower()
            keywords = conditions['subject_keywords']
            if not any(keyword.lower() in subject for keyword in keywords):
                return False
        
        # Verificar palabras clave en el contenido
        if 'content_keywords' in conditions:
            content = email_data.get('content', '').lower()
            keywords = conditions['content_keywords']
            if not any(keyword.lower() in content for keyword in keywords):
                return False
        
        # Verificar dominio del remitente
        if 'sender_domain_whitelist' in conditions:
            sender = email_data.get('sender', '')
            domains = conditions['sender_domain_whitelist']
            sender_domain = sender.split('@')[-1] if '@' in sender else ''
            if sender_domain not in domains:
                return False
        
        return True
    
    def _rule_matches_pdf(self, rule: StatusUpdateRule, pdf_result: PDFAnalysisResult) -> bool:
        """Verificar si una regla aplica a un resultado de análisis PDF"""
        if rule.trigger_type != "pdf_analysis":
            return False
        
        conditions = rule.conditions
        
        # Verificar tipo de documento
        if 'document_type' in conditions:
            if pdf_result.document_type != conditions['document_type']:
                return False
        
        # Verificar umbral de confianza
        if 'confidence_threshold' in conditions:
            if pdf_result.confidence < conditions['confidence_threshold']:
                return False
        
        # Verificar presencia de datos específicos
        if 'has_invoice_number' in conditions and conditions['has_invoice_number']:
            if not pdf_result.extracted_data.get('invoice_number'):
                return False
        
        if 'has_tracking_number' in conditions and conditions['has_tracking_number']:
            if not pdf_result.extracted_data.get('tracking_number'):
                return False
        
        return True
    
    def _execute_rule_actions(self, rule: StatusUpdateRule, email_data: Dict[str, Any], tracked_email) -> List[StatusUpdateLog]:
        """Ejecutar acciones de una regla específica"""
        logs = []
        
        for action in rule.actions:
            try:
                log = self._execute_single_action(action, email_data, rule.name, tracked_email)
                if log:
                    logs.append(log)
            except Exception as e:
                logger.error(f"Error ejecutando acción {action}: {e}")
                logs.append(StatusUpdateLog(
                    rule_name=rule.name,
                    trigger_data=email_data,
                    action_taken=action.get('type', 'unknown'),
                    success=False,
                    error_message=str(e),
                    timestamp=timezone.now()
                ))
        
        return logs
    
    def _execute_pdf_rule_actions(self, rule: StatusUpdateRule, pdf_result: PDFAnalysisResult, email_context: Dict[str, Any]) -> List[StatusUpdateLog]:
        """Ejecutar acciones basadas en análisis de PDF"""
        logs = []
        
        for action in rule.actions:
            try:
                log = self._execute_pdf_action(action, pdf_result, rule.name, email_context)
                if log:
                    logs.append(log)
            except Exception as e:
                logger.error(f"Error ejecutando acción PDF {action}: {e}")
                logs.append(StatusUpdateLog(
                    rule_name=rule.name,
                    trigger_data=asdict(pdf_result),
                    action_taken=action.get('type', 'unknown'),
                    success=False,
                    error_message=str(e),
                    timestamp=timezone.now()
                ))
        
        return logs
    
    def _execute_single_action(self, action: Dict[str, Any], email_data: Dict[str, Any], rule_name: str, tracked_email) -> Optional[StatusUpdateLog]:
        """Ejecutar una acción individual"""
        action_type = action.get('type')
        
        if action_type == 'update_purchase_order_status':
            return self._update_purchase_order_status(action, email_data, rule_name)
        elif action_type == 'create_alert':
            return self._create_alert(action, email_data, rule_name)
        elif action_type == 'create_tracking_record':
            return self._create_tracking_record(action, email_data, rule_name)
        elif action_type == 'update_delivery_date':
            return self._update_delivery_date(action, email_data, rule_name)
        else:
            logger.warning(f"Tipo de acción desconocido: {action_type}")
            return None
    
    def _execute_pdf_action(self, action: Dict[str, Any], pdf_result: PDFAnalysisResult, rule_name: str, email_context: Dict[str, Any]) -> Optional[StatusUpdateLog]:
        """Ejecutar una acción basada en análisis de PDF"""
        action_type = action.get('type')
        
        # Preparar datos combinados
        combined_data = {
            **pdf_result.extracted_data,
            **email_context,
            'document_type': pdf_result.document_type,
            'confidence': pdf_result.confidence
        }
        
        if action_type == 'update_purchase_order_status':
            return self._update_purchase_order_status(action, combined_data, rule_name)
        elif action_type == 'create_alert':
            return self._create_alert(action, combined_data, rule_name)
        elif action_type == 'create_tracking_record':
            return self._create_tracking_record(action, combined_data, rule_name)
        else:
            logger.warning(f"Tipo de acción PDF desconocido: {action_type}")
            return None
    
    def _execute_suggested_status_update(self, update: Dict[str, Any], pdf_result: PDFAnalysisResult, email_context: Dict[str, Any]) -> Optional[StatusUpdateLog]:
        """Ejecutar una actualización de estado sugerida por el análisis de PDF"""
        try:
            action_type = update.get('action')
            
            if action_type == 'update_purchase_order_status':
                # Simular ejecución de actualización de estado
                # En implementación real, aquí se actualizaría la base de datos
                
                return StatusUpdateLog(
                    rule_name="pdf_suggested_update",
                    trigger_data={
                        'pdf_analysis': asdict(pdf_result),
                        'email_context': email_context,
                        'suggested_update': update
                    },
                    action_taken=f"Update PO {update.get('purchase_order_id')} to {update.get('new_status')}",
                    success=True,
                    timestamp=timezone.now(),
                    metadata=update.get('data', {})
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error ejecutando update sugerido: {e}")
            return StatusUpdateLog(
                rule_name="pdf_suggested_update_error",
                trigger_data=update,
                action_taken="none",
                success=False,
                error_message=str(e),
                timestamp=timezone.now()
            )
    
    def _update_purchase_order_status(self, action: Dict[str, Any], data: Dict[str, Any], rule_name: str) -> StatusUpdateLog:
        """Actualizar estado de orden de compra"""
        # En una implementación real, aquí se actualizaría la base de datos
        # Por ahora, registramos la acción que se tomaría
        
        new_status = action.get('status')
        note = action.get('add_note', '')
        
        return StatusUpdateLog(
            rule_name=rule_name,
            trigger_data=data,
            action_taken=f"Update purchase order status to '{new_status}'",
            success=True,
            timestamp=timezone.now(),
            metadata={
                'new_status': new_status,
                'note': note,
                'data_used': data
            }
        )
    
    def _create_alert(self, action: Dict[str, Any], data: Dict[str, Any], rule_name: str) -> StatusUpdateLog:
        """Crear una alerta"""
        alert_type = action.get('alert_type')
        severity = action.get('severity', 'medium')
        message = action.get('message', '')
        
        return StatusUpdateLog(
            rule_name=rule_name,
            trigger_data=data,
            action_taken=f"Create alert: {alert_type} ({severity})",
            success=True,
            timestamp=timezone.now(),
            metadata={
                'alert_type': alert_type,
                'severity': severity,
                'message': message
            }
        )
    
    def _create_tracking_record(self, action: Dict[str, Any], data: Dict[str, Any], rule_name: str) -> StatusUpdateLog:
        """Crear registro de tracking"""
        source = action.get('source', 'email_automation')
        
        return StatusUpdateLog(
            rule_name=rule_name,
            trigger_data=data,
            action_taken=f"Create tracking record from {source}",
            success=True,
            timestamp=timezone.now(),
            metadata={
                'source': source,
                'tracking_data': data.get('tracking_number')
            }
        )
    
    def _update_delivery_date(self, action: Dict[str, Any], data: Dict[str, Any], rule_name: str) -> StatusUpdateLog:
        """Actualizar fecha de entrega"""
        extend_days = action.get('extend_days', 0)
        note = action.get('add_note', '')
        
        return StatusUpdateLog(
            rule_name=rule_name,
            trigger_data=data,
            action_taken=f"Extend delivery date by {extend_days} days",
            success=True,
            timestamp=timezone.now(),
            metadata={
                'days_extended': extend_days,
                'note': note
            }
        )
    
    def _analyze_email_patterns(self, email_data: Dict[str, Any], tracked_email) -> List[StatusUpdateLog]:
        """Análisis de patrones de email con IA"""
        logs = []
        
        try:
            # Aquí se podría integrar análisis más avanzado con IA
            # Por ahora, implementamos lógica básica de patrones
            
            subject = email_data.get('subject', '').lower()
            content = email_data.get('content', '').lower()
            
            # Patrones comunes de estado
            status_patterns = {
                'confirmed': ['confirmed', 'confirmado', 'aprobado', 'orden aceptada'],
                'shipped': ['shipped', 'enviado', 'despachado', 'en transito'],
                'delivered': ['delivered', 'entregado', 'recibido'],
                'cancelled': ['cancelled', 'cancelado', 'rechazado'],
                'delayed': ['delayed', 'retraso', 'retrasado', 'postponed']
            }
            
            for status, keywords in status_patterns.items():
                if any(keyword in subject or keyword in content for keyword in keywords):
                    logs.append(StatusUpdateLog(
                        rule_name="pattern_detection",
                        trigger_data=email_data,
                        action_taken=f"Detected status pattern: {status}",
                        success=True,
                        timestamp=timezone.now(),
                        metadata={
                            'detected_status': status,
                            'keywords_matched': [kw for kw in keywords if kw in subject or kw in content]
                        }
                    ))
                    break
            
        except Exception as e:
            logger.error(f"Error en análisis de patrones: {e}")
        
        return logs
    
    def _save_logs(self, logs: List[StatusUpdateLog]):
        """Guardar logs en cache y opcionalmente en base de datos"""
        if not logs:
            return
        
        try:
            # Guardar en cache para acceso rápido
            cached_logs = cache.get(self.log_cache_key, [])
            
            # Convertir logs a diccionarios para serialización
            log_dicts = []
            for log in logs:
                log_dict = asdict(log)
                if log_dict['timestamp']:
                    log_dict['timestamp'] = log_dict['timestamp'].isoformat()
                log_dicts.append(log_dict)
            
            cached_logs.extend(log_dicts)
            
            # Mantener solo los últimos 100 logs en cache
            if len(cached_logs) > 100:
                cached_logs = cached_logs[-100:]
            
            cache.set(self.log_cache_key, cached_logs, timeout=86400)  # 24 horas
            
            logger.info(f"Guardados {len(logs)} logs de automatización")
            
        except Exception as e:
            logger.error(f"Error guardando logs: {e}")
    
    def get_recent_logs(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Obtener logs recientes de automatización"""
        try:
            cached_logs = cache.get(self.log_cache_key, [])
            return cached_logs[-limit:] if cached_logs else []
        except Exception as e:
            logger.error(f"Error obteniendo logs: {e}")
            return []
    
    def get_automation_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de automatización"""
        try:
            logs = cache.get(self.log_cache_key, [])
            
            if not logs:
                return {
                    'total_automations': 0,
                    'success_rate': 0,
                    'top_rules': [],
                    'recent_activity': []
                }
            
            total = len(logs)
            successful = sum(1 for log in logs if log.get('success', False))
            success_rate = (successful / total * 100) if total > 0 else 0
            
            # Contar reglas más usadas
            rule_counts = {}
            for log in logs:
                rule = log.get('rule_name', 'unknown')
                rule_counts[rule] = rule_counts.get(rule, 0) + 1
            
            top_rules = sorted(rule_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            
            return {
                'total_automations': total,
                'success_rate': round(success_rate, 1),
                'successful_automations': successful,
                'failed_automations': total - successful,
                'top_rules': [{'rule': rule, 'count': count} for rule, count in top_rules],
                'recent_activity': logs[-10:] if logs else []
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {
                'total_automations': 0,
                'success_rate': 0,
                'error': str(e)
            }


# ==============================================
# FUNCIONES DE UTILIDAD GLOBAL
# ==============================================

def get_status_update_service() -> StatusUpdateAutomationService:
    """Obtener instancia del servicio de automatización"""
    return StatusUpdateAutomationService()

def process_email_for_automation(tracked_email_id: str) -> List[StatusUpdateLog]:
    """Función de utilidad para procesar email para automatización"""
    service = get_status_update_service()
    return service.process_email_for_status_updates(tracked_email_id)

def process_pdf_for_automation(pdf_path: str, email_context: Dict[str, Any]) -> List[StatusUpdateLog]:
    """Función de utilidad para procesar PDF para automatización"""
    service = get_status_update_service()
    return service.process_pdf_attachment_for_status_updates(pdf_path, email_context)
