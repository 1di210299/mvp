"""
Servicio mejorado para detección de stock bajo y generación automática de órdenes de compra
INTEGRADO CON EmailTrackingService para seguimiento completo de emails
"""
import logging
from django.utils import timezone
from django.db import models
from django.db.models import Q, Sum, F
from django.conf import settings
from decimal import Decimal
from datetime import datetime, timedelta, date

from alerts.models import Alert, AlertRule
from inventory.models import Product, PurchaseOrder, PurchaseOrderEmailLog
from authentication.models import Company

logger = logging.getLogger(__name__)


class PurchaseOrderService:
    """Servicio para generar órdenes de compra automáticas basadas en alertas de stock"""
    
    def __init__(self):
        self.email_service = EmailService()
        # ✅ NUEVO: Importar EmailTrackingService localmente para evitar importaciones circulares
        try:
            from inventory.services.email_tracking_service import EmailTrackingService
            self.email_tracking_service = EmailTrackingService(company_id=None)  # Se configurará dinámicamente
        except ImportError as e:
            logger.warning(f"EmailTrackingService no disponible: {e}")
            self.email_tracking_service = None
    
    def check_low_stock_and_generate_orders(self, company=None):
        """
        Verificar stock bajo y generar órdenes automáticas
        Returns: dict con resultados de la operación
        """
        try:
            results = {
                'processed_products': 0,
                'orders_generated': 0,
                'emails_sent': 0,
                'errors': []
            }
            
            # Encontrar productos con stock bajo
            low_stock_products = Product.objects.filter(
                is_active=True
            )
            
            if company:
                low_stock_products = low_stock_products.filter(company=company)
            
            # Filtrar por stock bajo
            low_stock_products = low_stock_products.filter(
                Q(stock__lte=F('min_stock')) |
                Q(stock__lte=10)  # Umbral por defecto
            ).select_related('supplier')
            
            logger.info(f"Encontrados {low_stock_products.count()} productos con stock bajo")
            
            for product in low_stock_products:
                try:
                    results['processed_products'] += 1
                    
                    # Verificar si ya existe una orden pendiente reciente
                    if self._has_pending_order(product):
                        logger.info(f"Producto {product.name} ya tiene orden pendiente")
                        continue
                    
                    # Calcular cantidad a ordenar
                    quantity_to_order = self._calculate_order_quantity(product)
                    
                    if quantity_to_order <= 0:
                        continue
                    
                    # Generar orden de compra
                    purchase_order = self._create_purchase_order(product, quantity_to_order)
                    
                    if purchase_order:
                        results['orders_generated'] += 1
                        
                        # Enviar email automáticamente si está configurado
                        if self._should_send_email_automatically(purchase_order):
                            email_sent = self._send_purchase_order_email(purchase_order)
                            if email_sent:
                                results['emails_sent'] += 1
                        
                        logger.info(f"Orden generada: {purchase_order.order_number} para {product.name}")
                
                except Exception as e:
                    error_msg = f"Error procesando producto {product.name}: {str(e)}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
            
            return results
            
        except Exception as e:
            logger.error(f"Error en check_low_stock_and_generate_orders: {str(e)}")
            return {'error': str(e)}
    
    def _has_pending_order(self, product, days_threshold=7):
        """Verificar si existe una orden pendiente reciente"""
        threshold_date = timezone.now() - timedelta(days=days_threshold)
        
        return PurchaseOrder.objects.filter(
            product=product,
            status__in=['draft', 'sent', 'confirmed'],
            created_at__gte=threshold_date
        ).exists()
    
    def _calculate_order_quantity(self, product):
        """Calcular cantidad óptima a ordenar basada en diferentes factores"""
        try:
            current_stock = product.stock or 0
            min_stock = product.min_stock or 10
            max_stock = product.max_stock or (min_stock * 3)
            
            # Método 1: Reposición hasta stock máximo
            basic_quantity = max_stock - current_stock
            
            # Método 2: Basado en demanda histórica (si está disponible)
            demand_based_quantity = self._calculate_demand_based_quantity(product)
            
            # Método 3: Múltiplos del proveedor (si están configurados)
            supplier_minimum = getattr(product.supplier, 'minimum_order_quantity', 1) if product.supplier else 1
            
            # Usar la mayor cantidad calculada
            final_quantity = max(basic_quantity, demand_based_quantity)
            
            # Ajustar a múltiplos del proveedor
            if supplier_minimum > 1:
                final_quantity = ((final_quantity // supplier_minimum) + 1) * supplier_minimum
            
            return max(final_quantity, 1)  # Mínimo 1 unidad
            
        except Exception as e:
            logger.error(f"Error calculando cantidad para {product.name}: {str(e)}")
            return max((product.max_stock or 50) - (product.stock or 0), 1)
    
    def _calculate_demand_based_quantity(self, product):
        """Calcular cantidad basada en demanda histórica"""
        try:
            from inventory.models import Transaction
            
            # Analizar ventas de los últimos 30 días
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=30)
            
            recent_sales = Transaction.objects.filter(
                product=product,
                transaction_type='sale',
                transaction_date__date__range=[start_date, end_date]
            ).aggregate(
                total_sold=Sum('quantity')
            )['total_sold'] or 0
            
            if recent_sales > 0:
                # Calcular demanda diaria promedio
                daily_demand = recent_sales / 30
                
                # Proyectar para 60 días (2 meses de stock)
                projected_demand = daily_demand * 60
                
                return int(projected_demand)
            
            return 0
            
        except Exception as e:
            logger.error(f"Error calculando demanda para {product.name}: {str(e)}")
            return 0
    
    def _create_purchase_order(self, product, quantity):
        """Crear orden de compra"""
        try:
            # Determinar precio unitario
            unit_price = product.cost_price or product.price or Decimal('0.00')
            
            # Crear la orden
            purchase_order = PurchaseOrder.objects.create(
                company=product.company,
                product=product,
                supplier=product.supplier,
                quantity=quantity,
                unit_price=unit_price,
                supplier_email=getattr(product.supplier, 'email', None) if product.supplier else None,
                priority=self._determine_priority(product),
                expected_delivery_date=self._calculate_expected_delivery_date(product),
                ai_generated=True,
                ai_confidence_score=0.85,  # Score base para órdenes automáticas
                created_by=None  # Sistema automático
            )
            
            # Crear alerta asociada
            self._create_associated_alert(purchase_order)
            
            return purchase_order
            
        except Exception as e:
            logger.error(f"Error creando orden para {product.name}: {str(e)}")
            return None
    
    def _determine_priority(self, product):
        """Determinar prioridad de la orden basada en stock actual"""
        current_stock = product.current_stock or 0
        min_stock = product.min_stock or 0
        
        if current_stock <= 0:
            return 'urgent'
        elif current_stock <= min_stock * 0.5:
            return 'high'
        elif current_stock <= min_stock:
            return 'medium'
        else:
            return 'low'
    
    def _calculate_expected_delivery_date(self, product):
        """Calcular fecha esperada de entrega"""
        # Días de entrega por defecto o del proveedor
        delivery_days = 7  # Default
        
        if product.supplier and hasattr(product.supplier, 'delivery_days'):
            delivery_days = product.supplier.delivery_days
        
        return timezone.now().date() + timedelta(days=delivery_days)
    
    def _create_associated_alert(self, purchase_order):
        """Crear alerta asociada a la orden de compra"""
        try:
            Alert.objects.create(
                company=purchase_order.company,
                product=purchase_order.product,
                title=f"Orden de Compra Generada: {purchase_order.product.name}",
                message=f"Se ha generado automáticamente la orden {purchase_order.order_number} "
                       f"para reabastecer {purchase_order.quantity} unidades debido a stock bajo.",
                severity='medium',
                status='active',
                source='system',
                current_value=purchase_order.product.stock,
                threshold_value=purchase_order.product.min_stock,
                context_data={
                    'purchase_order_id': purchase_order.id,
                    'order_number': purchase_order.order_number,
                    'auto_generated': True
                }
            )
            
        except Exception as e:
            logger.error(f"Error creando alerta para orden {purchase_order.order_number}: {str(e)}")
    
    def _should_send_email_automatically(self, purchase_order):
        """Determinar si se debe enviar email automáticamente"""
        # Verificar configuración global
        if not getattr(settings, 'AUTO_SEND_PURCHASE_ORDERS', True):
            return False
        
        # Verificar que tenga email del proveedor
        if not purchase_order.supplier_email:
            return False
        
        # Verificar que no se haya enviado ya
        if purchase_order.email_sent:
            return False
        
        return True
    
    def _send_purchase_order_email(self, purchase_order):
        """Enviar email de orden de compra CON TRACKING AUTOMÁTICO"""
        try:
            # Generar contenido del email con IA
            email_content = self.email_service.generate_purchase_order_email(purchase_order)
            
            # Determinar destinatario
            recipient_email = purchase_order.supplier_email
            if not recipient_email and purchase_order.supplier:
                recipient_email = purchase_order.supplier.email
            
            if not recipient_email:
                logger.warning(f"No hay email para enviar orden {purchase_order.order_number}")
                return False
            
            # ✅ NUEVO: Enviar email CON TRACKING usando EmailTrackingService
            if self.email_tracking_service:
                # Configurar company_id dinámicamente
                self.email_tracking_service.company_id = purchase_order.company.id
                
                tracking_result = self._send_tracked_purchase_order_email(
                    purchase_order, recipient_email, email_content
                )
                
                if tracking_result['success']:
                    purchase_order.mark_as_sent(recipient_email)
                    purchase_order.email_subject = email_content['subject']
                    purchase_order.email_content = email_content['content']
                    purchase_order.tracking_id = tracking_result.get('tracking_id')  # Guardar tracking ID
                    purchase_order.email_tracking_campaign_id = tracking_result.get('campaign_id')  # Guardar campaign ID
                    purchase_order.save()
                    
                    logger.info(f"✅ Email con tracking enviado: {purchase_order.order_number} -> {recipient_email}")
                    return True
                else:
                    logger.error(f"❌ Error con tracking: {tracking_result.get('error')}")
            
            # Fallback: Enviar email tradicional si tracking no está disponible
            success = self.email_service.send_purchase_order_email(
                purchase_order=purchase_order,
                recipient_email=recipient_email,
                subject=email_content['subject'],
                content=email_content['content']
            )
            
            if success:
                purchase_order.mark_as_sent(recipient_email)
                purchase_order.email_subject = email_content['subject']
                purchase_order.email_content = email_content['content']
                purchase_order.save()
            
            return success
            
        except Exception as e:
            logger.error(f"Error enviando email para orden {purchase_order.order_number}: {str(e)}")
            return False

    def _send_tracked_purchase_order_email(self, purchase_order, recipient_email, email_content):
        """
        Enviar email de orden de compra CON TRACKING usando EmailTrackingService
        """
        try:
            # Obtener o crear campaña para órdenes de compra
            campaign = self._get_or_create_purchase_order_campaign(purchase_order.company)
            
            # Preparar contenido del email con pixel de tracking
            subject = email_content['subject']
            content = email_content['content']
            
            # Añadir información adicional al email para tracking
            content_with_tracking = f"""
{content}

DETALLES ADICIONALES:
• Orden: {purchase_order.order_number}
• Fecha: {purchase_order.created_at.strftime('%d/%m/%Y %H:%M')}
• Prioridad: {purchase_order.get_priority_display()}

Para confirmar recepción y disponibilidad, por favor responda este email.

---
Sistema DataLens - Gestión Inteligente de Inventario
"""
            
            # Enviar email con tracking usando EmailTrackingService
            result = self.email_tracking_service.send_tracked_email(
                to=recipient_email,
                subject=subject,
                body=content_with_tracking,
                html_body=self._generate_html_email_content(purchase_order, content_with_tracking),
                track_opens=True,
                track_clicks=True
            )
            
            if result['success']:
                logger.info(f"📧✅ Email con tracking enviado exitosamente: {purchase_order.order_number}")
                
                # Actualizar métricas de la campaña
                if campaign:
                    campaign.total_sent += 1
                    campaign.save()
                
                return {
                    'success': True,
                    'tracking_id': result['tracking_id'],
                    'email_id': result['email_id'],
                    'campaign_id': str(campaign.id) if campaign else None
                }
            else:
                logger.error(f"📧❌ Error enviando email con tracking: {result.get('error')}")
                return {'success': False, 'error': result.get('error')}
                
        except Exception as e:
            logger.error(f"📧❌ Error en _send_tracked_purchase_order_email: {str(e)}")
            return {'success': False, 'error': str(e)}

    def _get_or_create_purchase_order_campaign(self, company):
        """
        Obtener o crear campaña para órdenes de compra
        """
        try:
            from inventory.models import EmailCampaign
            
            campaign, created = EmailCampaign.objects.get_or_create(
                name="Órdenes de Compra Automáticas",
                company=company,
                defaults={
                    'description': 'Campaña automática para seguimiento de órdenes de compra generadas por el sistema',
                    'track_opens': True,
                    'track_clicks': True,
                    'is_active': True
                }
            )
            
            if created:
                logger.info(f"📊 Campaña de email creada para {company.name}")
            
            return campaign
            
        except Exception as e:
            logger.error(f"Error creando campaña de email: {str(e)}")
            return None

    def _generate_html_email_content(self, purchase_order, text_content):
        """
        Generar contenido HTML para email con mejor presentación
        """
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Orden de Compra - {purchase_order.order_number}</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; }}
        .header {{ background-color: #2c3e50; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background-color: #f9f9f9; }}
        .order-details {{ background-color: white; padding: 15px; border-radius: 5px; margin: 15px 0; }}
        .footer {{ background-color: #34495e; color: white; padding: 15px; text-align: center; font-size: 12px; }}
        .priority-{purchase_order.priority} {{ border-left: 4px solid {'#e74c3c' if purchase_order.priority == 'urgent' else '#f39c12' if purchase_order.priority == 'high' else '#27ae60'}; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🛒 Orden de Compra</h1>
        <h2>#{purchase_order.order_number}</h2>
    </div>
    
    <div class="content">
        <div class="order-details priority-{purchase_order.priority}">
            <h3>📋 Detalles de la Orden</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <tr><td><strong>Producto:</strong></td><td>{purchase_order.product.name}</td></tr>
                <tr><td><strong>SKU:</strong></td><td>{purchase_order.product.sku}</td></tr>
                <tr><td><strong>Cantidad:</strong></td><td>{purchase_order.quantity} unidades</td></tr>
                <tr><td><strong>Precio Unitario:</strong></td><td>S/ {purchase_order.unit_price}</td></tr>
                <tr><td><strong>Total:</strong></td><td>S/ {purchase_order.total_amount}</td></tr>
                <tr><td><strong>Prioridad:</strong></td><td>{purchase_order.get_priority_display()}</td></tr>
                <tr><td><strong>Fecha Esperada:</strong></td><td>{purchase_order.expected_delivery_date}</td></tr>
            </table>
        </div>
        
        <div style="background-color: white; padding: 15px; border-radius: 5px; margin: 15px 0;">
            <h3>📞 Información de Contacto</h3>
            <p><strong>Empresa:</strong> {purchase_order.company.name}</p>
            <p><strong>Teléfono:</strong> {getattr(purchase_order.company, 'phone', 'Por especificar')}</p>
            <p><strong>Email:</strong> {getattr(purchase_order.company, 'email', 'sistema@datalens.com')}</p>
        </div>
        
        <div style="text-align: center; margin: 20px 0;">
            <p><strong>Por favor confirme:</strong></p>
            <ul style="text-align: left; display: inline-block;">
                <li>✅ Disponibilidad del producto</li>
                <li>📅 Tiempo de entrega</li>
                <li>💰 Condiciones de pago</li>
                <li>🚚 Datos para entrega</li>
            </ul>
        </div>
    </div>
    
    <div class="footer">
        <p>📧 Para confirmar, responda este email o contacte a nuestro equipo de compras</p>
        <p>Sistema DataLens - Gestión Inteligente de Inventario</p>
    </div>
</body>
</html>
        """
        return html_content

    def get_purchase_order_tracking_status(self, purchase_order):
        """
        Obtener estado del tracking para una orden de compra
        """
        try:
            if not self.email_tracking_service:
                return {'tracking_available': False, 'reason': 'EmailTrackingService no disponible'}
            
            tracking_id = getattr(purchase_order, 'tracking_id', None)
            if not tracking_id:
                return {'tracking_available': False, 'reason': 'No hay tracking_id en la orden'}
            
            # Obtener datos de tracking usando el método público
            try:
                # Intentar obtener datos de tracking directamente desde la base de datos
                from inventory.models import TrackedEmail
                
                tracked_email = TrackedEmail.objects.filter(tracking_id=tracking_id).first()
                
                if not tracked_email:
                    return {'tracking_available': False, 'reason': 'Email tracked no encontrado en BD'}
                
                return {
                    'tracking_available': True,
                    'tracking_id': tracking_id,
                    'status': tracked_email.status,
                    'sent_at': tracked_email.sent_at,
                    'opened_at': tracked_email.first_opened_at,
                    'clicked_at': tracked_email.first_clicked_at,
                    'replied_at': tracked_email.replied_at,
                    'recipient': tracked_email.recipient_email,
                    'subject': tracked_email.subject,
                    'open_count': tracked_email.open_count,
                    'click_count': tracked_email.click_count,
                    'last_activity': tracked_email.last_opened_at or tracked_email.sent_at
                }
                
            except ImportError:
                return {'tracking_available': False, 'reason': 'No se pudo importar TrackedEmail'}
            
        except Exception as e:
            logger.error(f"Error obteniendo tracking status: {str(e)}")
            return {'tracking_available': False, 'error': str(e)}

    def get_purchase_orders_with_tracking_summary(self, company=None, days_back=30):
        """
        Obtener resumen de órdenes de compra con información de tracking
        """
        try:
            from datetime import timedelta
            from django.utils import timezone
            
            # Filtros básicos
            queryset = PurchaseOrder.objects.filter(
                created_at__gte=timezone.now() - timedelta(days=days_back),
                email_sent=True
            )
            
            if company:
                queryset = queryset.filter(company=company)
            
            orders_summary = []
            
            for order in queryset.select_related('product', 'supplier', 'company'):
                tracking_status = self.get_purchase_order_tracking_status(order)
                
                summary = {
                    'order_number': order.order_number,
                    'product_name': order.product.name,
                    'supplier_name': order.supplier.name if order.supplier else 'N/A',
                    'supplier_email': order.supplier_email,
                    'priority': order.priority,
                    'total_amount': float(order.total_amount),
                    'created_at': order.created_at,
                    'email_sent_at': order.email_sent_at,
                    'email_subject': order.email_subject,
                    'tracking': tracking_status
                }
                
                orders_summary.append(summary)
            
            # Estadísticas generales
            total_orders = len(orders_summary)
            orders_with_tracking = len([o for o in orders_summary if o['tracking']['tracking_available']])
            orders_opened = len([o for o in orders_summary if o['tracking'].get('opened_at')])
            orders_clicked = len([o for o in orders_summary if o['tracking'].get('clicked_at')])
            
            return {
                'orders': orders_summary,
                'summary': {
                    'total_orders': total_orders,
                    'orders_with_tracking': orders_with_tracking,
                    'tracking_coverage': (orders_with_tracking / total_orders * 100) if total_orders > 0 else 0,
                    'open_rate': (orders_opened / orders_with_tracking * 100) if orders_with_tracking > 0 else 0,
                    'click_rate': (orders_clicked / orders_with_tracking * 100) if orders_with_tracking > 0 else 0,
                    'orders_opened': orders_opened,
                    'orders_clicked': orders_clicked
                }
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo resumen de tracking: {str(e)}")
            return {'error': str(e)}


class EmailService:
    """Servicio para envío de emails con diferentes proveedores"""
    
    def __init__(self):
        self.gmail_service = GmailService()
        self.sendgrid_service = SendGridService()
        self.default_service = 'smtp'  # Fallback a SMTP básico
    
    def generate_purchase_order_email(self, purchase_order):
        """Generar contenido de email para orden de compra usando OpenAI"""
        try:
            if not hasattr(settings, 'OPENAI_API_KEY') or not settings.OPENAI_API_KEY:
                return self._generate_basic_email_content(purchase_order)
            
            import openai
            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            
            prompt = f"""
            Genera un email profesional para una orden de compra con estos detalles:
            
            Orden: {purchase_order.order_number}
            Producto: {purchase_order.product.name}
            SKU: {purchase_order.product.sku}
            Cantidad: {purchase_order.quantity}
            Precio unitario: S/ {purchase_order.unit_price}
            Total: S/ {purchase_order.total_amount}
            Prioridad: {purchase_order.get_priority_display()}
            Fecha esperada: {purchase_order.expected_delivery_date}
            
            Proveedor: {purchase_order.supplier.name if purchase_order.supplier else 'N/A'}
            Empresa: {purchase_order.company.name}
            
            El email debe ser:
            - Profesional y cordial
            - Incluir todos los detalles de la orden
            - Solicitar confirmación de disponibilidad y tiempo de entrega
            - Incluir urgencia si la prioridad es alta
            
            Responde en formato JSON con keys: subject, content
            """
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=600,
                temperature=0.7
            )
            
            import json
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Error generando email con OpenAI: {str(e)}")
            return self._generate_basic_email_content(purchase_order)
    
    def _generate_basic_email_content(self, purchase_order):
        """Generar contenido básico de email sin IA"""
        priority_text = ""
        if purchase_order.priority in ['high', 'urgent']:
            priority_text = f"🚨 ORDEN {purchase_order.get_priority_display().upper()}"
        
        subject = f"{priority_text} Orden de Compra #{purchase_order.order_number} - {purchase_order.product.name}"
        
        content = f"""
Estimado proveedor,

Nos dirigimos a ustedes para solicitar la siguiente orden de compra:

DETALLES DE LA ORDEN:
• Número de Orden: {purchase_order.order_number}
• Producto: {purchase_order.product.name}
• SKU: {purchase_order.product.sku}
• Cantidad: {purchase_order.quantity} unidades
• Precio unitario: S/ {purchase_order.unit_price}
• Total: S/ {purchase_order.total_amount}
• Prioridad: {purchase_order.get_priority_display()}
• Fecha esperada de entrega: {purchase_order.expected_delivery_date}

Por favor, confirmen:
1. Disponibilidad del producto
2. Tiempo de entrega
3. Condiciones de pago
4. Datos para coordinación de entrega

{purchase_order.company.name}
Email: {getattr(purchase_order.company, 'email', '')}
Teléfono: {getattr(purchase_order.company, 'phone', '')}

Saludos cordiales,
Sistema Automático DataLens
        """
        
        return {'subject': subject, 'content': content}
    
    def send_purchase_order_email(self, purchase_order, recipient_email, subject, content):
        """Enviar email usando el mejor servicio disponible"""
        try:
            # Intentar Gmail API primero
            if self._is_gmail_configured():
                success = self.gmail_service.send_email(recipient_email, subject, content)
                if success:
                    self._log_email_sent(purchase_order, recipient_email, subject, content, 'gmail', True)
                    return True
            
            # Fallback a SendGrid
            if self._is_sendgrid_configured():
                success = self.sendgrid_service.send_email(recipient_email, subject, content)
                if success:
                    self._log_email_sent(purchase_order, recipient_email, subject, content, 'sendgrid', True)
                    return True
            
            # Fallback final a SMTP
            success = self._send_smtp_email(recipient_email, subject, content)
            if success:
                self._log_email_sent(purchase_order, recipient_email, subject, content, 'smtp', True)
                return True
            
            # Si todo falla, log del error
            self._log_email_sent(purchase_order, recipient_email, subject, content, 'smtp', False, "Todos los servicios fallaron")
            return False
            
        except Exception as e:
            logger.error(f"Error enviando email: {str(e)}")
            self._log_email_sent(purchase_order, recipient_email, subject, content, 'smtp', False, str(e))
            return False
    
    def _is_gmail_configured(self):
        """Verificar si Gmail API está configurado"""
        return (
            hasattr(settings, 'GMAIL_API_CREDENTIALS') and
            settings.GMAIL_API_CREDENTIALS
        )
    
    def _is_sendgrid_configured(self):
        """Verificar si SendGrid está configurado"""
        return (
            hasattr(settings, 'SENDGRID_API_KEY') and
            settings.SENDGRID_API_KEY
        )
    
    def _send_smtp_email(self, recipient_email, subject, content):
        """Enviar email usando SMTP básico"""
        try:
            from django.core.mail import send_mail
            
            send_mail(
                subject=subject,
                message=content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient_email],
                fail_silently=False,
            )
            return True
            
        except Exception as e:
            logger.error(f"Error enviando SMTP email: {str(e)}")
            return False
    
    def _log_email_sent(self, purchase_order, recipient_email, subject, content, service, success, error_msg=None):
        """Crear log del email enviado"""
        try:
            PurchaseOrderEmailLog.objects.create(
                purchase_order=purchase_order,
                email_type='order',
                recipient_email=recipient_email,
                subject=subject,
                content=content,
                sent_successfully=success,
                error_message=error_msg,
                email_service=service
            )
        except Exception as e:
            logger.error(f"Error logging email: {str(e)}")


class GmailService:
    """Servicio para Gmail API"""
    
    def send_email(self, recipient_email, subject, content):
        """Enviar email usando Gmail API"""
        try:
            # TODO: Implementar Gmail API
            # Por ahora, fallback a SMTP
            logger.info("Gmail API no implementado aún, usando SMTP fallback")
            return False
            
        except Exception as e:
            logger.error(f"Error en Gmail API: {str(e)}")
            return False


class SendGridService:
    """Servicio para SendGrid API"""
    
    def send_email(self, recipient_email, subject, content):
        """Enviar email usando SendGrid API"""
        try:
            # TODO: Implementar SendGrid API
            # Por ahora, fallback a SMTP
            logger.info("SendGrid API no implementado aún, usando SMTP fallback")
            return False
            
        except Exception as e:
            logger.error(f"Error en SendGrid API: {str(e)}")
            return False
