"""
Comando para entrenar modelos de ML automáticamente
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import timedelta
import logging

from forecasting.models import ForecastModel
from authentication.models import Company
from forecasting.services.ml_model_service import MLModelService
from inventory.models import Product

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Entrena modelos de machine learning automáticamente'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--company-id',
            type=int,
            help='ID de empresa específica para entrenar modelos'
        )
        parser.add_argument(
            '--model-id',
            type=int,
            help='ID de modelo específico para entrenar'
        )
        parser.add_argument(
            '--algorithm',
            type=str,
            choices=['prophet', 'arima', 'ensemble', 'auto'],
            default='auto',
            help='Algoritmo específico a usar'
        )
        parser.add_argument(
            '--optimize-hyperparameters',
            action='store_true',
            help='Optimizar hiperparámetros automáticamente'
        )
        parser.add_argument(
            '--force-retrain',
            action='store_true',
            help='Forzar re-entrenamiento aunque el modelo esté actualizado'
        )
        parser.add_argument(
            '--create-models',
            action='store_true',
            help='Crear modelos automáticamente para empresas sin modelos'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Iniciando entrenamiento de modelos ML...')
        )
        
        try:
            if options['model_id']:
                # Entrena modelo específico
                self._train_specific_model(options)
            elif options['company_id']:
                # Entrena modelos de empresa específica
                self._train_company_models(options)
            else:
                # Entrena todos los modelos necesarios
                self._train_all_models(options)
                
        except Exception as e:
            logger.error(f"Error en entrenamiento de modelos: {str(e)}")
            raise CommandError(f'Error: {str(e)}')
    
    def _train_specific_model(self, options):
        """Entrena un modelo específico"""
        model_id = options['model_id']
        algorithm = options['algorithm']
        optimize = options['optimize_hyperparameters']
        
        try:
            forecast_model = ForecastModel.objects.get(id=model_id)
            
            self.stdout.write(f"Entrenando modelo {model_id}: {forecast_model.name}")
            
            ml_service = MLModelService()
            
            if algorithm == 'auto':
                # Re-entrena con el algoritmo actual del modelo
                updated_model = ml_service.retrain_model(
                    model_id=model_id,
                    optimize_hyperparameters=optimize
                )
            else:
                # Entrena con algoritmo específico
                updated_model = ml_service.create_and_train_model(
                    company=forecast_model.company,
                    name=f"{forecast_model.name} - {algorithm}",
                    description=f"Re-entrenado con {algorithm}",
                    model_type=algorithm,
                    products=list(forecast_model.products.all()),
                    categories=list(forecast_model.categories.all()),
                    optimize_hyperparameters=optimize,
                    forecast_horizon_days=forecast_model.forecast_horizon_days,
                    training_period_days=forecast_model.training_period_days
                )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Modelo {model_id} entrenado exitosamente. '
                    f'MAE: {updated_model.mae}, MAPE: {updated_model.mape}%'
                )
            )
            
        except ForecastModel.DoesNotExist:
            raise CommandError(f'Modelo {model_id} no encontrado')
    
    def _train_company_models(self, options):
        """Entrena modelos de una empresa específica"""
        company_id = options['company_id']
        force_retrain = options['force_retrain']
        create_models = options['create_models']
        
        try:
            company = Company.objects.get(id=company_id)
            
            self.stdout.write(f"Entrenando modelos para empresa: {company.name}")
            
            # Obtiene modelos existentes
            existing_models = ForecastModel.objects.filter(company=company)
            
            if not existing_models.exists() and create_models:
                self._create_automatic_models(company, options)
                existing_models = ForecastModel.objects.filter(company=company)
            
            models_trained = 0
            
            for model in existing_models:
                try:
                    # Verifica si necesita entrenamiento
                    if self._needs_training(model) or force_retrain:
                        self.stdout.write(f"  Entrenando: {model.name}")
                        
                        ml_service = MLModelService()
                        updated_model = ml_service.retrain_model(
                            model_id=model.id,
                            optimize_hyperparameters=options['optimize_hyperparameters']
                        )
                        
                        models_trained += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'    ✓ Completado. MAE: {updated_model.mae:.2f}'
                            )
                        )
                    else:
                        self.stdout.write(f"  Saltando: {model.name} (no necesita entrenamiento)")
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'    ✗ Error entrenando {model.name}: {str(e)}')
                    )
            
            self.stdout.write(
                self.style.SUCCESS(f'Entrenados {models_trained} modelos para {company.name}')
            )
            
        except Company.DoesNotExist:
            raise CommandError(f'Empresa {company_id} no encontrada')
    
    def _train_all_models(self, options):
        """Entrena todos los modelos que necesitan entrenamiento"""
        force_retrain = options['force_retrain']
        create_models = options['create_models']
        
        self.stdout.write("Entrenando todos los modelos necesarios...")
        
        # Obtiene todas las empresas activas
        companies = Company.objects.filter(is_active=True)
        
        total_trained = 0
        
        for company in companies:
            self.stdout.write(f"\nProcesando empresa: {company.name}")
            
            # Obtiene modelos de la empresa
            models = ForecastModel.objects.filter(company=company)
            
            if not models.exists() and create_models:
                self._create_automatic_models(company, options)
                models = ForecastModel.objects.filter(company=company)
            
            company_trained = 0
            
            for model in models:
                try:
                    if self._needs_training(model) or force_retrain:
                        self.stdout.write(f"  Entrenando: {model.name}")
                        
                        ml_service = MLModelService()
                        updated_model = ml_service.retrain_model(
                            model_id=model.id,
                            optimize_hyperparameters=options['optimize_hyperparameters']
                        )
                        
                        company_trained += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'    ✓ MAE: {updated_model.mae:.2f}, MAPE: {updated_model.mape:.2f}%'
                            )
                        )
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'    ✗ Error: {str(e)}')
                    )
            
            total_trained += company_trained
            self.stdout.write(f"  Modelos entrenados: {company_trained}")
        
        self.stdout.write(
            self.style.SUCCESS(f'\nTotal de modelos entrenados: {total_trained}')
        )
    
    def _create_automatic_models(self, company, options):
        """Crea modelos automáticos para una empresa"""
        self.stdout.write(f"  Creando modelos automáticos para {company.name}...")
        
        try:
            # Verifica que hay productos con datos suficientes
            from inventory.models import Transaction
            
            products_with_data = []
            for product in company.products.all():
                transaction_count = Transaction.objects.filter(
                    product=product,
                    transaction_date__gte=timezone.now().date() - timedelta(days=365)
                ).count()
                
                if transaction_count >= 30:
                    products_with_data.append(product)
            
            if not products_with_data:
                self.stdout.write(
                    self.style.WARNING(f"    No hay productos con suficientes datos para {company.name}")
                )
                return
            
            # Crea modelo general
            ml_service = MLModelService()
            
            general_model = ml_service.create_and_train_model(
                company=company,
                name="Modelo General - Automático",
                description="Modelo automático para pronósticos generales",
                model_type=options['algorithm'],
                products=products_with_data,
                optimize_hyperparameters=options['optimize_hyperparameters'],
                forecast_horizon_days=30,
                training_period_days=365
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"    ✓ Modelo general creado: MAE {general_model.mae:.2f}"
                )
            )
            
            # Crea modelos por categoría si hay múltiples categorías
            categories = set(p.category for p in products_with_data if p.category)
            
            if len(categories) > 1:
                for category in categories:
                    category_products = [p for p in products_with_data if p.category == category]
                    
                    if len(category_products) >= 5:  # Mínimo 5 productos por categoría
                        try:
                            category_model = ml_service.create_and_train_model(
                                company=company,
                                name=f"Modelo {category.name} - Automático",
                                description=f"Modelo automático para categoría {category.name}",
                                model_type=options['algorithm'],
                                products=category_products,
                                optimize_hyperparameters=options['optimize_hyperparameters'],
                                forecast_horizon_days=30,
                                training_period_days=365
                            )
                            
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"    ✓ Modelo {category.name} creado: MAE {category_model.mae:.2f}"
                                )
                            )
                            
                        except Exception as e:
                            self.stdout.write(
                                self.style.ERROR(f"    ✗ Error creando modelo para {category.name}: {str(e)}")
                            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"    ✗ Error creando modelos automáticos: {str(e)}")
            )
    
    def _needs_training(self, model):
        """Verifica si un modelo necesita entrenamiento"""
        # Modelo nunca entrenado
        if model.status in ['training', 'failed'] or not model.training_completed_at:
            return True
        
        # Modelo muy antiguo
        days_since_training = (timezone.now() - model.training_completed_at).days
        if days_since_training > 7:  # Re-entrena cada semana
            return True
        
        # Modelo con métricas pobres
        if model.mape and model.mape > 25:  # MAPE > 25%
            return True
        
        return False
