# Generated migration for data_import

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('authentication', '0001_initial'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='DataImportSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('import_type', models.CharField(choices=[('products', 'Productos'), ('suppliers', 'Proveedores'), ('categories', 'Categorías'), ('customers', 'Clientes'), ('leads', 'Leads'), ('inventory', 'Inventario'), ('transactions', 'Transacciones')], max_length=20)),
                ('status', models.CharField(choices=[('pending', 'Pendiente'), ('mapping', 'Mapeando'), ('processing', 'Procesando'), ('completed', 'Completado'), ('failed', 'Fallido'), ('cancelled', 'Cancelado')], default='pending', max_length=20)),
                ('original_filename', models.CharField(max_length=255)),
                ('file_path', models.CharField(max_length=500)),
                ('file_size', models.BigIntegerField()),
                ('total_rows', models.IntegerField(default=0)),
                ('header_row', models.IntegerField(default=1)),
                ('detected_columns', models.JSONField(default=list)),
                ('processed_rows', models.IntegerField(default=0)),
                ('successful_rows', models.IntegerField(default=0)),
                ('failed_rows', models.IntegerField(default=0)),
                ('error_log', models.JSONField(default=list)),
                ('skip_duplicates', models.BooleanField(default=True)),
                ('update_existing', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='import_sessions', to='authentication.company')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='import_sessions', to='authentication.user')),
            ],
            options={
                'verbose_name': 'Sesión de Importación',
                'verbose_name_plural': 'Sesiones de Importación',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='FieldDefinition',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('import_type', models.CharField(choices=[('products', 'Productos'), ('suppliers', 'Proveedores'), ('categories', 'Categorías'), ('customers', 'Clientes'), ('leads', 'Leads'), ('inventory', 'Inventario'), ('transactions', 'Transacciones')], max_length=20)),
                ('field_name', models.CharField(max_length=100)),
                ('display_name', models.CharField(max_length=200)),
                ('field_type', models.CharField(choices=[('text', 'Texto'), ('number', 'Número'), ('decimal', 'Decimal'), ('date', 'Fecha'), ('datetime', 'Fecha y Hora'), ('boolean', 'Sí/No'), ('email', 'Email'), ('phone', 'Teléfono'), ('choice', 'Lista de opciones'), ('foreign_key', 'Relación')], max_length=20)),
                ('description', models.TextField(blank=True)),
                ('is_required', models.BooleanField(default=False)),
                ('is_unique', models.BooleanField(default=False)),
                ('default_value', models.TextField(blank=True)),
                ('related_model', models.CharField(blank=True, max_length=100)),
                ('lookup_field', models.CharField(blank=True, max_length=100)),
                ('choices', models.JSONField(default=list)),
                ('min_length', models.IntegerField(blank=True, null=True)),
                ('max_length', models.IntegerField(blank=True, null=True)),
                ('min_value', models.DecimalField(blank=True, decimal_places=4, max_digits=15, null=True)),
                ('max_value', models.DecimalField(blank=True, decimal_places=4, max_digits=15, null=True)),
                ('regex_pattern', models.CharField(blank=True, max_length=500)),
                ('order', models.IntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ['import_type', 'order', 'display_name'],
            },
        ),
        migrations.CreateModel(
            name='ImportTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('import_type', models.CharField(choices=[('products', 'Productos'), ('suppliers', 'Proveedores'), ('categories', 'Categorías'), ('customers', 'Clientes'), ('leads', 'Leads'), ('inventory', 'Inventario'), ('transactions', 'Transacciones')], max_length=20)),
                ('column_mappings', models.JSONField(default=dict)),
                ('import_settings', models.JSONField(default=dict)),
                ('is_default', models.BooleanField(default=False)),
                ('usage_count', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='import_templates', to='authentication.company')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='created_templates', to='authentication.user')),
            ],
            options={
                'ordering': ['-usage_count', 'name'],
            },
        ),
        migrations.CreateModel(
            name='ColumnMapping',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source_column', models.CharField(max_length=255)),
                ('source_index', models.IntegerField()),
                ('target_field', models.CharField(max_length=100)),
                ('field_type', models.CharField(max_length=50)),
                ('is_required', models.BooleanField(default=False)),
                ('default_value', models.TextField(blank=True)),
                ('transformation_rules', models.JSONField(default=dict)),
                ('sample_values', models.JSONField(default=list)),
                ('validation_errors', models.JSONField(default=list)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('import_session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='column_mappings', to='data_import.dataimportsession')),
            ],
            options={
                'ordering': ['source_index'],
            },
        ),
        migrations.AddConstraint(
            model_name='importtemplate',
            constraint=models.UniqueConstraint(fields=('company', 'name', 'import_type'), name='unique_template_per_company'),
        ),
        migrations.AddConstraint(
            model_name='fielddefinition',
            constraint=models.UniqueConstraint(fields=('import_type', 'field_name'), name='unique_field_per_import_type'),
        ),
        migrations.AddConstraint(
            model_name='columnmapping',
            constraint=models.UniqueConstraint(fields=('import_session', 'source_column'), name='unique_column_per_session'),
        ),
    ]
