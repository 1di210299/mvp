from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from authentication.models import Company
import getpass


class Command(BaseCommand):
    help = 'Crear un superusuario con empresa asociada'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Nombre de usuario')
        parser.add_argument('--email', type=str, help='Email del usuario')
        parser.add_argument('--company-name', type=str, help='Nombre de la empresa')
        parser.add_argument('--company-ruc', type=str, help='RUC de la empresa')

    def handle(self, *args, **options):
        User = get_user_model()
        
        # Obtener datos del usuario
        username = options.get('username')
        if not username:
            username = input('Nombre de usuario: ')
        
        email = options.get('email')
        if not email:
            email = input('Email: ')
        
        # Obtener datos de la empresa
        company_name = options.get('company_name')
        if not company_name:
            company_name = input('Nombre de la empresa: ')
        
        company_ruc = options.get('company_ruc')
        if not company_ruc:
            company_ruc = input('RUC de la empresa: ')
        
        # Solicitar contraseña
        password = getpass.getpass('Password: ')
        password_confirm = getpass.getpass('Password (again): ')
        
        if password != password_confirm:
            self.stdout.write(
                self.style.ERROR('Las contraseñas no coinciden')
            )
            return
        
        try:
            # Crear o obtener la empresa
            company, created = Company.objects.get_or_create(
                ruc=company_ruc,
                defaults={
                    'name': company_name,
                    'address': 'Dirección por definir',
                    'email': email,
                    'subscription_type': 'premium'  # Superusuario tendrá acceso premium
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Empresa "{company.name}" creada exitosamente')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Empresa "{company.name}" ya existe, usando la existente')
                )
            
            # Crear el superusuario
            if User.objects.filter(username=username).exists():
                self.stdout.write(
                    self.style.ERROR(f'El usuario "{username}" ya existe')
                )
                return
            
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                company=company,
                role='superadmin'
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'Superusuario "{username}" creado exitosamente')
            )
            self.stdout.write(
                self.style.SUCCESS(f'Empresa asociada: "{company.name}"')
            )
            self.stdout.write(
                self.style.SUCCESS('El usuario puede acceder al panel de administración en /admin/')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error al crear el superusuario: {str(e)}')
            )
