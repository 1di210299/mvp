from django.core.management.base import BaseCommand
from django.utils import timezone
from reports.models import ReportTemplate
from authentication.models import Company, User


class Command(BaseCommand):
    help = 'Creates default report templates for all companies'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--company-id',
            type=int,
            help='Create templates only for specific company ID',
        )
    
    def handle(self, *args, **options):
        self.stdout.write('Creating default report templates...')
        
        # Get companies to create templates for
        if options['company_id']:
            companies = Company.objects.filter(id=options['company_id'])
        else:
            companies = Company.objects.filter(is_active=True)
        
        if not companies.exists():
            self.stdout.write(
                self.style.WARNING('No companies found to create templates for.')
            )
            return
        
        # Default template configurations
        default_templates = [
            {
                'id': 1,
                'name': 'Reporte de Inventario',
                'description': 'Resumen completo del estado actual del inventario',
                'report_type': 'inventory_summary',
                'default_format': 'pdf',
                'frequency': 'on_demand',
                'is_system_template': True
            },
            {
                'id': 2,
                'name': 'Reporte de Ventas',
                'description': 'Análisis de ventas y movimientos de productos',
                'report_type': 'stock_movement',
                'default_format': 'excel',
                'frequency': 'on_demand',
                'is_system_template': True
            },
            {
                'id': 3,
                'name': 'Reporte Financiero',
                'description': 'Análisis de costos y valoración del inventario',
                'report_type': 'cost_analysis',
                'default_format': 'pdf',
                'frequency': 'on_demand',
                'is_system_template': True
            },
            {
                'id': 4,
                'name': 'Reporte de Movimientos',
                'description': 'Detalle de entradas, salidas y ajustes de inventario',
                'report_type': 'stock_movement',
                'default_format': 'excel',
                'frequency': 'on_demand',
                'is_system_template': True
            },
            {
                'id': 5,
                'name': 'Reporte de Pronósticos',
                'description': 'Análisis de precisión de pronósticos de demanda',
                'report_type': 'forecast_accuracy',
                'default_format': 'pdf',
                'frequency': 'on_demand',
                'is_system_template': True
            }
        ]
        
        created_count = 0
        for company in companies:
            self.stdout.write(f'Processing company: {company.name}')
            
            # Get a user from this company to set as created_by
            admin_user = company.users.filter(is_staff=True).first()
            if not admin_user:
                admin_user = company.users.first()
            
            for template_config in default_templates:
                # Check if template already exists for this company
                existing = ReportTemplate.objects.filter(
                    company=company,
                    name=template_config['name']
                ).first()
                
                if existing:
                    self.stdout.write(
                        f'  - Template "{template_config["name"]}" already exists (ID: {existing.id})'
                    )
                    continue
                
                # Create the template
                template = ReportTemplate.objects.create(
                    company=company,
                    name=template_config['name'],
                    description=template_config['description'],
                    report_type=template_config['report_type'],
                    default_format=template_config['default_format'],
                    frequency=template_config['frequency'],
                    is_system_template=template_config['is_system_template'],
                    is_active=True,
                    created_by=admin_user,
                    default_filters={},
                    columns_config=[],
                    charts_config=[],
                    grouping_config={},
                    sorting_config=[]
                )
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  ✓ Created template "{template.name}" (ID: {template.id})'
                    )
                )
                created_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully created {created_count} report templates!'
            )
        )
        
        if created_count > 0:
            self.stdout.write(
                '\nYou can now generate reports from the frontend. The templates are mapped as follows:'
            )
            self.stdout.write('  - inventory: Uses "Reporte de Inventario" template')
            self.stdout.write('  - sales: Uses "Reporte de Ventas" template') 
            self.stdout.write('  - financial: Uses "Reporte Financiero" template')
            self.stdout.write('  - movement: Uses "Reporte de Movimientos" template')
            self.stdout.write('  - forecast: Uses "Reporte de Pronósticos" template')