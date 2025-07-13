"""
Comando para probar el sistema completo de alertas con forecasting
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from alerts.models import AlertRule, Alert
from alerts.services import AlertService
from authentication.models import Company, User
from inventory.models import Product, Category
from forecasting.models import ForecastModel, DemandForecast, ReorderRecommendation
from decimal import Decimal
from datetime import date, timedelta
import random


class Command(BaseCommand):
    help = 'Prueba el sistema completo de alertas con forecasting y genera datos de ejemplo'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company-id',
            type=int,
            help='ID de la empresa para probar las alertas',
        )
        parser.add_argument(
            '--create-data',
            action='store_true',
            help='Crear datos de ejemplo para forecasting',
        )

    def handle(self, *args, **options):
        company_id = options.get('company_id')
        create_data = options.get('create_data', False)
        
        if company_id:
            try:
                company = Company.objects.get(id=company_id)
            except Company.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Empresa con ID {company_id} no encontrada')
                )
                return
        else:
            company = Company.objects.first()
            if not company:
                self.stdout.write(
                    self.style.ERROR('No hay empresas en el sistema')
                )
                return

        self.stdout.write(f'🏢 Probando sistema de alertas para: {company.name}')
        
        # Crear datos de ejemplo si se solicita
        if create_data:
            self.create_sample_data(company)
        
        # Probar el servicio de alertas
        alert_service = AlertService()
        
        # 1. Verificar alertas sincronizadas
        self.stdout.write('\n📊 Ejecutando verificación síncrona de alertas...')
        result = alert_service.check_all_alerts_sync()
        
        self.stdout.write(f'✅ Reglas procesadas: {result.get("rules_processed", 0)}')
        self.stdout.write(f'🚨 Alertas generadas: {result.get("alerts_generated", 0)}')
        self.stdout.write(f'📈 Alertas de forecasting: {result.get("forecasting_alerts", 0)}')
        
        # 2. Mostrar estadísticas de alertas
        self.show_alert_statistics(company)
        
        # 3. Probar notificaciones (sin enviar realmente)
        self.test_notifications(company)
        
        # 4. Mostrar alertas recientes
        self.show_recent_alerts(company)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n🎉 Prueba completada exitosamente!\n'
                f'💡 Para ver las alertas en el dashboard:\n'
                f'   http://localhost:8081/app/alerts\n\n'
                f'🔧 Comandos útiles:\n'
                f'   python manage.py setup_alert_rules --company-id {company.id}\n'
                f'   python manage.py test_comprehensive_alerts --company-id {company.id} --create-data\n'
            )
        )

    def create_sample_data(self, company):
        """Crear datos de ejemplo para forecasting y alertas"""
        self.stdout.write('📦 Creando datos de ejemplo...')
        
        # Obtener productos existentes
        products = Product.objects.filter(company=company, is_active=True)[:5]
        
        if not products.exists():
            self.stdout.write(
                self.style.WARNING('No hay productos disponibles. Creando productos de ejemplo...')
            )
            category, _ = Category.objects.get_or_create(
                name='Productos de Prueba',
                company=company,
                defaults={'description': 'Categoría para pruebas de alertas'}
            )
            
            products_data = [
                {'name': 'Producto A', 'sku': 'TEST-001', 'min_stock': 10, 'current_stock': 5},
                {'name': 'Producto B', 'sku': 'TEST-002', 'min_stock': 20, 'current_stock': 25},
                {'name': 'Producto C', 'sku': 'TEST-003', 'min_stock': 15, 'current_stock': 0},
                {'name': 'Producto D', 'sku': 'TEST-004', 'min_stock': 30, 'current_stock': 45},
                {'name': 'Producto E', 'sku': 'TEST-005', 'min_stock': 8, 'current_stock': -2},
            ]
            
            created_products = []
            for data in products_data:
                product, created = Product.objects.get_or_create(
                    sku=data['sku'],
                    company=company,
                    defaults={
                        'name': data['name'],
                        'category': category,
                        'cost_price': Decimal('10.00'),
                        'sale_price': Decimal('15.00'),
                        'min_stock': data['min_stock'],
                        'max_stock': data['min_stock'] * 5,
                        'reorder_point': data['min_stock'] * 1.5,
                        'unit': 'unidad',
                        'current_stock': data['current_stock'],
                        'track_batches': False,
                        'has_expiration': False,
                    }
                )
                if created:
                    created_products.append(product)
            
            products = created_products
            self.stdout.write(f'✅ Creados {len(created_products)} productos de ejemplo')
        
        # Crear modelo de forecasting de ejemplo
        forecast_model, created = ForecastModel.objects.get_or_create(
            name='Modelo de Prueba',
            company=company,
            defaults={
                'description': 'Modelo para pruebas de alertas',
                'model_type': 'prophet',
                'status': 'active',
                'mae': Decimal('2.5'),
                'mape': Decimal('15.0'),
                'rmse': Decimal('3.2'),
                'r2_score': Decimal('0.85'),
                'forecast_horizon_days': 30,
                'training_period_days': 365,
                'confidence_interval': Decimal('95.0'),
            }
        )
        
        if created:
            self.stdout.write('✅ Modelo de forecasting creado')
        
        # Crear pronósticos de demanda
        for product in products:
            for days_ahead in range(1, 8):  # Próximos 7 días
                forecast_date = date.today() + timedelta(days=days_ahead)
                base_demand = random.randint(5, 50)
                confidence = 0.15  # 15% de variación
                
                DemandForecast.objects.get_or_create(
                    model=forecast_model,
                    product=product,
                    forecast_date=forecast_date,
                    defaults={
                        'forecast_type': 'daily',
                        'predicted_demand': Decimal(str(base_demand)),
                        'lower_bound': Decimal(str(base_demand * (1 - confidence))),
                        'upper_bound': Decimal(str(base_demand * (1 + confidence))),
                        'confidence_level': Decimal('95.0'),
                    }
                )
        
        self.stdout.write('✅ Pronósticos de demanda creados')
        
        # Crear recomendaciones de reorden
        for product in products[:3]:  # Solo para algunos productos
            if product.current_stock <= product.min_stock:
                priority = 'urgent' if product.current_stock <= 0 else 'high'
                
                ReorderRecommendation.objects.get_or_create(
                    product=product,
                    defaults={
                        'recommended_quantity': product.min_stock * 2,
                        'current_stock': product.current_stock,
                        'projected_demand': Decimal(str(random.randint(20, 60))),
                        'recommended_order_date': date.today() + timedelta(days=1),
                        'expected_stockout_date': date.today() + timedelta(days=random.randint(3, 10)),
                        'lead_time_days': 7,
                        'priority': priority,
                        'status': 'pending',
                        'estimated_cost': Decimal(str(product.cost_price)) * (product.min_stock * 2),
                        'potential_lost_sales': Decimal(str(random.randint(100, 500))),
                        'notes': 'Recomendación generada automáticamente para pruebas',
                    }
                )
        
        self.stdout.write('✅ Recomendaciones de reorden creadas')

    def show_alert_statistics(self, company):
        """Mostrar estadísticas de alertas"""
        self.stdout.write('\n📈 Estadísticas de alertas:')
        
        alerts = Alert.objects.filter(company=company)
        total_alerts = alerts.count()
        active_alerts = alerts.filter(status='active').count()
        critical_alerts = alerts.filter(severity='critical').count()
        forecast_alerts = alerts.filter(source='forecast').count()
        
        self.stdout.write(f'   📊 Total de alertas: {total_alerts}')
        self.stdout.write(f'   🔴 Alertas activas: {active_alerts}')
        self.stdout.write(f'   ⚠️  Alertas críticas: {critical_alerts}')
        self.stdout.write(f'   🤖 Alertas de IA/Forecasting: {forecast_alerts}')
        
        # Alertas por tipo
        alert_types = alerts.values('rule__alert_type').distinct()
        if alert_types:
            self.stdout.write('\n   📋 Alertas por tipo:')
            for alert_type in alert_types:
                if alert_type['rule__alert_type']:
                    count = alerts.filter(rule__alert_type=alert_type['rule__alert_type']).count()
                    self.stdout.write(f'      • {alert_type["rule__alert_type"]}: {count}')

    def test_notifications(self, company):
        """Probar sistema de notificaciones"""
        self.stdout.write('\n📧 Probando sistema de notificaciones...')
        
        from alerts.services import NotificationService
        notification_service = NotificationService()
        
        # Probar conexión de email
        email_test = notification_service.test_email_connection()
        if email_test['status'] == 'success':
            self.stdout.write('   ✅ Conexión de email: OK')
        else:
            self.stdout.write(f'   ❌ Conexión de email: {email_test["message"]}')
        
        # Probar conexión de WhatsApp
        whatsapp_test = notification_service.test_whatsapp_connection()
        if whatsapp_test['status'] == 'success':
            self.stdout.write('   ✅ Conexión de WhatsApp: OK')
        else:
            self.stdout.write(f'   ❌ Conexión de WhatsApp: {whatsapp_test["message"]}')

    def show_recent_alerts(self, company):
        """Mostrar alertas recientes"""
        self.stdout.write('\n🚨 Alertas recientes:')
        
        recent_alerts = Alert.objects.filter(
            company=company
        ).order_by('-priority_score', '-created_at')[:5]
        
        if not recent_alerts.exists():
            self.stdout.write('   📭 No hay alertas recientes')
            return
        
        for alert in recent_alerts:
            severity_emoji = {
                'low': '🟢',
                'medium': '🟡',
                'high': '🟠',
                'critical': '🔴'
            }.get(alert.severity, '⚪')
            
            source_emoji = {
                'rule': '📋',
                'forecast': '🤖',
                'system': '⚙️',
                'manual': '👤'
            }.get(alert.source, '📋')
            
            self.stdout.write(
                f'   {severity_emoji} {source_emoji} {alert.title} '
                f'(Prioridad: {alert.priority_score}/100)'
            )
            
            if alert.product:
                self.stdout.write(f'      📦 Producto: {alert.product.name} ({alert.product.sku})')
            
            if alert.demand_forecast:
                self.stdout.write(f'      📈 Demanda proyectada: {alert.demand_forecast.predicted_demand}')
            
            if alert.reorder_recommendation:
                self.stdout.write(f'      📋 Recomendación: {alert.reorder_recommendation.recommended_quantity} unidades')
            
            self.stdout.write(f'      📅 {alert.created_at.strftime("%d/%m/%Y %H:%M")}')
            self.stdout.write('')