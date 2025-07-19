"""
EmailTrackingService - Servicio completo para seguimiento y análisis de emails
Integra Gmail API, webhooks, análisis de patrones y OpenAI para insights de email
"""
import base64
import json
import logging
import os
import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from django.db.models import Count, Avg, Q
from django.core.mail import send_mail

# Gmail API (requiere: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib)
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    GMAIL_API_AVAILABLE = True
except ImportError:
    GMAIL_API_AVAILABLE = False

# OpenAI para análisis de contenido
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from alerts.models import Alert
from authentication.models import Company

logger = logging.getLogger(__name__)

# Scopes necesarios para Gmail API
GMAIL_SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify'
]

@dataclass
class EmailPattern:
    """Estructura para patrones de email detectados"""
    pattern_type: str
    frequency: int
    confidence: float
    description: str
    examples: List[str]
    recommendation: str

@dataclass
class EmailInsight:
    """Estructura para insights de email generados por IA"""
    insight_type: str
    priority: str  # 'high', 'medium', 'low'
    title: str
    description: str
    action_items: List[str]
    confidence_score: float

@dataclass
class EmailTracking:
    """Estructura para tracking de emails enviados"""
    email_id: str
    recipient: str
    subject: str
    sent_at: datetime
    opened_at: Optional[datetime]
    clicked_at: Optional[datetime]
    replied_at: Optional[datetime]
    status: str  # 'sent', 'delivered', 'opened', 'clicked', 'replied', 'bounced'
    tracking_data: Dict[str, Any]


