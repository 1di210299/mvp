"""
Comando para inicializar las definiciones de campos de importación
"""
from django.core.management.base import BaseCommand
from data_import.models import FieldDefinition, FIELD_DEFINITIONS


class Command(BaseCommand):
    help = 'Inicializa las definiciones de campos para importación de datos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Fuerza la recreación de todas las definiciones',
        )

    def handle(self, *args, **options):
        force = options['force']
        
        if force:
            self.stdout.write('🗑️  Eliminando definiciones existentes...')
            FieldDefinition.objects.all().delete()
        
        created_count = 0
        updated_count = 0
        
        for import_type, fields in FIELD_DEFINITIONS.items():
            self.stdout.write(f'\n📝 Procesando campos para: {import_type}')
            
            for order, field_data in enumerate(fields):
                field_name = field_data['field_name']
                
                # Verificar si ya existe
                field_def, created = FieldDefinition.objects.get_or_create(
                    import_type=import_type,
                    field_name=field_name,
                    defaults={
                        'display_name': field_data['display_name'],
                        'field_type': field_data['field_type'],
                        'description': field_data.get('description', ''),
                        'is_required': field_data.get('is_required', False),
                        'is_unique': field_data.get('is_unique', False),
                        'default_value': field_data.get('default_value', ''),
                        'related_model': field_data.get('related_model', ''),
                        'lookup_field': field_data.get('lookup_field', ''),
                        'choices': field_data.get('choices', []),
                        'min_length': field_data.get('min_length'),
                        'max_length': field_data.get('max_length'),
                        'min_value': field_data.get('min_value'),
                        'max_value': field_data.get('max_value'),
                        'regex_pattern': field_data.get('regex_pattern', ''),
                        'order': order,
                        'is_active': True
                    }
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(f'  ✅ Creado: {field_data["display_name"]}')
                else:
                    # Actualizar campos existentes si force está habilitado
                    if force:
                        for key, value in {
                            'display_name': field_data['display_name'],
                            'field_type': field_data['field_type'],
                            'description': field_data.get('description', ''),
                            'is_required': field_data.get('is_required', False),
                            'is_unique': field_data.get('is_unique', False),
                            'default_value': field_data.get('default_value', ''),
                            'related_model': field_data.get('related_model', ''),
                            'lookup_field': field_data.get('lookup_field', ''),
                            'choices': field_data.get('choices', []),
                            'min_length': field_data.get('min_length'),
                            'max_length': field_data.get('max_length'),
                            'min_value': field_data.get('min_value'),
                            'max_value': field_data.get('max_value'),
                            'regex_pattern': field_data.get('regex_pattern', ''),
                            'order': order,
                            'is_active': True
                        }.items():
                            setattr(field_def, key, value)
                        field_def.save()
                        updated_count += 1
                        self.stdout.write(f'  🔄 Actualizado: {field_data["display_name"]}')
                    else:
                        self.stdout.write(f'  ⏭️  Ya existe: {field_data["display_name"]}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n🎉 Proceso completado!\n'
                f'   • Creados: {created_count} campos\n'
                f'   • Actualizados: {updated_count} campos\n'
                f'   • Total tipos de importación: {len(FIELD_DEFINITIONS)}'
            )
        )