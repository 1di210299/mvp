import random
from datetime import datetime, timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from authentication.models import Company, User
from inventory.models import Product, Location, InventoryItem, Transaction
import json

class Command(BaseCommand):
    help = 'Create sample data for the forecasting system (historical data only)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating sample historical data...'))
        
        # Get or create companies
        companies = self.create_companies()
        
        # Create locations
        locations = self.create_locations(companies)
        
        # Create products
        products = self.create_products(companies)
        
        # Create inventory records
        self.create_inventory_records(products, locations)
        
        # Create historical transactions (this is what ML models need)
        self.create_historical_transactions(products, locations)
        
        self.stdout.write(self.style.SUCCESS('Sample historical data created successfully!'))
        self.stdout.write(self.style.WARNING('Next steps:'))
        self.stdout.write('1. Use the API to train ML models: POST /api/forecasting/models/')
        self.stdout.write('2. Generate forecasts: POST /api/forecasting/predict/')
        self.stdout.write('3. View results in the frontend')

    def create_companies(self):
        companies = []
        existing_companies = Company.objects.all()
        
        if existing_companies:
            self.stdout.write(f'Using existing {len(existing_companies)} companies')
            return list(existing_companies)
        
        company_names = [
            'TechCorp Solutions',
            'Global Electronics Inc',
            'Industrial Supply Co',
            'Retail Distribution Ltd'
        ]
        
        for name in company_names:
            company, created = Company.objects.get_or_create(
                name=name,
                defaults={
                    'email': f'info@{name.lower().replace(" ", "").replace(".", "")}.com',
                    'phone': f'+1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}',
                    'address': f'{random.randint(100, 9999)} Business Ave, City, State 12345'
                }
            )
            companies.append(company)
            if created:
                self.stdout.write(f'Created company: {name}')
            
        return companies

    def create_locations(self, companies):
        locations = []
        location_data = [
            ('Main Warehouse', 'WH-001'),
            ('Distribution Center', 'DC-001'),
            ('Retail Store North', 'ST-001'),
            ('Retail Store South', 'ST-002'),
            ('Customer Service Center', 'CS-001')
        ]
        
        for company in companies:
            for name, code in location_data:
                location, created = Location.objects.get_or_create(
                    name=f'{company.name} - {name}',
                    code=f'{code}-{company.id}',
                    company=company,
                    defaults={
                        'warehouse': f'{company.name} Warehouse',
                        'zone': 'Zone A',
                        'aisle': f'A{random.randint(1, 10)}',
                        'rack': f'R{random.randint(1, 20)}',
                        'shelf': f'S{random.randint(1, 5)}',
                        'is_active': True
                    }
                )
                locations.append(location)
                if created:
                    self.stdout.write(f'Created location: {location.name}')
                
        return locations

    def create_products(self, companies):
        products = []
        product_data = [
            ('Laptop Pro 15"', 'ELECTRONICS', 1299.99, 'SKU-LAP-001'),
            ('Wireless Mouse', 'ELECTRONICS', 29.99, 'SKU-MOU-002'),
            ('USB-C Cable', 'ELECTRONICS', 19.99, 'SKU-CAB-003'),
            ('Office Chair', 'FURNITURE', 199.99, 'SKU-CHR-004'),
            ('Desk Lamp', 'FURNITURE', 49.99, 'SKU-LAM-005'),
            ('Monitor 24"', 'ELECTRONICS', 299.99, 'SKU-MON-006'),
            ('Keyboard Mechanical', 'ELECTRONICS', 89.99, 'SKU-KEY-007'),
            ('Smartphone Case', 'ACCESSORIES', 24.99, 'SKU-CAS-008'),
            ('Power Bank', 'ELECTRONICS', 39.99, 'SKU-POW-009'),
            ('Headphones', 'ELECTRONICS', 79.99, 'SKU-HEA-010'),
            ('Tablet 10"', 'ELECTRONICS', 399.99, 'SKU-TAB-011'),
            ('Printer', 'ELECTRONICS', 149.99, 'SKU-PRI-012'),
            ('External HDD', 'ELECTRONICS', 89.99, 'SKU-HDD-013'),
            ('Router WiFi', 'ELECTRONICS', 119.99, 'SKU-ROU-014'),
            ('Smart Watch', 'ELECTRONICS', 249.99, 'SKU-WAT-015')
        ]
        
        for company in companies:
            for name, category, price, sku in product_data:
                product, created = Product.objects.get_or_create(
                    name=f'{name} - {company.name}',
                    sku=f'{sku}-{company.id}',
                    company=company,
                    defaults={
                        'description': f'High-quality {name.lower()} for professional use',
                        'cost_price': Decimal(str(price * 0.6)),
                        'sale_price': Decimal(str(price)),
                        'unit': 'unit',
                        'is_active': True,
                        'min_stock': random.randint(10, 50),
                        'max_stock': random.randint(100, 500),
                        'reorder_point': random.randint(20, 80)
                    }
                )
                products.append(product)
                if created:
                    self.stdout.write(f'Created product: {product.name}')
                
        return products

    def create_inventory_records(self, products, locations):
        created_count = 0
        for product in products:
            company_locations = [loc for loc in locations if loc.company == product.company]
            
            for location in company_locations[:3]:  # Use first 3 locations per company
                quantity = random.randint(50, 500)
                inventory, created = InventoryItem.objects.get_or_create(
                    product=product,
                    location=location,
                    defaults={
                        'quantity': quantity,
                        'reserved_quantity': random.randint(0, quantity // 10),
                        'unit_cost': product.cost_price,
                        'batch_number': f'BATCH-{random.randint(1000, 9999)}',
                        'is_active': True
                    }
                )
                if created:
                    created_count += 1
                    
        self.stdout.write(f'Created {created_count} inventory records')

    def create_historical_transactions(self, products, locations):
        # Create transactions for the last 18 months (more data for better ML training)
        start_date = timezone.now() - timedelta(days=540)  # 18 months of data
        transaction_types = ['purchase', 'sale', 'adjustment', 'transfer']
        created_count = 0
        
        for product in products:
            company_locations = [loc for loc in locations if loc.company == product.company]
            
            # Create more realistic transaction patterns
            # More transactions for popular items (electronics), fewer for furniture
            if 'ELECTRONICS' in product.name:
                num_transactions = random.randint(100, 200)
            elif 'FURNITURE' in product.name:
                num_transactions = random.randint(30, 60)
            else:
                num_transactions = random.randint(50, 100)
                
            for _ in range(num_transactions):
                transaction_date = start_date + timedelta(
                    days=random.randint(0, 540),
                    hours=random.randint(8, 18),  # Business hours
                    minutes=random.randint(0, 59)
                )
                
                # Create seasonal patterns
                month = transaction_date.month
                seasonal_multiplier = 1.0
                if month in [11, 12]:  # Holiday season
                    seasonal_multiplier = 1.5
                elif month in [6, 7, 8]:  # Summer
                    seasonal_multiplier = 1.2
                elif month in [1, 2]:  # Post-holiday
                    seasonal_multiplier = 0.8
                
                transaction_type = random.choice(transaction_types)
                location = random.choice(company_locations)
                
                # Generate realistic quantities with seasonal variation
                if transaction_type == 'purchase':
                    base_quantity = random.randint(50, 200)
                    quantity = int(base_quantity * seasonal_multiplier)
                elif transaction_type == 'sale':
                    base_quantity = random.randint(1, 30)
                    quantity = -int(base_quantity * seasonal_multiplier)
                elif transaction_type == 'adjustment':
                    quantity = random.randint(-10, 10)
                else:  # transfer
                    quantity = random.randint(-50, 50)
                
                Transaction.objects.create(
                    company=product.company,
                    product=product,
                    location=location,
                    transaction_type=transaction_type,
                    quantity=quantity,
                    unit_cost=product.cost_price,
                    reference_number=f'REF-{random.randint(100000, 999999)}',
                    batch_number=f'BATCH-{random.randint(1000, 9999)}',
                    notes=f'Historical {transaction_type} transaction for {product.name}',
                    transaction_date=transaction_date,
                    user=None  # Historical data
                )
                created_count += 1
                
        self.stdout.write(f'Created {created_count} historical transactions')
        self.stdout.write(f'Transaction date range: {start_date.date()} to {timezone.now().date()}')