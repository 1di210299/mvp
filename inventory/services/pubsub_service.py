"""
Google Cloud Pub/Sub Service para Gmail Webhooks
Maneja la configuración y comunicación con Google Cloud Pub/Sub
"""
import json
import logging
import base64
from typing import Dict, Any, Optional

from django.conf import settings

# Google Cloud Pub/Sub imports
try:
    from google.cloud import pubsub_v1
    from google.oauth2 import service_account
    PUBSUB_AVAILABLE = True
except ImportError:
    PUBSUB_AVAILABLE = False

logger = logging.getLogger(__name__)


class PubSubService:
    """
    Servicio para manejar Google Cloud Pub/Sub para Gmail webhooks
    """
    
    def __init__(self):
        self.project_id = settings.GOOGLE_CLOUD_PROJECT_ID
        self.topic_name = settings.PUBSUB_TOPIC_NAME
        self.subscription_name = settings.PUBSUB_SUBSCRIPTION_NAME
        
        self.publisher = None
        self.subscriber = None
        
        if PUBSUB_AVAILABLE and self.project_id:
            self._initialize_clients()
    
    def _initialize_clients(self):
        """Inicializar clientes de Pub/Sub"""
        try:
            # Configurar credenciales si están disponibles
            credentials = None
            if settings.GOOGLE_APPLICATION_CREDENTIALS:
                credentials = service_account.Credentials.from_service_account_file(
                    settings.GOOGLE_APPLICATION_CREDENTIALS
                )
            
            # Inicializar publisher y subscriber
            if credentials:
                self.publisher = pubsub_v1.PublisherClient(credentials=credentials)
                self.subscriber = pubsub_v1.SubscriberClient(credentials=credentials)
            else:
                # Usar credenciales por defecto del ambiente
                self.publisher = pubsub_v1.PublisherClient()
                self.subscriber = pubsub_v1.SubscriberClient()
            
            logger.info("🔧 Pub/Sub clients inicializados correctamente")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando Pub/Sub clients: {e}")
            self.publisher = None
            self.subscriber = None
    
    def is_available(self) -> bool:
        """Verificar si Pub/Sub está disponible"""
        return PUBSUB_AVAILABLE and self.publisher is not None
    
    def create_topic(self) -> bool:
        """Crear topic de Pub/Sub si no existe"""
        if not self.is_available():
            logger.warning("⚠️  Pub/Sub no disponible")
            return False
        
        try:
            topic_path = self.publisher.topic_path(self.project_id, self.topic_name)
            
            # Verificar si el topic ya existe
            try:
                self.publisher.get_topic(request={"topic": topic_path})
                logger.info(f"✅ Topic ya existe: {topic_path}")
                return True
            except Exception:
                # Topic no existe, crear uno nuevo
                pass
            
            # Crear topic
            topic = self.publisher.create_topic(request={"name": topic_path})
            logger.info(f"✅ Topic creado: {topic.name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creando topic: {e}")
            return False
    
    def create_subscription(self, endpoint_url: str) -> bool:
        """Crear subscription de Pub/Sub para webhook"""
        if not self.is_available():
            logger.warning("⚠️  Pub/Sub no disponible")
            return False
        
        try:
            topic_path = self.publisher.topic_path(self.project_id, self.topic_name)
            subscription_path = self.subscriber.subscription_path(
                self.project_id, self.subscription_name
            )
            
            # Verificar si la subscription ya existe
            try:
                self.subscriber.get_subscription(request={"subscription": subscription_path})
                logger.info(f"✅ Subscription ya existe: {subscription_path}")
                return True
            except Exception:
                # Subscription no existe, crear una nueva
                pass
            
            # Configurar push config
            push_config = pubsub_v1.types.PushConfig(
                push_endpoint=endpoint_url
            )
            
            # Crear subscription
            subscription = self.subscriber.create_subscription(
                request={
                    "name": subscription_path,
                    "topic": topic_path,
                    "push_config": push_config,
                }
            )
            
            logger.info(f"✅ Subscription creada: {subscription.name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creando subscription: {e}")
            return False
    
    def publish_message(self, data: Dict[str, Any]) -> Optional[str]:
        """Publicar mensaje en el topic (para testing)"""
        if not self.is_available():
            logger.warning("⚠️  Pub/Sub no disponible")
            return None
        
        try:
            topic_path = self.publisher.topic_path(self.project_id, self.topic_name)
            
            # Convertir data a JSON y luego a bytes
            message_data = json.dumps(data).encode('utf-8')
            
            # Publicar mensaje
            future = self.publisher.publish(topic_path, message_data)
            message_id = future.result()
            
            logger.info(f"📨 Mensaje publicado: {message_id}")
            return message_id
            
        except Exception as e:
            logger.error(f"❌ Error publicando mensaje: {e}")
            return None
    
    def parse_pubsub_message(self, request_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parsear mensaje de Pub/Sub webhook"""
        try:
            # Extraer mensaje de Pub/Sub
            message = request_data.get('message', {})
            
            # Decodificar data base64
            data_b64 = message.get('data', '')
            if data_b64:
                data_bytes = base64.b64decode(data_b64)
                data_str = data_bytes.decode('utf-8')
                data = json.loads(data_str)
            else:
                data = {}
            
            # Extraer atributos
            attributes = message.get('attributes', {})
            
            # Información del mensaje
            message_id = message.get('messageId')
            publish_time = message.get('publishTime')
            
            return {
                'message_id': message_id,
                'publish_time': publish_time,
                'data': data,
                'attributes': attributes,
                'raw_message': message
            }
            
        except Exception as e:
            logger.error(f"❌ Error parseando mensaje Pub/Sub: {e}")
            return None
    
    def setup_gmail_webhook(self) -> bool:
        """Setup completo de webhook para Gmail"""
        try:
            # 1. Crear topic
            if not self.create_topic():
                return False
            
            # 2. Crear subscription
            webhook_url = settings.PUBSUB_WEBHOOK_URL
            if not webhook_url:
                logger.error("❌ PUBSUB_WEBHOOK_URL no configurado")
                return False
            
            if not self.create_subscription(webhook_url):
                return False
            
            logger.info("✅ Gmail webhook setup completado")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error en setup de Gmail webhook: {e}")
            return False
    
    def get_topic_path(self) -> str:
        """Obtener path completo del topic"""
        if not self.is_available():
            return ""
        return self.publisher.topic_path(self.project_id, self.topic_name)
    
    def get_subscription_path(self) -> str:
        """Obtener path completo de la subscription"""
        if not self.is_available():
            return ""
        return self.subscriber.subscription_path(self.project_id, self.subscription_name)


# Instancia global del servicio
pubsub_service = PubSubService()
