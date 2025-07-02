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
            
        # Hiperparámetros por defecto de Prophet
        default_params = {
            'growth': 'linear',  # 'linear' o 'logistic'
            'yearly_seasonality': 'auto',
            'weekly_seasonality': 'auto', 
            'daily_seasonality': 'auto',
            'seasonality_mode': 'additive',  # 'additive' o 'multiplicative'
            'changepoint_prior_scale': 0.05,
            'seasonality_prior_scale': 10.0,
            'holidays_prior_scale': 10.0,
            'mcmc_samples': 0,
            'interval_width': 0.95,
            'uncertainty_samples': 1000
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
        Entrena el modelo Prophet
        
        Args:
            data: DataFrame con datos históricos
            target_column: Nombre de la columna objetivo
            
        Returns:
            self: Instancia del modelo entrenado
        """
        try:
            # Valida los datos
            self.validate_data(data, target_column)
            
            # Preprocesa los datos
            processed_data = self.preprocess_data(data, target_column)
            self.training_data = processed_data.copy()
            
            # Prepara los datos para Prophet (requiere columnas 'ds' y 'y')
            prophet_data = pd.DataFrame({
                'ds': processed_data.index,
                'y': processed_data[target_column]
            })
            
            # Añade regresores adicionales si existen
            for regressor in self.additional_regressors:
                regressor_name = regressor['name']
                if regressor_name in processed_data.columns:
                    prophet_data[regressor_name] = processed_data[regressor_name]
            
            # Inicializa el modelo Prophet
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
            
            # Añade días festivos si están definidos
            if self.holidays is not None:
                self.model.holidays = self.holidays
            
            # Añade regresores adicionales
            for regressor in self.additional_regressors:
                self.model.add_regressor(
                    regressor['name'],
                    prior_scale=regressor['prior_scale'],
                    standardize=regressor['standardize'],
                    mode=regressor['mode']
                )
            
            # Entrena el modelo
            logger.info(f"Entrenando modelo Prophet con {len(prophet_data)} observaciones")
            self.model.fit(prophet_data)
            
            self.is_fitted = True
            
            # Calcula métricas en el conjunto de entrenamiento
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
        prophet_data = pd.DataFrame({
            'ds': self.training_data.index,
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
        except Exception as e:
            logger.error(f"Error en validación cruzada: {str(e)}")
            return pd.DataFrame()
