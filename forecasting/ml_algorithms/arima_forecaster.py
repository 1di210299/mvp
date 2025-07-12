"""
Implementación del algoritmo ARIMA para pronósticos de demanda
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import logging
from datetime import datetime, timedelta
import warnings

try:
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.seasonal import seasonal_decompose
    from statsmodels.tsa.stattools import adfuller, acf, pacf
    from statsmodels.stats.diagnostic import acorr_ljungbox
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False

try:
    import pmdarima as pm
    from pmdarima import auto_arima
    PMDARIMA_AVAILABLE = True
except ImportError:
    PMDARIMA_AVAILABLE = False

from .base_forecaster import BaseForecaster

logger = logging.getLogger(__name__)
warnings.filterwarnings('ignore')


class ARIMAForecaster(BaseForecaster):
    """
    Implementación del algoritmo ARIMA para pronósticos de series temporales
    """
    
    def __init__(self, hyperparameters: Optional[Dict[str, Any]] = None):
        """
        Inicializa el forecaster ARIMA
        
        Args:
            hyperparameters: Parámetros específicos de ARIMA
        """
        if not STATSMODELS_AVAILABLE:
            raise ImportError("statsmodels no está instalado. Instálalo con: pip install statsmodels")
            
        # Hiperparámetros por defecto de ARIMA
        default_params = {
            'order': None,  # (p, d, q) - si es None, se usa auto_arima
            'seasonal_order': None,  # (P, D, Q, s) - para SARIMA
            'auto_arima': True,  # Usar auto_arima para encontrar mejores parámetros
            'max_p': 5,
            'max_d': 2,
            'max_q': 5,
            'max_P': 2,
            'max_D': 1,
            'max_Q': 2,
            'seasonal': True,
            'stepwise': True,
            'suppress_warnings': True,
            'error_action': 'ignore',
            'information_criterion': 'aic',  # 'aic', 'bic', 'hqic'
            'seasonal_test': 'ocsb',  # Test para detectar estacionalidad
            'alpha': 0.05  # Nivel de significancia
        }
        
        if hyperparameters:
            default_params.update(hyperparameters)
            
        super().__init__(default_params)
        
        self.seasonal_period = None
        self.differencing_order = None
        self.is_seasonal = False
        
    def get_model_name(self) -> str:
        """Retorna el nombre del modelo"""
        return "ARIMA"
    
    def _check_stationarity(self, timeseries: pd.Series, alpha: float = 0.05) -> Tuple[bool, Dict]:
        """
        Verifica si la serie temporal es estacionaria usando el test de Dickey-Fuller
        
        Args:
            timeseries: Serie temporal a verificar
            alpha: Nivel de significancia
            
        Returns:
            Tuple con (es_estacionaria, resultados_test)
        """
        try:
            result = adfuller(timeseries.dropna())
            
            test_results = {
                'adf_statistic': result[0],
                'p_value': result[1],
                'critical_values': result[4],
                'is_stationary': result[1] < alpha
            }
            
            return test_results['is_stationary'], test_results
            
        except Exception as e:
            logger.warning(f"Error en test de estacionariedad: {str(e)}")
            return False, {}
    
    def _detect_seasonality(self, timeseries: pd.Series) -> Tuple[bool, Optional[int]]:
        """
        Detecta estacionalidad en la serie temporal
        
        Args:
            timeseries: Serie temporal
            
        Returns:
            Tuple con (es_estacional, período_estacional)
        """
        try:
            # Intenta detectar estacionalidad automáticamente
            if len(timeseries) < 24:
                return False, None
            
            # Prueba diferentes períodos estacionales comunes
            seasonal_periods = [7, 30, 365]  # Semanal, mensual, anual
            
            best_period = None
            best_score = float('inf')
            
            for period in seasonal_periods:
                if len(timeseries) >= 2 * period:
                    try:
                        decomposition = seasonal_decompose(
                            timeseries, 
                            model='additive', 
                            period=period
                        )
                        # Calcula la varianza de la componente estacional
                        seasonal_var = np.var(decomposition.seasonal.dropna())
                        total_var = np.var(timeseries.dropna())
                        
                        # Si la varianza estacional es significativa
                        if seasonal_var / total_var > 0.1 and seasonal_var < best_score:
                            best_score = seasonal_var
                            best_period = period
                            
                    except Exception:
                        continue
            
            if best_period is not None:
                return True, best_period
            else:
                return False, None
                
        except Exception as e:
            logger.warning(f"Error detectando estacionalidad: {str(e)}")
            return False, None
    
    def _find_optimal_order(self, timeseries: pd.Series) -> Tuple[Tuple[int, int, int], Optional[Tuple[int, int, int, int]]]:
        """
        Encuentra el orden óptimo de ARIMA usando auto_arima
        
        Args:
            timeseries: Serie temporal
            
        Returns:
            Tuple con (orden_arima, orden_estacional)
        """
        try:
            if PMDARIMA_AVAILABLE and self.hyperparameters.get('auto_arima', True):
                logger.info("Usando auto_arima para encontrar parámetros óptimos...")
                
                model = auto_arima(
                    timeseries,
                    start_p=0, start_q=0,
                    max_p=self.hyperparameters.get('max_p', 5),
                    max_d=self.hyperparameters.get('max_d', 2), 
                    max_q=self.hyperparameters.get('max_q', 5),
                    max_P=self.hyperparameters.get('max_P', 2),
                    max_D=self.hyperparameters.get('max_D', 1),
                    max_Q=self.hyperparameters.get('max_Q', 2),
                    seasonal=self.hyperparameters.get('seasonal', True),
                    stepwise=self.hyperparameters.get('stepwise', True),
                    suppress_warnings=self.hyperparameters.get('suppress_warnings', True),
                    error_action=self.hyperparameters.get('error_action', 'ignore'),
                    information_criterion=self.hyperparameters.get('information_criterion', 'aic')
                )
                
                order = model.order
                seasonal_order = model.seasonal_order if model.seasonal_order != (0, 0, 0, 0) else None
                
                logger.info(f"Parámetros óptimos encontrados: ARIMA{order}")
                if seasonal_order:
                    logger.info(f"Parámetros estacionales: {seasonal_order}")
                
                return order, seasonal_order
                
            else:
                # Búsqueda manual simple
                logger.info("Usando búsqueda manual de parámetros...")
                
                best_aic = float('inf')
                best_order = (1, 1, 1)
                best_seasonal = None
                
                # Prueba diferentes combinaciones
                for p in range(0, min(3, self.hyperparameters.get('max_p', 3))):
                    for d in range(0, min(2, self.hyperparameters.get('max_d', 2))):
                        for q in range(0, min(3, self.hyperparameters.get('max_q', 3))):
                            try:
                                model = ARIMA(timeseries, order=(p, d, q))
                                fitted_model = model.fit()
                                
                                if fitted_model.aic < best_aic:
                                    best_aic = fitted_model.aic
                                    best_order = (p, d, q)
                                    
                            except Exception:
                                continue
                
                return best_order, best_seasonal
                
        except Exception as e:
            logger.warning(f"Error encontrando parámetros óptimos: {str(e)}")
            return (1, 1, 1), None
    
    def fit(self, data: pd.DataFrame, target_column: str = 'demand') -> 'ARIMAForecaster':
        """
        Entrena el modelo ARIMA
        
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
            
            # Extrae la serie temporal
            timeseries = processed_data[target_column]
            
            logger.info(f"Entrenando modelo ARIMA con {len(timeseries)} observaciones")
            
            # Verifica estacionariedad
            is_stationary, stationarity_test = self._check_stationarity(timeseries)
            logger.info(f"Serie estacionaria: {is_stationary} (p-value: {stationarity_test.get('p_value', 'N/A')})")
            
            # Detecta estacionalidad
            is_seasonal, seasonal_period = self._detect_seasonality(timeseries)
            self.is_seasonal = is_seasonal
            self.seasonal_period = seasonal_period
            
            if is_seasonal:
                logger.info(f"Estacionalidad detectada con período: {seasonal_period}")
            
            # Determina el orden del modelo
            if self.hyperparameters.get('order') is not None:
                order = self.hyperparameters['order']
                seasonal_order = self.hyperparameters.get('seasonal_order')
            else:
                order, seasonal_order = self._find_optimal_order(timeseries)
            
            # Crea y entrena el modelo
            if seasonal_order is not None:
                logger.info(f"Entrenando SARIMA{order}x{seasonal_order}")
                self.model = ARIMA(
                    timeseries,
                    order=order,
                    seasonal_order=seasonal_order
                )
            else:
                logger.info(f"Entrenando ARIMA{order}")
                self.model = ARIMA(timeseries, order=order)
            
            # Entrena el modelo
            self.fitted_model = self.model.fit()
            self.is_fitted = True
            
            # Calcula métricas en el conjunto de entrenamiento
            fitted_values = self.fitted_model.fittedvalues
            y_true = timeseries[fitted_values.index]
            
            self.metrics = self.calculate_metrics(y_true.values, fitted_values.values)
            
            # Añade métricas específicas de ARIMA - Asegurar valores JSON válidos
            self.metrics['aic'] = float(self.fitted_model.aic) if not np.isnan(self.fitted_model.aic) else 0.0
            self.metrics['bic'] = float(self.fitted_model.bic) if not np.isnan(self.fitted_model.bic) else 0.0
            self.metrics['hqic'] = float(self.fitted_model.hqic) if not np.isnan(self.fitted_model.hqic) else 0.0
            
            # Test de residuales - Manejo seguro de NaN
            try:
                residuals = self.fitted_model.resid
                if len(residuals) > 10:
                    ljung_box = acorr_ljungbox(residuals, lags=10, return_df=True)
                    p_value = ljung_box['lb_pvalue'].iloc[-1]
                    self.metrics['ljung_box_p_value'] = float(p_value) if not np.isnan(p_value) else 0.0
                else:
                    self.metrics['ljung_box_p_value'] = 0.0
            except Exception:
                self.metrics['ljung_box_p_value'] = 0.0
            
            logger.info(f"Modelo ARIMA entrenado exitosamente.")
            logger.info(f"AIC: {self.metrics['aic']:.2f}, MAE: {self.metrics['mae']:.2f}, MAPE: {self.metrics['mape']:.2f}%")
            
            return self
            
        except Exception as e:
            logger.error(f"Error entrenando modelo ARIMA: {str(e)}")
            raise
    
    def predict(self, periods: int, confidence_interval: float = 0.95) -> pd.DataFrame:
        """
        Genera pronósticos usando ARIMA
        
        Args:
            periods: Número de períodos a pronosticar
            confidence_interval: Nivel de confianza
            
        Returns:
            DataFrame con pronósticos y intervalos de confianza
        """
        if not self.is_fitted:
            raise ValueError("El modelo debe ser entrenado antes de hacer predicciones")
        
        # FIX: Verificar que fitted_model existe después de cargar desde archivo
        if not hasattr(self, 'fitted_model') or self.fitted_model is None:
            # Si no existe fitted_model, intentar recrearlo desde el modelo base
            if hasattr(self, 'model') and self.model is not None:
                logger.warning("fitted_model no encontrado, intentando recrear...")
                try:
                    # Reajustar el modelo si tenemos datos de entrenamiento
                    if hasattr(self, 'training_data') and self.training_data is not None:
                        target_column = 'quantity' if 'quantity' in self.training_data.columns else self.training_data.columns[0]
                        timeseries = self.training_data[target_column]
                        self.fitted_model = self.model.fit()
                        logger.info("fitted_model recreado exitosamente")
                    else:
                        raise ValueError("No hay datos de entrenamiento disponibles para recrear el modelo")
                except Exception as e:
                    logger.error(f"Error recreando fitted_model: {str(e)}")
                    raise ValueError(f"No se pudo recrear el modelo ARIMA: {str(e)}")
            else:
                raise ValueError("Modelo ARIMA no disponible para hacer predicciones")
        
        try:
            # Genera pronósticos
            forecast_result = self.fitted_model.forecast(
                steps=periods,
                alpha=1-confidence_interval
            )
            
            # Obtiene intervalos de confianza
            conf_int = self.fitted_model.get_forecast(
                steps=periods,
                alpha=1-confidence_interval
            ).conf_int()
            
            # Crea fechas futuras basadas en el índice de datos de entrenamiento
            if hasattr(self, 'training_data') and not self.training_data.empty:
                last_date = self.training_data.index[-1]
            else:
                # Fallback a fecha actual
                from datetime import datetime
                last_date = pd.Timestamp(datetime.now().date())
            
            future_dates = pd.date_range(
                start=last_date + pd.Timedelta(days=1),
                periods=periods,
                freq='D'
            )
            
            # Prepara el resultado
            result = pd.DataFrame({
                'predicted_demand': forecast_result.values,
                'lower_bound': conf_int.iloc[:, 0].values,
                'upper_bound': conf_int.iloc[:, 1].values,
                'confidence_level': confidence_interval
            }, index=future_dates)
            
            # Asegura que no haya valores negativos
            result['predicted_demand'] = result['predicted_demand'].clip(lower=0)
            result['lower_bound'] = result['lower_bound'].clip(lower=0)
            result['upper_bound'] = result['upper_bound'].clip(lower=0)
            
            logger.info(f"Generados {periods} pronósticos ARIMA")
            
            return result
            
        except Exception as e:
            logger.error(f"Error generando pronósticos ARIMA: {str(e)}")
            raise
    
    def get_residuals(self) -> pd.Series:
        """
        Obtiene los residuales del modelo
        
        Returns:
            Serie con residuales
        """
        if not self.is_fitted:
            return pd.Series()
            
        return self.fitted_model.resid
    
    def diagnostic_plots(self) -> None:
        """
        Genera gráficos de diagnóstico del modelo
        """
        if not self.is_fitted:
            raise ValueError("El modelo debe ser entrenado antes de generar diagnósticos")
            
        try:
            import matplotlib.pyplot as plt
            from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
            from scipy import stats
            
            residuals = self.get_residuals()
            
            fig, axes = plt.subplots(2, 2, figsize=(12, 8))
            
            # Gráfico de residuales
            axes[0, 0].plot(residuals)
            axes[0, 0].set_title('Residuales')
            axes[0, 0].set_xlabel('Tiempo')
            axes[0, 0].set_ylabel('Residuales')
            
            # Q-Q plot
            stats.probplot(residuals, dist="norm", plot=axes[0, 1])
            axes[0, 1].set_title('Q-Q Plot')
            
            # ACF de residuales
            plot_acf(residuals, ax=axes[1, 0], lags=20)
            axes[1, 0].set_title('ACF de Residuales')
            
            # Histograma de residuales
            axes[1, 1].hist(residuals, bins=20, density=True, alpha=0.7)
            axes[1, 1].set_title('Distribución de Residuales')
            axes[1, 1].set_xlabel('Residuales')
            axes[1, 1].set_ylabel('Densidad')
            
            plt.tight_layout()
            plt.show()
            
        except ImportError:
            logger.warning("matplotlib no está disponible para generar gráficos")
        except Exception as e:
            logger.error(f"Error generando gráficos de diagnóstico: {str(e)}")
    
    def get_model_summary(self) -> str:
        """
        Obtiene un resumen del modelo entrenado
        
        Returns:
            String con resumen del modelo
        """
        if not self.is_fitted:
            return "Modelo no entrenado"
            
        return str(self.fitted_model.summary())
    
    def get_information_criteria(self) -> Dict[str, float]:
        """
        Obtiene criterios de información del modelo
        
        Returns:
            Diccionario con AIC, BIC, HQIC
        """
        if not self.is_fitted:
            return {}
            
        return {
            'aic': self.fitted_model.aic,
            'bic': self.fitted_model.bic,
            'hqic': self.fitted_model.hqic
        }
    
    def predict_in_sample(self) -> pd.Series:
        """
        Genera predicciones dentro de la muestra (fitted values)
        
        Returns:
            Serie con predicciones dentro de la muestra
        """
        if not self.is_fitted:
            return pd.Series()
            
        return self.fitted_model.fittedvalues
