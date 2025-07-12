from django.core.management.base import BaseCommand
from django.db import transaction
from forecasting.models import ForecastModel
from forecasting.services.ml_model_service import MLModelService
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Prueba y valida modelos ML individuales'

    def add_arguments(self, parser):
        parser.add_argument('--model-id', type=int, help='ID específico del modelo a probar')
        parser.add_argument('--validate-db', action='store_true', help='Validar que se guarden correctamente en DB')
        parser.add_argument('--test-predictions', action='store_true', help='Probar predicciones')

    def handle(self, *args, **options):
        service = MLModelService()
        
        if options['model_id']:
            models = ForecastModel.objects.filter(id=options['model_id'])
        else:
            models = ForecastModel.objects.all()[:5]  # Probar solo 5 modelos
            
        for model in models:
            self.stdout.write(f"\n=== Probando modelo: {model.name} (ID: {model.id}) ===")
            
            try:
                # 1. Entrenar modelo
                self.stdout.write("1. Entrenando modelo...")
                with transaction.atomic():
                    success = service.retrain_model(model.id)
                    
                if success:
                    model.refresh_from_db()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✓ Entrenado exitosamente. MAE: {model.mae}, MAPE: {model.mape}"
                        )
                    )
                    
                    # 2. Validar datos en DB
                    if options['validate_db']:
                        self.stdout.write("2. Validando datos en base de datos...")
                        self._validate_database_fields(model)
                    
                    # 3. Probar predicciones
                    if options['test_predictions']:
                        self.stdout.write("3. Probando predicciones...")
                        self._test_predictions(model, service)
                        
                else:
                    self.stdout.write(self.style.ERROR(f"✗ Error entrenando modelo"))
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ Excepción: {str(e)}"))
                
    def _validate_database_fields(self, model):
        """Valida que los campos se guardaron correctamente"""
        issues = []
        
        if model.mae is None:
            issues.append("MAE es None")
        elif model.mae < 0:
            issues.append("MAE es negativo")
            
        if model.mape is not None and model.mape < 0:
            issues.append("MAPE es negativo")
            
        if model.status != 'trained':
            issues.append(f"Status incorrecto: {model.status}")
            
        if model.training_completed_at is None:
            issues.append("training_completed_at es None")
            
        if issues:
            self.stdout.write(self.style.ERROR(f"  ✗ Problemas encontrados: {', '.join(issues)}"))
        else:
            self.stdout.write(self.style.SUCCESS("  ✓ Todos los campos válidos"))
            
    def _test_predictions(self, model, service):
        """Prueba que el modelo puede hacer predicciones"""
        try:
            # Intentar hacer una predicción
            predictions = service.generate_forecast(model.id, days_ahead=7)
            
            if predictions and len(predictions) > 0:
                self.stdout.write(self.style.SUCCESS(f"  ✓ Predicción exitosa: {len(predictions)} días"))
                self.stdout.write(f"    Ejemplo: {predictions[0]}")
            else:
                self.stdout.write(self.style.ERROR("  ✗ Predicción vacía"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  ✗ Error en predicción: {str(e)}"))
