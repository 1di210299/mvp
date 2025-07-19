#!/usr/bin/env python3
"""
Script para crear datos de prueba para los dashboards
"""
import os
import sys
import django

# Setup Django
sys.path.append('/Users/juandiegogutierrezcortez/mvp')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'datalens_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from authentication.models import Company
from inventory.models import Supplier, PurchaseOrder, EmailCampaign, TrackedEmail
from datetime import datetime, timedelta
import random

def create_test_data():
    """Crear datos de prueba"""
    User = get_user_model()
    
    try:
        user = User.objects.get(email='admin@testcompany.com')
        company = user.company
        print(f"✅ Usuario encontrado: {user.email}")
        print(f"✅ Company: {company.name}")
    except User.DoesNotExist:
        print("❌ Usuario admin@testcompany.com no encontrado")
        return False

    # Crear suppliers (no tienen campo company en este modelo)
    suppliers_data = [
        {'name': 'Supplier A', 'email': 'suppliea@example.com', 'phone': '123456789'},
        {'name': 'Supplier B', 'email': 'supplieb@example.com', 'phone': '987654321'},
        {'name': 'Supplier C', 'email': 'suppliec@example.com', 'phone': '555666777'},
    ]

    suppliers = []
    for data in suppliers_data:
        supplier, created = Supplier.objects.get_or_create(
            name=data['name'],
            defaults={
                'email': data['email'],
                'phone': data['phone'],
                'contact_name': f'Contact {data["name"]}',
                'address': f'Address for {data["name"]}',
            }
        )
        suppliers.append(supplier)
        if created:
            print(f"✅ Supplier creado: {supplier.name}")

    # Crear Purchase Orders
    statuses = ['draft', 'sent', 'confirmed', 'in_transit', 'received', 'cancelled']
    priorities = ['low', 'medium', 'high', 'urgent']
    
    for i in range(20):
        order_number = f'PO-{1000 + i}'
        if not PurchaseOrder.objects.filter(order_number=order_number).exists():
            date = datetime.now() - timedelta(days=random.randint(0, 30))
            
            # Necesitamos crear un producto primero
            from inventory.models import Category
            category, _ = Category.objects.get_or_create(
                name='Test Category',
                defaults={'description': 'Test category for purchase orders'}
            )
            
            from inventory.models import Product
            product, _ = Product.objects.get_or_create(
                sku=f'PROD-{1000 + i}',
                defaults={
                    'name': f'Test Product {i+1}',
                    'description': f'Test product {i+1}',
                    'company': company,
                    'category': category,
                    'supplier': random.choice(suppliers),
                    'cost_price': random.uniform(10, 100),
                    'sale_price': random.uniform(15, 150),
                    'stock': random.randint(0, 100),
                    'min_stock': 10,
                    'reorder_point': 15,
                }
            )
            
            po = PurchaseOrder.objects.create(
                company=company,
                order_number=order_number,
                product=product,
                supplier=random.choice(suppliers),
                status=random.choice(statuses),
                priority=random.choice(priorities),
                quantity=random.randint(10, 100),
                unit_price=random.uniform(10, 100),
                total_amount=random.uniform(1000, 10000),
                notes=f'Test purchase order {i+1}',
                created_by=user,
                expected_delivery_date=date + timedelta(days=random.randint(7, 21)),
            )
            print(f"✅ PO creado: {po.order_number}")

    # Crear Email Campaigns
    campaigns = []
    for i in range(3):
        campaign_name = f'Campaign {i+1}'
        campaign, created = EmailCampaign.objects.get_or_create(
            name=campaign_name,
            company=company,
            defaults={
                'description': f'Test campaign {i+1}',
                'is_active': True,
            }
        )
        campaigns.append(campaign)
        if created:
            print(f"✅ Campaign creada: {campaign.name}")

    # Crear TrackedEmails
    email_statuses = ['pending', 'sent', 'delivered', 'opened', 'clicked', 'replied', 'bounced', 'failed']
    recipients = ['recipient1@example.com', 'recipient2@example.com', 'recipient3@example.com']

    for i in range(50):
        tracking_id = f'TRK-{10000 + i}'
        if not TrackedEmail.objects.filter(tracking_id=tracking_id).exists():
            sent_date = datetime.now() - timedelta(days=random.randint(0, 60))
            status = random.choice(email_statuses)
            
            # Determinar fechas basadas en el status
            first_opened_at = None
            first_clicked_at = None
            replied_at = None
            
            if status in ['opened', 'clicked', 'replied']:
                first_opened_at = sent_date + timedelta(hours=random.randint(1, 48))
            
            if status in ['clicked', 'replied']:
                first_clicked_at = first_opened_at + timedelta(minutes=random.randint(5, 120))
            
            if status == 'replied':
                replied_at = first_clicked_at + timedelta(hours=random.randint(1, 24))
            
            email = TrackedEmail.objects.create(
                company=company,
                email_id=f'EMAIL-{10000 + i}',
                tracking_id=tracking_id,
                campaign=random.choice(campaigns),
                recipient_email=random.choice(recipients),
                subject=f'Test Email {i+1} - Purchase Order Follow-up',
                status=status,
                sent_at=sent_date,
                first_opened_at=first_opened_at,
                first_clicked_at=first_clicked_at,
                replied_at=replied_at,
                open_count=random.randint(0, 5) if status in ['opened', 'clicked', 'replied'] else 0,
                click_count=random.randint(0, 3) if status in ['clicked', 'replied'] else 0,
            )
            if i < 5:  # Solo mostrar los primeros 5
                print(f"✅ Email creado: {email.tracking_id}")

    print('\n📊 RESUMEN DE DATOS CREADOS:')
    print(f'   🏢 Suppliers: {Supplier.objects.all().count()}')
    print(f'   📋 Purchase Orders: {PurchaseOrder.objects.filter(company=company).count()}')
    print(f'   📧 Email Campaigns: {EmailCampaign.objects.filter(company=company).count()}')
    print(f'   📨 Tracked Emails: {TrackedEmail.objects.filter(company=company).count()}')
    
    return True

if __name__ == "__main__":
    print("🔧 Creando datos de prueba para dashboards...")
    success = create_test_data()
    if success:
        print("✅ Datos de prueba creados exitosamente!")
    else:
        print("❌ Error al crear datos de prueba")
        sys.exit(1)
