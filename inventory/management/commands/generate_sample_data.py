#!/usr/bin/env python
"""
Comando personalizado de Django para generar datos de prueba
Usar: python manage.py generate_sample_data
"""

from django.core.management.base import BaseCommand
from django.db import transaction
import sys
import os

# Agregar el directorio raíz al path para importar el script
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from generate_sample_data import main as generate_data
except ImportError:
    # Si no se puede importar, definir una versión simplificada
    def generate_data():
        print("No se pudo importar el script generate_sample_data.py")
        print("Ejecuta: python manage.py shell < generate_sample_data.py")


class Command(BaseCommand):
    help = 'Genera datos de prueba con productos peruanos típicos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Limpiar datos existentes antes de generar nuevos',
        )

    def handle(self, *args, **options):
        if options['clean']:
            self.stdout.write('Limpiando datos existentes...')
            # Aquí podrías llamar al script de limpieza
            try:
                from clean_sample_data import clean_sample_data
                clean_sample_data()
            except ImportError:
                self.stdout.write(
                    self.style.WARNING('No se pudo importar clean_sample_data.py')
                )

        self.stdout.write('Generando datos de prueba...')
        
        try:
            with transaction.atomic():
                generate_data()
            self.stdout.write(
                self.style.SUCCESS('¡Datos generados exitosamente!')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error al generar datos: {e}')
            )
            raise
