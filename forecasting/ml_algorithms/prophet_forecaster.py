"""
Implementación del algoritmo Prophet para pronósticos de demanda
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import logging
from datetime import datetime, timedelta

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False

from .base_forecaster import BaseForecaster

logger = logging.getLogger(__name__)


class ProphetForecaster(BaseForecaster):
    """
    Implementación del algoritmo Facebook Prophet para pronósticos de series temporales
    """
    
    def __init__(self, hyperparameters: Optional[Dict[str, Any]] = None):
        """
        Inicializa el forecaster Prophet
        
        Args:
            hyperparameters: Parámetros específicos de Prophet
        """
        if not PROPHET_AVAILABLE:
            raise ImportError("Prophet no está instalado. Instálalo con: pip install prophet")
            
        # Hiperparámetros optimizados para ML Services Core
        default_params = {
            'growth': 'linear',  # 'linear' o 'logistic'
            'yearly_seasonality': 'auto',
            'weekly_seasonality': 'auto', 
            'daily_seasonality': 'auto',
            'seasonality_mode': 'additive',  # 'additive' o 'multiplicative'
            'changepoint_prior_scale': 0.05,  # Optimizado para estabilidad
            'seasonality_prior_scale': 10.0,
            'holidays_prior_scale': 10.0,
            'mcmc_samples': 0,
            'interval_width': 0.95,
            'uncertainty_samples': 1000,
            # Nuevos parámetros optimizados
            'changepoint_range': 0.8,  # Mejora detección de cambios
            'n_changepoints': 25,  # Número óptimo de changepoints
            'fourier_order': None,  # Auto-determinado por seasonality
        }
        
        if hyperparameters:
            default_params.update(hyperparameters)
            
        super().__init__(default_params)
        
        self.holidays = None
        self.additional_regressors = []
        
    def get_model_name(self) -> str:
        """Retorna el nombre del modelo"""
        return "Facebook Prophet"
    
    def add_holidays(self, holidays_df: pd.DataFrame) -> None:
        """
        Añade días festivos al modelo
        
        Args:
            holidays_df: DataFrame con columnas 'holiday' y 'ds' (fechas)
        """
        self.holidays = holidays_df
        
    def add_regressor(self, name: str, prior_scale: float = 10.0, 
                     standardize: bool = True, mode: str = 'additive') -> None:
        """
        Añade un regresor adicional al modelo
        
        Args:
            name: Nombre del regresor
            prior_scale: Escala del prior para el regresor
            standardize: Si estandarizar el regresor
            mode: 'additive' o 'multiplicative'
        """
        regressor_config = {
            'name': name,
            'prior_scale': prior_scale,
            'standardize': standardize,
            'mode': mode
        }
        self.additional_regressors.append(regressor_config)
    
    def fit(self, data: pd.DataFrame, target_column: str = 'demand') -> 'ProphetForecaster':
        """
        Entrena el modelo Prophet con validación robusta de datos
        
        Args:
            data: DataFrame con datos históricos
            target_column: Nombre de la columna objetivo
            
        Returns:
            self: Instancia del modelo entrenado
        """
        try:
            # VALIDACIÓN ROBUSTA DE DATOS
            if not isinstance(data, pd.DataFrame):
                raise ValueError("Los datos deben ser un DataFrame de pandas")
            
            if len(data) < 10:
                raise ValueError("Se necesitan al menos 10 observaciones para entrenar Prophet")
            
            # Verificar si tiene columna objetivo
            if target_column not in data.columns:
                # Si no tiene la columna objetivo, buscar alternativas
                if 'y' in data.columns:
                    target_column = 'y'
                elif 'value' in data.columns:
                    target_column = 'value'
                elif len(data.columns) == 1:
                    target_column = data.columns[0]
                else:
                    raise ValueError(f"Columna objetivo '{target_column}' no encontrada en los datos")
            
            # PREPARAR DATOS PARA PROPHET (requiere 'ds' y 'y')
            prophet_data = pd.DataFrame()
            
            # Manejar la columna de fecha (ds)
            if 'ds' in data.columns:
                # Si ya tiene columna 'ds', usarla
                prophet_data['ds'] = pd.to_datetime(data['ds'])
            elif 'date' in data.columns:
                # Si tiene columna 'date', usarla
                prophet_data['ds'] = pd.to_datetime(data['date'])
            elif isinstance(data.index, pd.DatetimeIndex):
                # Si el índice es de fechas, usarlo
                prophet_data['ds'] = data.index
            else:
                # Crear fechas sintéticas si no hay fechas
                logger.warning("No se encontraron fechas, creando fechas sintéticas")
                prophet_data['ds'] = pd.date_range(
                    start='2023-01-01', 
                    periods=len(data), 
                    freq='D'
                )
            
            # Manejar la columna objetivo (y)
            prophet_data['y'] = data[target_column].values
            
            # Limpiar timezone si existe
            if hasattr(prophet_data['ds'], 'dt') and prophet_data['ds'].dt.tz is not None:
                prophet_data['ds'] = prophet_data['ds'].dt.tz_localize(None)
            
            # Validar que no hay valores nulos
            if prophet_data['y'].isnull().any():
                logger.warning("Eliminando valores nulos en datos de entrenamiento")
                prophet_data = prophet_data.dropna()
            
            # Guardar datos de entrenamiento
            self.training_data = prophet_data.copy()
            
            # Inicializar modelo Prophet
            self.model = Prophet(
                growth=self.hyperparameters.get('growth', 'linear'),
                yearly_seasonality=self.hyperparameters.get('yearly_seasonality', 'auto'),
                weekly_seasonality=self.hyperparameters.get('weekly_seasonality', 'auto'),
                daily_seasonality=self.hyperparameters.get('daily_seasonality', 'auto'),
                seasonality_mode=self.hyperparameters.get('seasonality_mode', 'additive'),
                changepoint_prior_scale=self.hyperparameters.get('changepoint_prior_scale', 0.05),
                seasonality_prior_scale=self.hyperparameters.get('seasonality_prior_scale', 10.0),
                holidays_prior_scale=self.hyperparameters.get('holidays_prior_scale', 10.0),
                mcmc_samples=self.hyperparameters.get('mcmc_samples', 0),
                interval_width=self.hyperparameters.get('interval_width', 0.95),
                uncertainty_samples=self.hyperparameters.get('uncertainty_samples', 1000)
            )
            
            # Entrenar el modelo
            logger.info(f"Entrenando modelo Prophet con {len(prophet_data)} observaciones")
            self.model.fit(prophet_data)
            
            self.is_fitted = True
            
            # Calcular métricas en el conjunto de entrenamiento
            train_forecast = self.model.predict(prophet_data)
            y_true = prophet_data['y'].values
            y_pred = train_forecast['yhat'].values
            
            self.metrics = self.calculate_metrics(y_true, y_pred)
            
            logger.info(f"Modelo Prophet entrenado exitosamente. MAE: {self.metrics['mae']:.2f}, MAPE: {self.metrics['mape']:.2f}%")
            
            return self
            
        except Exception as e:
            logger.error(f"Error entrenando modelo Prophet: {str(e)}")
            raise
    
    def predict(self, periods: int, confidence_interval: float = 0.95) -> pd.DataFrame:
        """
        Genera pronósticos usando Prophet
        
        Args:
            periods: Número de períodos a pronosticar
            confidence_interval: Nivel de confianza
            
        Returns:
            DataFrame con pronósticos y intervalos de confianza
        """
        if not self.is_fitted:
            raise ValueError("El modelo debe ser entrenado antes de hacer predicciones")
        
        try:
            # Crea el dataframe futuro
            future = self.model.make_future_dataframe(periods=periods, freq='D')
            
            # Añade regresores futuros (deberían ser proporcionados externamente)
            for regressor in self.additional_regressors:
                regressor_name = regressor['name']
                if regressor_name not in future.columns:
                    # Usa el último valor conocido para periodos futuros
                    if hasattr(self.training_data, regressor_name):
                        last_value = self.training_data[regressor_name].iloc[-1]
                        future[regressor_name] = last_value
                    else:
                        future[regressor_name] = 0
            
            # Genera pronósticos
            forecast = self.model.predict(future)
            
            # Filtra solo los períodos futuros
            future_forecast = forecast.iloc[-periods:].copy()
            
            # Prepara el resultado
            result = pd.DataFrame({
                'date': future_forecast['ds'],
                'predicted_demand': future_forecast['yhat'],
                'lower_bound': future_forecast['yhat_lower'],
                'upper_bound': future_forecast['yhat_upper'],
                'trend': future_forecast['trend'],
                'seasonality': future_forecast.get('yearly', 0) + future_forecast.get('weekly', 0),
                'confidence_level': confidence_interval
            })
            
            # Asegura que no haya valores negativos
            result['predicted_demand'] = result['predicted_demand'].clip(lower=0)
            result['lower_bound'] = result['lower_bound'].clip(lower=0)
            result['upper_bound'] = result['upper_bound'].clip(lower=0)
            
            result.set_index('date', inplace=True)
            
            logger.info(f"Generados {periods} pronósticos Prophet")
            
            return result
            
        except Exception as e:
            logger.error(f"Error generando pronósticos Prophet: {str(e)}")
            raise
    
    def predict_with_history(self, periods: int) -> pd.DataFrame:
        """
        Genera pronósticos incluyendo el período histórico
        
        Args:
            periods: Número de períodos futuros a pronosticar
            
        Returns:
            DataFrame con pronósticos completos (histórico + futuro)
        """
        if not self.is_fitted:
            raise ValueError("El modelo debe ser entrenado antes de hacer predicciones")
        
        # Crea el dataframe futuro
        future = self.model.make_future_dataframe(periods=periods, freq='D')
        
        # Añade regresores si existen
        for regressor in self.additional_regressors:
            regressor_name = regressor['name']
            if regressor_name not in future.columns:
                if regressor_name in self.training_data.columns:
                    last_value = self.training_data[regressor_name].iloc[-1]
                    future[regressor_name] = last_value
                else:
                    future[regressor_name] = 0
        
        # Genera pronósticos
        forecast = self.model.predict(future)
        
        # Prepara el resultado completo
        result = pd.DataFrame({
            'date': forecast['ds'],
            'predicted_demand': forecast['yhat'],
            'lower_bound': forecast['yhat_lower'],
            'upper_bound': forecast['yhat_upper'],
            'trend': forecast['trend'],
            'seasonality': forecast.get('yearly', 0) + forecast.get('weekly', 0)
        })
        
        result.set_index('date', inplace=True)
        
        return result
    
    def get_components(self) -> Optional[pd.DataFrame]:
        """
        Obtiene los componentes del modelo (tendencia, estacionalidad, etc.)
        
        Returns:
            DataFrame con componentes del modelo
        """
        if not self.is_fitted:
            return None
            
        # Crea un dataframe con los datos de entrenamiento
        ds_values = self.training_data.index
        if hasattr(ds_values, 'tz') and ds_values.tz is not None:
            ds_values = ds_values.tz_localize(None)
            
        prophet_data = pd.DataFrame({
            'ds': ds_values,
            'y': self.training_data.iloc[:, 0]  # Asume que la primera columna es el target
        })
        
        # Obtiene los componentes
        forecast = self.model.predict(prophet_data)
        components = self.model.predict(prophet_data)[['ds', 'trend', 'yearly', 'weekly']]
        
        if 'daily' in forecast.columns:
            components['daily'] = forecast['daily']
            
        components.set_index('ds', inplace=True)
        
        return components
    
    def plot_forecast(self, periods: int = 30) -> None:
        """
        Genera gráficos del pronóstico (requiere matplotlib)
        
        Args:
            periods: Número de períodos a pronosticar en el gráfico
        """
        if not self.is_fitted:
            raise ValueError("El modelo debe ser entrenado antes de generar gráficos")
            
        try:
            import matplotlib.pyplot as plt
            
            # Genera pronósticos
            future = self.model.make_future_dataframe(periods=periods, freq='D')
            forecast = self.model.predict(future)
            
            # Crea el gráfico
            fig = self.model.plot(forecast)
            plt.title(f'Pronóstico Prophet - {periods} días')
            plt.xlabel('Fecha')
            plt.ylabel('Demanda')
            plt.show()
            
            # Gráfico de componentes
            fig2 = self.model.plot_components(forecast)
            plt.show()
            
        except ImportError:
            logger.warning("matplotlib no está disponible para generar gráficos")
        except Exception as e:
            logger.error(f"Error generando gráficos: {str(e)}")
    
    def get_changepoints(self) -> pd.DataFrame:
        """
        Obtiene los puntos de cambio detectados por Prophet
        
        Returns:
            DataFrame con puntos de cambio y su significancia
        """
        if not self.is_fitted:
            return pd.DataFrame()
            
        changepoints = self.model.changepoints
        changepoint_effects = self.model.params['delta'].mean(axis=0)
        
        result = pd.DataFrame({
            'changepoint': changepoints,
            'effect': changepoint_effects
        })
        
        return result.sort_values('effect', key=abs, ascending=False)
    
    def cross_validate(self, horizon: str = '30 days', 
                      initial: str = '730 days', period: str = '180 days') -> pd.DataFrame:
        """
        Realiza validación cruzada del modelo
        
        Args:
            horizon: Horizonte de pronóstico
            initial: Período inicial de entrenamiento  
            period: Período entre cortes de validación
            
        Returns:
            DataFrame con resultados de validación cruzada
        """
        if not self.is_fitted:
            raise ValueError("El modelo debe ser entrenado antes de la validación cruzada")
            
        try:
            from prophet.diagnostics import cross_validation, performance_metrics
            
            # Realiza validación cruzada
            df_cv = cross_validation(
                self.model, 
                horizon=horizon,
                initial=initial, 
                period=period
            )
            
            # Calcula métricas de rendimiento
            df_performance = performance_metrics(df_cv)
            
            return df_performance
            
        except ImportError:
            logger.error("prophet.diagnostics no está disponible")
            return pd.DataFrame()
    
    def get_baseline_accuracy_metrics(self, data: pd.DataFrame, 
                                    target_column: str = 'demand') -> Dict[str, float]:
        """
        Calcula métricas de accuracy baseline para ML Services Core
        
        Args:
            data: Datos de prueba
            target_column: Columna objetivo
            
        Returns:
            Dict con métricas baseline
        """
        if not self.is_fitted:
            raise ValueError("El modelo debe estar entrenado")
        
        # Preparar datos para Prophet (igual que en fit)
        prophet_data = pd.DataFrame()
        
        # Manejar la columna de fecha (ds)
        if 'ds' in data.columns:
            prophet_data['ds'] = pd.to_datetime(data['ds'])
        elif 'date' in data.columns:
            prophet_data['ds'] = pd.to_datetime(data['date'])
        elif isinstance(data.index, pd.DatetimeIndex):
            prophet_data['ds'] = data.index
        else:
            # Crear fechas sintéticas
            prophet_data['ds'] = pd.date_range(
                start='2024-01-01', 
                periods=len(data), 
                freq='D'
            )
        
        # Manejar la columna objetivo (y)
        if target_column in data.columns:
            prophet_data['y'] = data[target_column].values
        elif 'y' in data.columns:
            prophet_data['y'] = data['y'].values
        else:
            raise ValueError(f"No se encontró la columna objetivo '{target_column}'")
        
        # Limpiar timezone si existe
        if hasattr(prophet_data['ds'], 'dt') and prophet_data['ds'].dt.tz is not None:
            prophet_data['ds'] = prophet_data['ds'].dt.tz_localize(None)
        
        # Hacer predicciones
        forecast = self.model.predict(prophet_data[['ds']])
        
        # Calcular métricas
        actual = prophet_data['y'].values
        predicted = forecast['yhat'].values
        
        # Métricas básicas
        mae = np.mean(np.abs(actual - predicted))
        mse = np.mean((actual - predicted) ** 2)
        rmse = np.sqrt(mse)
        mape = np.mean(np.abs((actual - predicted) / np.where(actual != 0, actual, 1))) * 100
        
        # Métricas avanzadas para ML Core
        def mean_absolute_scaled_error(actual, predicted):
            """MASE - Mean Absolute Scaled Error"""
            naive_forecast = actual[:-1]  # Naive forecast (t-1)
            naive_mae = np.mean(np.abs(actual[1:] - naive_forecast))
            return mae / naive_mae if naive_mae != 0 else float('inf')
        
        mase = mean_absolute_scaled_error(actual, predicted)
        
        # Coeficiente de determinación
        ss_res = np.sum((actual - predicted) ** 2)
        ss_tot = np.sum((actual - np.mean(actual)) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
        # Accuracy score (100 - MAPE)
        accuracy_score = max(0, 100 - mape)
        
        # Directional accuracy (% de predicciones que van en la dirección correcta)
        if len(actual) > 1:
            actual_direction = np.diff(actual) > 0
            predicted_direction = np.diff(predicted) > 0
            directional_accuracy = np.mean(actual_direction == predicted_direction) * 100
        else:
            directional_accuracy = 0
        
        return {
            'mae': float(mae),
            'mse': float(mse),
            'rmse': float(rmse),
            'mape': float(mape),
            'mase': float(mase),
            'r2_score': float(r2),
            'accuracy_score': float(accuracy_score),
            'directional_accuracy': float(directional_accuracy),
            'forecast_bias': float(np.mean(predicted - actual)),
            'prediction_interval_coverage': self._calculate_coverage(actual, forecast)
        }
    
    def _calculate_coverage(self, actual: np.ndarray, forecast: pd.DataFrame) -> float:
        """
        Calcula la cobertura del intervalo de predicción
        """
        lower_bound = forecast['yhat_lower'].values
        upper_bound = forecast['yhat_upper'].values
        
        within_interval = (actual >= lower_bound) & (actual <= upper_bound)
        coverage = np.mean(within_interval) * 100
        
        return float(coverage)
    
    def get_performance_summary(self, data: pd.DataFrame, 
                              target_column: str = 'demand') -> Dict[str, Any]:
        """
        Resumen completo de performance para ML Services Core
        """
        baseline_metrics = self.get_baseline_accuracy_metrics(data, target_column)
        
        # Información del modelo
        model_info = {
            'model_name': self.get_model_name(),
            'hyperparameters': self.hyperparameters,
            'is_fitted': self.is_fitted,
            'training_samples': len(data) if data is not None else 0,
            'additional_regressors': len(self.additional_regressors),
            'has_holidays': self.holidays is not None
        }
        
        # Componentes del modelo (si está entrenado)
        components = {}
        if self.is_fitted:
            try:
                # Obtener componentes de seasonality
                components = {
                    'trend_changepoints': len(self.model.changepoints),
                    'yearly_seasonality': 'yearly' in self.model.seasonalities,
                    'weekly_seasonality': 'weekly' in self.model.seasonalities,
                    'daily_seasonality': 'daily' in self.model.seasonalities,
                    'growth_type': self.hyperparameters.get('growth', 'linear')
                }
            except Exception as e:
                logger.warning(f"Error obteniendo componentes: {e}")
        
        return {
            'model_info': model_info,
            'baseline_metrics': baseline_metrics,
            'model_components': components,
            'timestamp': datetime.now().isoformat()
        }
    
    def optimize_hyperparameters(self, data: pd.DataFrame, target_column: str = 'demand',
                                cv_horizon: str = '30 days') -> Dict[str, Any]:
        """
        Optimización automática de hiperparámetros para ML Services Core
        """
        param_grid = {
            'changepoint_prior_scale': [0.001, 0.01, 0.1, 0.5],
            'seasonality_prior_scale': [0.01, 0.1, 1.0, 10.0],
            'holidays_prior_scale': [0.01, 0.1, 1.0, 10.0],
            'seasonality_mode': ['additive', 'multiplicative']
        }
        
        best_params = None
        best_mape = float('inf')
        results = []
        
        logger.info("Iniciando optimización de hiperparámetros Prophet...")
        
        # Grid search simplificado
        for changepoint_scale in param_grid['changepoint_prior_scale']:
            for seasonality_scale in param_grid['seasonality_prior_scale']:
                for holidays_scale in param_grid['holidays_prior_scale']:
                    for season_mode in param_grid['seasonality_mode']:
                        
                        try:
                            # Crear modelo con parámetros específicos
                            test_params = self.hyperparameters.copy()
                            test_params.update({
                                'changepoint_prior_scale': changepoint_scale,
                                'seasonality_prior_scale': seasonality_scale,
                                'holidays_prior_scale': holidays_scale,
                                'seasonality_mode': season_mode
                            })
                            
                            # Entrenar y evaluar
                            test_model = ProphetForecaster(test_params)
                            test_model.fit(data, target_column)
                            
                            # Validación cruzada rápida
                            cv_results = test_model.cross_validate(horizon=cv_horizon)
                            if not cv_results.empty:
                                avg_mape = cv_results['mape'].mean()
                                
                                results.append({
                                    'params': test_params,
                                    'mape': avg_mape,
                                    'mae': cv_results['mae'].mean(),
                                    'rmse': cv_results['rmse'].mean()
                                })
                                
                                if avg_mape < best_mape:
                                    best_mape = avg_mape
                                    best_params = test_params
                        
                        except Exception as e:
                            logger.warning(f"Error en optimización con params {test_params}: {e}")
                            continue
        
        if best_params:
            self.hyperparameters = best_params
            logger.info(f"Mejores parámetros encontrados con MAPE: {best_mape:.4f}")
        
        return {
            'best_params': best_params,
            'best_mape': best_mape,
            'all_results': results
        }
