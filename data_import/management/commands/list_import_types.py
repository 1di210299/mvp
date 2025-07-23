"""
Management command para listar tipos de importación disponibles
Usage: python manage.py list_import_types
"""

from django.core.management.base import BaseCommand
from data_import.models import DataImportSession, FieldDefinition

class Command(BaseCommand):
    help = 'Lista todos los tipos de importación disponibles (base + dinámicos)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n🔍 TIPOS DE IMPORTACIÓN DISPONIBLES\n'))
        
        # Tipos base del modelo
        base_types = [choice for choice in DataImportSession.IMPORT_TYPES]
        self.stdout.write(self.style.WARNING('📋 Tipos Base (hardcoded):'))
        for type_code, type_name in base_types:
            field_count = FieldDefinition.objects.filter(import_type=type_code).count()
            self.stdout.write(f'  ✅ {type_code}: {type_name} ({field_count} campos)')
        
        # Tipos dinámicos
        dynamic_types = FieldDefinition.objects.values_list('import_type', flat=True).distinct()
        base_codes = [choice[0] for choice in base_types]
        dynamic_only = [t for t in dynamic_types if t not in base_codes]
        
        if dynamic_only:
            self.stdout.write(self.style.SUCCESS('\n🤖 Tipos Dinámicos (creados por IA):'))
            for type_code in dynamic_only:
                field_count = FieldDefinition.objects.filter(import_type=type_code).count()
                session_count = DataImportSession.objects.filter(import_type=type_code).count()
                self.stdout.write(f'  🆕 {type_code}: ({field_count} campos, {session_count} usos)')
        else:
            self.stdout.write(self.style.WARNING('\n🤖 Tipos Dinámicos: Ninguno encontrado'))
        
        # Estadísticas
        total_types = len(base_types) + len(dynamic_only)
        total_fields = FieldDefinition.objects.count()
        self.stdout.write(self.style.SUCCESS(f'\n📊 RESUMEN:'))
        self.stdout.write(f'  📋 Total tipos: {total_types}')
        self.stdout.write(f'  🏷️  Total campos: {total_fields}')
        self.stdout.write(f'  🎯 Tipos base: {len(base_types)}')
        self.stdout.write(f'  🤖 Tipos dinámicos: {len(dynamic_only)}')