class EmailTrackingService:
    """
    Servicio principal para tracking y análisis de emails
    """
    
    def __init__(self, company_id: int = None):
        """Inicializar el servicio"""
        self.company_id = company_id
        self.gmail_service = None
        self.openai_client = None
        
        # Inicializar OpenAI si está disponible
        if OPENAI_AVAILABLE:
            api_key = getattr(settings, 'OPENAI_API_KEY', None)
            if api_key:
                try:
                    self.openai_client = OpenAI(api_key=api_key)
                    logger.info("OpenAI client inicializado para EmailTrackingService")
                except Exception as e:
                    logger.warning(f"No se pudo inicializar OpenAI: {e}")
        
        # Cache keys
        self.cache_prefix = f"email_tracking_{company_id}_" if company_id else "email_tracking_"
    
    def setup_gmail_api(self, credentials_path: str = None, token_path: str = None) -> bool:
        """
        Configurar la conexión con Gmail API
        
        Args:
            credentials_path: Ruta al archivo credentials.json
            token_path: Ruta al archivo token.json
        """
        if not GMAIL_API_AVAILABLE:
            logger.error("Gmail API no está disponible. Instalar: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
            return False
        
        try:
            creds = None
            token_file = token_path or getattr(settings, 'GMAIL_TOKEN_PATH', 'token.json')
            
            # Cargar token existente
            if os.path.exists(token_file):
                creds = Credentials.from_authorized_user_file(token_file, GMAIL_SCOPES)
            
            # Si no hay credenciales válidas, obtener nuevas
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    credentials_file = credentials_path or getattr(settings, 'GMAIL_CREDENTIALS_PATH', 'credentials.json')
                    if not os.path.exists(credentials_file):
                        logger.error(f"Archivo de credenciales no encontrado: {credentials_file}")
                        return False
                    
                    flow = InstalledAppFlow.from_client_secrets_file(credentials_file, GMAIL_SCOPES)
                    creds = flow.run_local_server(port=0)
                
                # Guardar credenciales para la próxima ejecución
                with open(token_file, 'w') as token:
                    token.write(creds.to_json())
            
            # Crear servicio Gmail
            self.gmail_service = build('gmail', 'v1', credentials=creds)
            logger.info("Gmail API configurada exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"Error configurando Gmail API: {e}")
            return False
    
    def send_tracked_email(self, to: str, subject: str, body: str, 
                          html_body: str = None, track_opens: bool = True, 
                          track_clicks: bool = True) -> Dict[str, Any]:
        """
        Enviar email con tracking
        
        Args:
            to: Destinatario
            subject: Asunto
            body: Cuerpo del email (texto)
            html_body: Cuerpo HTML (opcional)
            track_opens: Activar tracking de aperturas
            track_clicks: Activar tracking de clicks
        """
        try:
            # Generar ID único para tracking
            tracking_id = f"track_{int(time.time())}_{hash(to + subject) % 10000}"
            
            # Preparar contenido con tracking
            if track_opens:
                pixel_url = f"{settings.FRONTEND_URL}/api/email-tracking/open/{tracking_id}/"
                tracking_pixel = f'<img src="{pixel_url}" width="1" height="1" style="display:none;" />'
                
                if html_body:
                    html_body += tracking_pixel
                else:
                    html_body = f"<html><body>{body.replace(chr(10), '<br>')}{tracking_pixel}</body></html>"
            
            if track_clicks and html_body:
                html_body = self._add_click_tracking(html_body, tracking_id)
            
            # Crear mensaje
            msg = MIMEMultipart('alternative') if html_body else MIMEText(body)
            msg['to'] = to
            msg['subject'] = subject
            msg['from'] = settings.DEFAULT_FROM_EMAIL
            
            if html_body:
                msg.attach(MIMEText(body, 'plain'))
                msg.attach(MIMEText(html_body, 'html'))
            
            # Enviar email
            if self.gmail_service:
                # Usar Gmail API
                raw_message = {'raw': base64.urlsafe_b64encode(msg.as_bytes()).decode()}
                result = self.gmail_service.users().messages().send(
                    userId='me', body=raw_message
                ).execute()
                
                email_id = result['id']
            else:
                # Usar Django email backend como fallback
                send_mail(
                    subject=subject,
                    message=body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[to],
                    html_message=html_body,
                    fail_silently=False
                )
                email_id = tracking_id
            
            # Guardar tracking info en cache
            tracking_data = EmailTracking(
                email_id=email_id,
                recipient=to,
                subject=subject,
                sent_at=timezone.now(),
                opened_at=None,
                clicked_at=None,
                replied_at=None,
                status='sent',
                tracking_data={
                    'tracking_id': tracking_id,
                    'track_opens': track_opens,
                    'track_clicks': track_clicks
                }
            )
            
            # Cachear tracking data
            self._cache_tracking_data(tracking_id, tracking_data)
            
            # ✅ NUEVO: También guardar en base de datos usando TrackedEmail
            try:
                from inventory.models import TrackedEmail
                
                TrackedEmail.objects.create(
                    email_id=email_id,
                    tracking_id=tracking_id,
                    recipient_email=to,
                    subject=subject,
                    content_preview=body[:200] + "..." if len(body) > 200 else body,
                    status='sent',
                    sent_at=timezone.now(),
                    company_id=self.company_id or 1  # Usar company_id del servicio o default
                )
                logger.info(f"📧 TrackedEmail guardado en BD: {tracking_id}")
                
            except Exception as e:
                logger.warning(f"⚠️  No se pudo guardar TrackedEmail en BD: {e}")
            
            logger.info(f"Email enviado con tracking: {email_id} -> {to}")
            
            return {
                'success': True,
                'email_id': email_id,
                'tracking_id': tracking_id,
                'message': 'Email enviado exitosamente'
            }
            
        except Exception as e:
            logger.error(f"Error enviando email tracked: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def track_email_open(self, tracking_id: str, user_agent: str = None, 
                        ip_address: str = None) -> bool:
        """
        Registrar apertura de email
        """
        try:
            tracking_data = self._get_tracking_data(tracking_id)
            if tracking_data and not tracking_data.opened_at:
                tracking_data.opened_at = timezone.now()
                tracking_data.status = 'opened'
                tracking_data.tracking_data.update({
                    'user_agent': user_agent,
                    'ip_address': ip_address,
                    'opened_at': tracking_data.opened_at.isoformat()
                })
                
                self._cache_tracking_data(tracking_id, tracking_data)
                logger.info(f"Email abierto: {tracking_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error tracking email open: {e}")
        
        return False
    
    def track_email_click(self, tracking_id: str, link_url: str, 
                         user_agent: str = None, ip_address: str = None) -> bool:
        """
        Registrar click en email
        """
        try:
            tracking_data = self._get_tracking_data(tracking_id)
            if tracking_data:
                if not tracking_data.clicked_at:
                    tracking_data.clicked_at = timezone.now()
                    tracking_data.status = 'clicked'
                
                # Agregar click data
                clicks = tracking_data.tracking_data.get('clicks', [])
                clicks.append({
                    'url': link_url,
                    'clicked_at': timezone.now().isoformat(),
                    'user_agent': user_agent,
                    'ip_address': ip_address
                })
                tracking_data.tracking_data['clicks'] = clicks
                
                self._cache_tracking_data(tracking_id, tracking_data)
                logger.info(f"Email click: {tracking_id} -> {link_url}")
                return True
                
        except Exception as e:
            logger.error(f"Error tracking email click: {e}")
        
        return False
    
    def setup_gmail_webhook(self, webhook_url: str, topics: List[str] = None) -> Dict[str, Any]:
        """
        Configurar webhook para recibir notificaciones de Gmail
        
        Args:
            webhook_url: URL donde recibir las notificaciones
            topics: Lista de temas a monitorear ['INBOX', 'SENT', etc.]
        """
        if not self.gmail_service:
            return {'success': False, 'error': 'Gmail API no configurada'}
        
        try:
            topics = topics or ['INBOX']
            
            # Configurar Cloud Pub/Sub topic (requiere configuración previa en Google Cloud)
            request = {
                'labelIds': topics,
                'topicName': getattr(settings, 'GMAIL_PUBSUB_TOPIC', f'projects/{settings.GOOGLE_CLOUD_PROJECT}/topics/gmail-webhook')
            }
            
            result = self.gmail_service.users().watch(userId='me', body=request).execute()
            
            # Cachear configuración del webhook
            webhook_config = {
                'webhook_url': webhook_url,
                'topics': topics,
                'history_id': result.get('historyId'),
                'expiration': result.get('expiration'),
                'configured_at': timezone.now().isoformat()
            }
            
            cache.set(f"{self.cache_prefix}webhook_config", webhook_config, timeout=3600*24*7)  # 7 días
            
            logger.info("Gmail webhook configurado exitosamente")
            return {
                'success': True,
                'history_id': result.get('historyId'),
                'expiration': result.get('expiration')
            }
            
        except Exception as e:
            logger.error(f"Error configurando Gmail webhook: {e}")
            return {'success': False, 'error': str(e)}
    
    def process_gmail_webhook_notification(self, notification_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesar notificación de webhook de Gmail desde Pub/Sub
        
        Args:
            notification_data: Datos de la notificación de Gmail
        """
        try:
            email_address = notification_data.get('emailAddress')
            history_id = notification_data.get('historyId')
            
            if not email_address or not history_id:
                return {'success': False, 'error': 'Datos de notificación inválidos'}
            
            logger.info(f"📧 Procesando notificación Gmail - Email: {email_address}, History: {history_id}")
            
            # Obtener cambios desde el último history_id conocido
            webhook_config = cache.get(f"{self.cache_prefix}webhook_config", {})
            last_history_id = webhook_config.get('history_id')
            
            processed_changes = []
            
            if last_history_id and self.gmail_service:
                # Obtener historial de cambios desde Gmail
                changes = self._get_gmail_history(last_history_id, history_id)
                
                for change in changes:
                    result = self._process_gmail_change(change)
                    if result:
                        processed_changes.append(result)
                        
                        # Si hay mensajes nuevos, verificar si son respuestas a emails tracked
                        if result.get('type') == 'messages_added':
                            self._check_for_tracked_email_replies(change.get('messagesAdded', []))
                
                # Actualizar último history_id
                webhook_config['history_id'] = history_id
                webhook_config['last_processed'] = timezone.now().isoformat()
                cache.set(f"{self.cache_prefix}webhook_config", webhook_config, timeout=3600*24*7)
            
            logger.info(f"✅ Webhook procesado - {len(processed_changes)} cambios")
            
            return {
                'success': True,
                'processed_changes': len(processed_changes),
                'changes': processed_changes,
                'email_address': email_address,
                'history_id': history_id
            }
            
        except Exception as e:
            logger.error(f"❌ Error procesando webhook Gmail: {e}")
            return {'success': False, 'error': str(e)}
    
    def _check_for_tracked_email_replies(self, new_messages: List[Dict[str, Any]]):
        """
        Verificar si hay respuestas a emails tracked
        """
        try:
            if not self.gmail_service:
                return
            
            for message_ref in new_messages:
                message_id = message_ref.get('message', {}).get('id')
                if not message_id:
                    continue
                
                # Obtener detalles del mensaje
                message = self.gmail_service.users().messages().get(
                    userId='me', id=message_id
                ).execute()
                
                # Verificar si es respuesta a un email tracked
                thread_id = message.get('threadId')
                if thread_id:
                    self._process_potential_reply(message, thread_id)
                    
        except Exception as e:
            logger.error(f"Error verificando respuestas tracked: {e}")
    
    def _process_potential_reply(self, message: Dict[str, Any], thread_id: str):
        """
        Procesar posible respuesta a email tracked
        """
        try:
            # Obtener headers del mensaje
            headers = message.get('payload', {}).get('headers', [])
            
            # Buscar información relevante
            from_email = None
            subject = None
            
            for header in headers:
                name = header.get('name', '').lower()
                value = header.get('value', '')
                
                if name == 'from':
                    from_email = value
                elif name == 'subject':
                    subject = value
            
            if from_email:
                # Buscar emails tracked a este destinatario
                try:
                    from inventory.models import TrackedEmail
                    
                    tracked_emails = TrackedEmail.objects.filter(
                        recipient_email__icontains=from_email.split('<')[0].strip(),
                        status__in=['sent', 'opened', 'clicked']
                    ).order_by('-sent_at')[:5]  # Últimos 5 emails a este destinatario
                    
                    for tracked_email in tracked_emails:
                        # Marcar como respondido si no está ya marcado
                        if tracked_email.status != 'replied':
                            tracked_email.status = 'replied'
                            tracked_email.replied_at = timezone.now()
                            tracked_email.save()
                            
                            logger.info(f"📩 Email tracked marcado como respondido: {tracked_email.tracking_id}")
                            
                            # Actualizar datos en cache también
                            tracking_data = self._get_tracking_data(tracked_email.tracking_id)
                            if tracking_data:
                                tracking_data.replied_at = timezone.now()
                                tracking_data.status = 'replied'
                                self._cache_tracking_data(tracked_email.tracking_id, tracking_data)
                    
                except Exception as e:
                    logger.warning(f"Error actualizando tracked emails: {e}")
                    
        except Exception as e:
            logger.error(f"Error procesando posible respuesta: {e}")

    def process_gmail_webhook(self, notification_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesar notificación de webhook de Gmail
        """
        try:
            # Decodificar datos de la notificación
            message_data = notification_data.get('message', {})
            data = json.loads(base64.b64decode(message_data.get('data', '')).decode())
            
            email_address = data.get('emailAddress')
            history_id = data.get('historyId')
            
            if not email_address or not history_id:
                return {'success': False, 'error': 'Datos de notificación inválidos'}
            
            # Obtener cambios desde el último history_id conocido
            webhook_config = cache.get(f"{self.cache_prefix}webhook_config", {})
            last_history_id = webhook_config.get('history_id')
            
            if last_history_id:
                changes = self._get_gmail_history(last_history_id, history_id)
                
                # Procesar cambios
                processed_changes = []
                for change in changes:
                    result = self._process_gmail_change(change)
                    if result:
                        processed_changes.append(result)
                
                # Actualizar último history_id
                webhook_config['history_id'] = history_id
                cache.set(f"{self.cache_prefix}webhook_config", webhook_config, timeout=3600*24*7)
                
                return {
                    'success': True,
                    'processed_changes': len(processed_changes),
                    'changes': processed_changes
                }
            
            return {'success': True, 'message': 'Webhook procesado (sin historial previo)'}
            
        except Exception as e:
            logger.error(f"Error procesando Gmail webhook: {e}")
            return {'success': False, 'error': str(e)}
    
    def analyze_email_patterns(self, days_back: int = 30, 
                             include_ai_analysis: bool = True) -> List[EmailPattern]:
        """
        Analizar patrones de email
        """
        try:
            patterns = []
            
            # Obtener emails del período
            emails = self._get_emails_for_analysis(days_back)
            
            if not emails:
                return patterns
            
            # Análisis básico de patrones
            patterns.extend(self._analyze_time_patterns(emails))
            patterns.extend(self._analyze_sender_patterns(emails))
            patterns.extend(self._analyze_subject_patterns(emails))
            patterns.extend(self._analyze_content_patterns(emails))
            
            # Análisis con IA si está disponible
            if include_ai_analysis and self.openai_client:
                ai_patterns = self._analyze_patterns_with_ai(emails)
                patterns.extend(ai_patterns)
            
            # Cachear resultados
            cache.set(f"{self.cache_prefix}email_patterns", patterns, timeout=3600*6)  # 6 horas
            
            logger.info(f"Análisis de patrones completado: {len(patterns)} patrones encontrados")
            return patterns
            
        except Exception as e:
            logger.error(f"Error analizando patrones de email: {e}")
            return []
    
    def generate_email_insights(self, patterns: List[EmailPattern] = None) -> List[EmailInsight]:
        """
        Generar insights usando OpenAI
        """
        if not self.openai_client:
            logger.warning("OpenAI no disponible para generar insights")
            return []
        
        try:
            # Usar patrones existentes o generar nuevos
            if not patterns:
                patterns = self.analyze_email_patterns()
            
            # Preparar datos para análisis
            patterns_data = [asdict(pattern) for pattern in patterns]
            
            # Obtener métricas adicionales
            metrics = self._get_email_metrics()
            
            # Crear prompt para análisis
            prompt = f"""
            Analiza los siguientes patrones de email y métricas para generar insights accionables:
            
            PATRONES DETECTADOS:
            {json.dumps(patterns_data, indent=2, default=str)}
            
            MÉTRICAS:
            {json.dumps(metrics, indent=2, default=str)}
            
            Por favor genera insights específicos que incluyan:
            1. Identificación de oportunidades de mejora
            2. Recomendaciones para optimizar comunicación por email
            3. Detección de problemas o riesgos
            4. Sugerencias para automatización
            5. Insights sobre comportamiento de clientes/usuarios
            
            Responde en formato JSON con una lista de insights.
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un experto analista de comunicaciones por email y marketing digital. "
                                 "Genera insights valiosos y accionables basados en datos de email."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3
            )
            
            # Parsear respuesta
            insights_data = json.loads(response.choices[0].message.content)
            
            # Convertir a objetos EmailInsight
            insights = []
            for insight_dict in insights_data.get('insights', []):
                insight = EmailInsight(
                    insight_type=insight_dict.get('insight_type', 'general'),
                    priority=insight_dict.get('priority', 'medium'),
                    title=insight_dict.get('title', ''),
                    description=insight_dict.get('description', ''),
                    action_items=insight_dict.get('action_items', []),
                    confidence_score=insight_dict.get('confidence_score', 0.5)
                )
                insights.append(insight)
            
            # Cachear insights
            cache.set(f"{self.cache_prefix}email_insights", insights, timeout=3600*12)  # 12 horas
            
            logger.info(f"Insights generados: {len(insights)} insights")
            return insights
            
        except Exception as e:
            logger.error(f"Error generando insights de email: {e}")
            return []
    
    def get_email_analytics_dashboard(self) -> Dict[str, Any]:
        """
        Obtener datos completos para dashboard de analytics
        """
        try:
            # Métricas básicas
            metrics = self._get_email_metrics()
            
            # Patrones recientes
            patterns = cache.get(f"{self.cache_prefix}email_patterns")
            if not patterns:
                patterns = self.analyze_email_patterns()
            
            # Insights recientes
            insights = cache.get(f"{self.cache_prefix}email_insights")
            if not insights:
                insights = self.generate_email_insights(patterns)
            
            # Estadísticas de tracking
            tracking_stats = self._get_tracking_statistics()
            
            # Tendencias
            trends = self._get_email_trends()
            
            dashboard_data = {
                'metrics': metrics,
                'patterns': [asdict(p) for p in patterns],
                'insights': [asdict(i) for i in insights],
                'tracking_stats': tracking_stats,
                'trends': trends,
                'last_updated': timezone.now().isoformat(),
                'company_id': self.company_id
            }
            
            # Cachear dashboard
            cache.set(f"{self.cache_prefix}dashboard", dashboard_data, timeout=3600*2)  # 2 horas
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error generando dashboard de analytics: {e}")
            return {}
    
    # Métodos auxiliares privados
    
    def _add_click_tracking(self, html_content: str, tracking_id: str) -> str:
        """Agregar tracking de clicks a enlaces en HTML"""
        try:
            # Patrón para encontrar enlaces
            link_pattern = r'<a\s+(?:[^>]*?\s+)?href=(["\'])(.*?)\1'
            
            def replace_link(match):
                quote = match.group(1)
                original_url = match.group(2)
                
                # No trackear enlaces internos
                if original_url.startswith('#') or 'email-tracking' in original_url:
                    return match.group(0)
                
                # Crear URL de tracking
                tracking_url = f"{settings.FRONTEND_URL}/api/email-tracking/click/{tracking_id}/?url={original_url}"
                
                return match.group(0).replace(f'href={quote}{original_url}{quote}', 
                                            f'href={quote}{tracking_url}{quote}')
            
            return re.sub(link_pattern, replace_link, html_content)
            
        except Exception as e:
            logger.error(f"Error agregando click tracking: {e}")
            return html_content
    
    def _cache_tracking_data(self, tracking_id: str, tracking_data: EmailTracking):
        """Cachear datos de tracking"""
        cache.set(f"{self.cache_prefix}tracking_{tracking_id}", 
                 asdict(tracking_data), timeout=3600*24*30)  # 30 días
    
    def _get_tracking_data(self, tracking_id: str) -> Optional[EmailTracking]:
        """Obtener datos de tracking del cache"""
        data = cache.get(f"{self.cache_prefix}tracking_{tracking_id}")
        if data:
            # Convertir datetime strings de vuelta a objetos datetime
            for date_field in ['sent_at', 'opened_at', 'clicked_at', 'replied_at']:
                if data.get(date_field):
                    data[date_field] = datetime.fromisoformat(data[date_field].replace('Z', '+00:00'))
            return EmailTracking(**data)
        return None
    
    def _get_emails_for_analysis(self, days_back: int) -> List[Dict[str, Any]]:
        """Obtener emails para análisis (implementación básica usando cache)"""
        # En una implementación real, esto obtendría emails de Gmail API o base de datos
        # Por ahora, retornamos datos de ejemplo para análisis
        return []
    
    def _analyze_time_patterns(self, emails: List[Dict[str, Any]]) -> List[EmailPattern]:
        """Analizar patrones temporales"""
        patterns = []
        
        # Análisis de horarios pico (ejemplo)
        pattern = EmailPattern(
            pattern_type="time_peak",
            frequency=5,
            confidence=0.8,
            description="Pico de emails recibidos entre 9-11 AM",
            examples=["9:30 AM - 15 emails", "10:15 AM - 12 emails"],
            recommendation="Programar respuestas automáticas durante horas pico"
        )
        patterns.append(pattern)
        
        return patterns
    
    def _analyze_sender_patterns(self, emails: List[Dict[str, Any]]) -> List[EmailPattern]:
        """Analizar patrones de remitentes"""
        return []
    
    def _analyze_subject_patterns(self, emails: List[Dict[str, Any]]) -> List[EmailPattern]:
        """Analizar patrones en asuntos"""
        return []
    
    def _analyze_content_patterns(self, emails: List[Dict[str, Any]]) -> List[EmailPattern]:
        """Analizar patrones en contenido"""
        return []
    
    def _analyze_patterns_with_ai(self, emails: List[Dict[str, Any]]) -> List[EmailPattern]:
        """Analizar patrones usando IA"""
        patterns = []
        
        try:
            if not emails:
                return patterns
            
            # Preparar datos para análisis de IA
            sample_data = emails[:20]  # Muestra para análisis
            
            prompt = f"""
            Analiza los siguientes emails y detecta patrones interesantes:
            
            {json.dumps(sample_data, indent=2, default=str)[:2000]}...
            
            Identifica patrones únicos que no serían obvios en análisis básicos.
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un experto en análisis de patrones de comunicación por email."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3
            )
            
            # Procesar respuesta y crear patrones
            # (implementación simplificada)
            
        except Exception as e:
            logger.error(f"Error en análisis de IA: {e}")
        
        return patterns
    
    def _get_email_metrics(self) -> Dict[str, Any]:
        """Obtener métricas básicas de email"""
        return {
            'total_emails_sent': 0,
            'total_emails_opened': 0,
            'total_emails_clicked': 0,
            'open_rate': 0.0,
            'click_rate': 0.0,
            'bounce_rate': 0.0,
            'reply_rate': 0.0
        }
    
    def _get_tracking_statistics(self) -> Dict[str, Any]:
        """Obtener estadísticas de tracking"""
        return {
            'tracked_emails': 0,
            'unique_opens': 0,
            'unique_clicks': 0,
            'avg_time_to_open': '0 minutes',
            'top_clicked_links': []
        }
    
    def _get_email_trends(self) -> Dict[str, Any]:
        """Obtener tendencias de email"""
        return {
            'daily_volume': [],
            'response_times': [],
            'engagement_trends': []
        }
    
    def _get_gmail_history(self, start_history_id: str, end_history_id: str) -> List[Dict[str, Any]]:
        """Obtener historial de cambios de Gmail"""
        if not self.gmail_service:
            return []
        
        try:
            result = self.gmail_service.users().history().list(
                userId='me',
                startHistoryId=start_history_id
            ).execute()
            
            return result.get('history', [])
            
        except Exception as e:
            logger.error(f"Error obteniendo historial de Gmail: {e}")
            return []
    
    def _process_gmail_change(self, change: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Procesar un cambio individual de Gmail"""
        try:
            # Procesar diferentes tipos de cambios
            if 'messagesAdded' in change:
                return self._process_messages_added(change['messagesAdded'])
            elif 'messagesDeleted' in change:
                return self._process_messages_deleted(change['messagesDeleted'])
            elif 'labelsAdded' in change:
                return self._process_labels_changed(change['labelsAdded'])
            
            return None
            
        except Exception as e:
            logger.error(f"Error procesando cambio de Gmail: {e}")
            return None
    
    def _process_messages_added(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Procesar mensajes agregados"""
        return {
            'type': 'messages_added',
            'count': len(messages),
            'processed_at': timezone.now().isoformat()
        }
    
    def _process_messages_deleted(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Procesar mensajes eliminados"""
        return {
            'type': 'messages_deleted',
            'count': len(messages),
            'processed_at': timezone.now().isoformat()
        }
    
    def _process_labels_changed(self, labels: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Procesar cambios de etiquetas"""
        return {
            'type': 'labels_changed',
            'count': len(labels),
            'processed_at': timezone.now().isoformat()
        }


# Funciones de utilidad para integración

def get_email_tracking_service(company_id: int = None) -> EmailTrackingService:
    """Obtener instancia del servicio de tracking de emails"""
    return EmailTrackingService(company_id=company_id)

def send_tracked_email(to: str, subject: str, body: str, company_id: int = None, 
                      **kwargs) -> Dict[str, Any]:
    """Función de utilidad para enviar email tracked"""
    service = get_email_tracking_service(company_id)
    return service.send_tracked_email(to, subject, body, **kwargs)

def analyze_email_patterns(company_id: int = None, days_back: int = 30) -> List[EmailPattern]:
    """Función de utilidad para analizar patrones"""
    service = get_email_tracking_service(company_id)
    return service.analyze_email_patterns(days_back=days_back)

def get_email_insights(company_id: int = None) -> List[EmailInsight]:
    """Función de utilidad para obtener insights"""
    service = get_email_tracking_service(company_id)
    return service.generate_email_insights()


# =================================
# MÉTODOS ALIAS PARA COMPATIBILIDAD
# =================================

# Agregar métodos alias a la clase EmailTrackingService
def _add_alias_methods():
    """Agregar métodos alias para compatibilidad con pruebas"""
    
    def analyze_patterns(self, days_back: int = 30):
        """Alias para analyze_email_patterns"""
        return self.analyze_email_patterns(days_back=days_back)
    
    def generate_insights(self, patterns=None):
        """Alias para generate_email_insights"""
        return self.generate_email_insights(patterns=patterns)
    
    # Agregar métodos a la clase
    EmailTrackingService.analyze_patterns = analyze_patterns
    EmailTrackingService.generate_insights = generate_insights

# Ejecutar la función para agregar alias
_add_alias_methods()
