from django.core.management.base import BaseCommand
from django.apps import apps

class Command(BaseCommand):
    help = 'Verificar modelos disponibles en forecasting'

    def handle(self, *args, **options):
        self.stdout.write("=== Modelos en forecasting app ===")
        
        try:
            forecasting_models = apps.get_app_config('forecasting').get_models()
            
            for model in forecasting_models:
                self.stdout.write(f"Modelo: {model.__name__}")
                self.stdout.write(f"  Tabla: {model._meta.db_table}")
                self.stdout.write(f"  Campos: {[f.name for f in model._meta.fields]}")
                self.stdout.write("")
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))
