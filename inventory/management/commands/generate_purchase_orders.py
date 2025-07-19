"""
Comando para generar órdenes de compra automáticas manualmente
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from inventory.services.purchase_order_service import PurchaseOrderService
from authentication.models import Company


class Command(BaseCommand):
    help = 'Generar órdenes de compra automáticas para productos con stock bajo'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--company-id',
            type=int,
            help='ID de la empresa específica (opcional)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Solo mostrar qué órdenes se generarían sin crearlas'
        )
        parser.add_argument(
            '--send-emails',
            action='store_true',
            default=True,
            help='Enviar emails automáticamente'
        )
    
    def handle(self, *args, **options):
        self.stdout.write('🚨 Iniciando generación de órdenes de compra automáticas...\n')
        
        try:
            purchase_service = PurchaseOrderService()
            
            # Determinar empresa(s) a procesar
            if options['company_id']:
                try:
                    company = Company.objects.get(id=options['company_id'])
                    companies = [company]
                    self.stdout.write(f'📋 Procesando empresa específica: {company.name}')
                except Company.DoesNotExist:
                    self.stdout.write(
                        self.style.ERROR(f'❌ Empresa con ID {options["company_id"]} no encontrada')
                    )
                    return
            else:
                companies = Company.objects.filter(is_active=True)
                self.stdout.write(f'📋 Procesando {companies.count()} empresas activas')
            
            total_results = {
                'companies_processed': 0,
                'total_products_processed': 0,
                'total_orders_generated': 0,
                'total_emails_sent': 0,
                'total_errors': 0
            }
            
            for company in companies:
                self.stdout.write(f'\n🏢 Procesando empresa: {company.name}')
                
                if options['dry_run']:
                    # Modo simulación - solo mostrar productos que califican
                    self._dry_run_analysis(company)
                else:
                    # Ejecutar generación real
                    results = purchase_service.check_low_stock_and_generate_orders(company=company)
                    
                    if 'error' in results:
                        self.stdout.write(
                            self.style.ERROR(f'   ❌ Error: {results["error"]}')
                        )
                        total_results['total_errors'] += 1
                    else:
                        self.stdout.write(f'   ✅ Productos procesados: {results["processed_products"]}')
                        self.stdout.write(f'   📦 Órdenes generadas: {results["orders_generated"]}')
                        self.stdout.write(f'   📧 Emails enviados: {results["emails_sent"]}')
                        
                        if results['errors']:
                            self.stdout.write(f'   ⚠️  Errores: {len(results["errors"])}')
                            for error in results['errors'][:3]:  # Mostrar solo los primeros 3
                                self.stdout.write(f'      • {error}')
                        
                        total_results['companies_processed'] += 1
                        total_results['total_products_processed'] += results['processed_products']
                        total_results['total_orders_generated'] += results['orders_generated']
                        total_results['total_emails_sent'] += results['emails_sent']
                        total_results['total_errors'] += len(results['errors'])
            
            # Resumen final
            self.stdout.write('\n' + '='*60)
            self.stdout.write('📊 RESUMEN FINAL:')
            self.stdout.write(f'   • Empresas procesadas: {total_results["companies_processed"]}')
            self.stdout.write(f'   • Productos analizados: {total_results["total_products_processed"]}')
            
            if not options['dry_run']:
                self.stdout.write(f'   • Órdenes generadas: {total_results["total_orders_generated"]}')
                self.stdout.write(f'   • Emails enviados: {total_results["total_emails_sent"]}')
                self.stdout.write(f'   • Errores totales: {total_results["total_errors"]}')
            
            self.stdout.write('='*60)
            
            if options['dry_run']:
                self.stdout.write(
                    self.style.WARNING('\n💡 Esto fue una simulación. Use --no-dry-run para ejecutar realmente.')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS('\n🎉 Proceso completado exitosamente!')
                )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'\n❌ Error general: {str(e)}')
            )
    
    def _dry_run_analysis(self, company):
        """Análisis en modo simulación"""
        from django.db.models import Q, F
        from inventory.models import Product
        from inventory.services.purchase_order_service import PurchaseOrderService
        
        try:
            # Buscar productos con stock bajo
            low_stock_products = Product.objects.filter(
                company=company,
                is_active=True
            ).filter(
                Q(stock__lte=F('min_stock')) |
                Q(stock__lte=10)
            ).select_related('supplier')
            
            self.stdout.write(f'   📦 Productos con stock bajo encontrados: {low_stock_products.count()}')
            
            purchase_service = PurchaseOrderService()
            
            for product in low_stock_products[:10]:  # Mostrar solo los primeros 10
                current_stock = product.stock or 0
                min_stock = product.min_stock or 0
                
                # Verificar si ya tiene orden pendiente
                has_pending = purchase_service._has_pending_order(product)
                
                # Calcular cantidad recomendada
                recommended_qty = purchase_service._calculate_order_quantity(product)
                
                status_icon = "⏳" if has_pending else "🆕"
                supplier_info = f" | Proveedor: {product.supplier.name}" if product.supplier else " | Sin proveedor"
                
                self.stdout.write(
                    f'      {status_icon} {product.name[:30]:<30} | '
                    f'Stock: {current_stock:>3}/{min_stock} | '
                    f'Recomendado: {recommended_qty:>3}{supplier_info}'
                )
            
            if low_stock_products.count() > 10:
                self.stdout.write(f'      ... y {low_stock_products.count() - 10} productos más')
                
        except Exception as e:
            self.stdout.write(f'   ❌ Error en análisis: {str(e)}')
