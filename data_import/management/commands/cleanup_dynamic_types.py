"""
Management command para limpiar tipos dinámicos no utilizados
Usage: python manage.py cleanup_dynamic_types
"""

from django.core.management.base import BaseCommand
from data_import.models import DataImportSession, FieldDefinition

class Command(BaseCommand):
    help = 'Limpia tipos dinámicos que no han sido utilizados'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Solo mostrar qué se eliminaría sin hacer cambios',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar eliminación sin confirmación',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n🧹 LIMPIEZA DE TIPOS DINÁMICOS\n'))
        
        # Encontrar tipos dinámicos sin uso
        base_codes = [choice[0] for choice in DataImportSession.IMPORT_TYPES]
        dynamic_types = FieldDefinition.objects.values_list('import_type', flat=True).distinct()
        dynamic_only = [t for t in dynamic_types if t not in base_codes]
        
        unused_types = []
        for type_code in dynamic_only:
            session_count = DataImportSession.objects.filter(import_type=type_code).count()
            if session_count == 0:
                unused_types.append(type_code)
        
        if not unused_types:
            self.stdout.write(self.style.SUCCESS('✅ No hay tipos dinámicos sin usar'))
            return
        
        self.stdout.write(self.style.WARNING(f'🗑️  Tipos dinámicos sin usar encontrados: {len(unused_types)}'))
        
        for type_code in unused_types:
            field_count = FieldDefinition.objects.filter(import_type=type_code).count()
            self.stdout.write(f'  🗑️  {type_code}: {field_count} campos')
        
        if options['dry_run']:
            self.stdout.write(self.style.SUCCESS('\n🔍 DRY RUN: No se realizaron cambios'))
            return
        
        if not options['force']:
            confirm = input('\n¿Desea eliminar estos tipos dinámicos? (y/N): ')
            if confirm.lower() != 'y':
                self.stdout.write(self.style.SUCCESS('❌ Operación cancelada'))
                return
        
        # Eliminar campos de tipos no usados
        deleted_count = 0
        for type_code in unused_types:
            count = FieldDefinition.objects.filter(import_type=type_code).delete()[0]
            deleted_count += count
            self.stdout.write(self.style.SUCCESS(f'  ✅ Eliminado tipo: {type_code}'))
        
        self.stdout.write(self.style.SUCCESS(f'\n🎉 Limpieza completada: {deleted_count} campos eliminados'))
