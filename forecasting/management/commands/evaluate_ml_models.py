"""
Comando para evaluar modelos de ML
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
import json
import logging

from forecasting.models import ForecastModel
from authentication.models import Company
from forecasting.services.evaluation_service import EvaluationService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Evalúa el rendimiento de modelos de machine learning'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--company-id',
            type=int,
            help='ID de empresa específica para evaluar'
        )
        parser.add_argument(
            '--model-id',
            type=int,
            help='ID de modelo específico para evaluar'
        )
        parser.add_argument(
            '--evaluation-days',
            type=int,
            default=30,
            help='Días de evaluación hacia atrás (default: 30)'
        )
        parser.add_argument(
            '--compare-models',
            action='store_true',
            help='Compara múltiples modelos de la misma empresa'
        )
        parser.add_argument(
            '--realtime-accuracy',
            action='store_true',
            help='Evalúa precisión en tiempo real comparando con datos reales'
        )
        parser.add_argument(
            '--generate-report',
            action='store_true',
            help='Genera reporte completo de rendimiento'
        )
        parser.add_argument(
            '--output-file',
            type=str,
            help='Archivo para guardar resultados en formato JSON'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Iniciando evaluación de modelos ML...')
        )
        
        try:
            evaluation_service = EvaluationService()
            results = {}
            
            if options['model_id']:
                # Evalúa modelo específico
                results = self._evaluate_specific_model(evaluation_service, options)
            elif options['company_id']:
                # Evalúa modelos de empresa específica
                results = self._evaluate_company_models(evaluation_service, options)
            else:
                # Evalúa todos los modelos
                results = self._evaluate_all_models(evaluation_service, options)
            
            # Guarda resultados en archivo si se especifica
            if options['output_file']:
                self._save_results(results, options['output_file'])
                
        except Exception as e:
            logger.error(f"Error en evaluación de modelos: {str(e)}")
            raise CommandError(f'Error: {str(e)}')
    
    def _evaluate_specific_model(self, evaluation_service, options):
        """Evalúa un modelo específico"""
        model_id = options['model_id']
        evaluation_days = options['evaluation_days']
        
        try:
            forecast_model = ForecastModel.objects.get(id=model_id)
            
            self.stdout.write(f"Evaluando modelo {model_id}: {forecast_model.name}")
            
            results = {}
            
            if options['realtime_accuracy']:
                # Evaluación en tiempo real
                realtime_results = evaluation_service.evaluate_forecast_accuracy_realtime(
                    model_id=model_id,
                    days_back=evaluation_days
                )
                results['realtime_accuracy'] = realtime_results
                
                if 'error' not in realtime_results:
                    summary = realtime_results['summary_metrics']
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Precisión en tiempo real:\n"
                            f"  MAE promedio: {summary['average_absolute_error']:.2f}\n"
                            f"  MAPE promedio: {summary['average_percentage_error']:.2f}%\n"
                            f"  Cobertura intervalos: {summary['interval_coverage_percentage']:.1f}%\n"
                            f"  Score de precisión: {summary['accuracy_score']:.1f}"
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f"Error en evaluación tiempo real: {realtime_results['error']}")
                    )
            
            # Evaluación con datos históricos
            historical_results = evaluation_service.evaluate_model_accuracy(
                model_id=model_id,
                evaluation_period_days=evaluation_days
            )
            results['historical_accuracy'] = historical_results
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"Precisión histórica:\n"
                    f"  MAE: {historical_results['mae']:.2f}\n"
                    f"  MAPE: {historical_results['mape']:.2f}%\n"
                    f"  RMSE: {historical_results['rmse']:.2f}\n"
                    f"  R²: {historical_results['r2']:.4f}\n"
                    f"  Precisión direccional: {historical_results.get('directional_accuracy', 0):.1f}%"
                )
            )
            
            return results
            
        except ForecastModel.DoesNotExist:
            raise CommandError(f'Modelo {model_id} no encontrado')
    
    def _evaluate_company_models(self, evaluation_service, options):
        """Evalúa modelos de una empresa específica"""
        company_id = options['company_id']
        
        try:
            company = Company.objects.get(id=company_id)
            
            self.stdout.write(f"Evaluando modelos de empresa: {company.name}")
            
            # Obtiene modelos activos de la empresa
            models = ForecastModel.objects.filter(
                company=company,
                status='active'
            )
            
            if not models.exists():
                self.stdout.write(
                    self.style.WARNING(f"No hay modelos activos para {company.name}")
                )
                return {}
            
            results = {}
            
            if options['generate_report']:
                # Genera reporte completo
                report = evaluation_service.generate_model_performance_report(
                    company_id=company_id,
                    period_days=options['evaluation_days']
                )
                results['performance_report'] = report
                
                self._display_performance_report(report)
            
            if options['compare_models'] and len(models) > 1:
                # Compara modelos
                model_ids = list(models.values_list('id', flat=True))
                comparison = evaluation_service.compare_models_performance(
                    model_ids=model_ids,
                    evaluation_period_days=options['evaluation_days']
                )
                results['models_comparison'] = comparison
                
                self._display_models_comparison(comparison)
            
            # Evalúa cada modelo individualmente
            individual_results = {}
            for model in models:
                try:
                    self.stdout.write(f"  Evaluando: {model.name}")
                    
                    model_results = evaluation_service.evaluate_model_accuracy(
                        model_id=model.id,
                        evaluation_period_days=options['evaluation_days']
                    )
                    individual_results[model.id] = model_results
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"    MAE: {model_results['mae']:.2f}, "
                            f"MAPE: {model_results['mape']:.2f}%"
                        )
                    )
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"    Error: {str(e)}")
                    )
            
            results['individual_models'] = individual_results
            
            return results
            
        except Company.DoesNotExist:
            raise CommandError(f'Empresa {company_id} no encontrada')
    
    def _evaluate_all_models(self, evaluation_service, options):
        """Evalúa todos los modelos activos"""
        
        self.stdout.write("Evaluando todos los modelos activos...")
        
        # Obtiene todas las empresas con modelos activos
        companies_with_models = Company.objects.filter(
            forecast_models__status='active'
        ).distinct()
        
        all_results = {}
        
        for company in companies_with_models:
            self.stdout.write(f"\n--- Empresa: {company.name} ---")
            
            try:
                # Configura opciones para esta empresa
                company_options = options.copy()
                company_options['company_id'] = company.id
                
                company_results = self._evaluate_company_models(evaluation_service, company_options)
                all_results[company.id] = {
                    'company_name': company.name,
                    'results': company_results
                }
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error evaluando {company.name}: {str(e)}")
                )
                all_results[company.id] = {
                    'company_name': company.name,
                    'error': str(e)
                }
        
        # Resumen general
        self._display_general_summary(all_results)
        
        return all_results
    
    def _display_performance_report(self, report):
        """Muestra el reporte de rendimiento"""
        self.stdout.write(
            self.style.SUCCESS("\n=== REPORTE DE RENDIMIENTO ===")
        )
        
        overall = report['overall_metrics']
        self.stdout.write(f"Modelos evaluados: {overall['models_count']}")
        self.stdout.write(f"Total pronósticos: {overall['total_forecasts']}")
        
        if overall['models_count'] > 0:
            self.stdout.write(f"MAE promedio: {overall['average_mae']:.2f}")
            self.stdout.write(f"MAPE promedio: {overall['average_mape']:.2f}%")
        
        # Mejor y peor modelo
        if report['best_performing_model']:
            best = report['best_performing_model']
            self.stdout.write(
                self.style.SUCCESS(
                    f"\nMejor modelo: {best['model_name']} "
                    f"(MAPE: {best['realtime_accuracy']['average_percentage_error']:.2f}%)"
                )
            )
        
        if report['worst_performing_model']:
            worst = report['worst_performing_model']
            self.stdout.write(
                self.style.WARNING(
                    f"Peor modelo: {worst['model_name']} "
                    f"(MAPE: {worst['realtime_accuracy']['average_percentage_error']:.2f}%)"
                )
            )
        
        # Recomendaciones
        if report['recommendations']:
            self.stdout.write("\nRecomendaciones:")
            for rec in report['recommendations']:
                self.stdout.write(f"  • {rec}")
    
    def _display_models_comparison(self, comparison):
        """Muestra la comparación de modelos"""
        self.stdout.write(
            self.style.SUCCESS("\n=== COMPARACIÓN DE MODELOS ===")
        )
        
        if comparison['best_model_overall']:
            best = comparison['best_model_overall']
            self.stdout.write(
                self.style.SUCCESS(
                    f"Mejor modelo general: {best['model_name']} (Rank: {best['overall_rank']:.2f})"
                )
            )
        
        # Rankings por métrica
        for metric, ranking in comparison['rankings_by_metric'].items():
            if ranking:
                self.stdout.write(f"\nRanking por {metric.upper()}:")
                for i, model_data in enumerate(ranking[:3], 1):  # Top 3
                    self.stdout.write(
                        f"  {i}. {model_data['model_name']}: {model_data[metric]:.3f}"
                    )
    
    def _display_general_summary(self, all_results):
        """Muestra resumen general de todas las evaluaciones"""
        self.stdout.write(
            self.style.SUCCESS("\n=== RESUMEN GENERAL ===")
        )
        
        total_companies = len(all_results)
        successful_evaluations = len([r for r in all_results.values() if 'error' not in r])
        
        self.stdout.write(f"Empresas procesadas: {total_companies}")
        self.stdout.write(f"Evaluaciones exitosas: {successful_evaluations}")
        
        if successful_evaluations < total_companies:
            errors = total_companies - successful_evaluations
            self.stdout.write(
                self.style.WARNING(f"Evaluaciones con errores: {errors}")
            )
    
    def _save_results(self, results, output_file):
        """Guarda los resultados en un archivo JSON"""
        try:
            # Convierte datetime objects a strings para serialización JSON
            json_results = self._convert_for_json(results)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(json_results, f, indent=2, ensure_ascii=False)
            
            self.stdout.write(
                self.style.SUCCESS(f"Resultados guardados en: {output_file}")
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error guardando resultados: {str(e)}")
            )
    
    def _convert_for_json(self, obj):
        """Convierte objetos para serialización JSON"""
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {key: self._convert_for_json(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_for_json(item) for item in obj]
        else:
            return obj
