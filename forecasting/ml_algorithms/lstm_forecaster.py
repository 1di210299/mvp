"""
Implementación del algoritmo LSTM para pronósticos de demanda
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import logging
from datetime import datetime, timedelta

try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization
    from tensorflow.keras.optimizers import Adam
    from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
    from sklearn.preprocessing import MinMaxScaler
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False

from .base_forecaster import BaseForecaster

logger = logging.getLogger(__name__)


class LSTMForecaster(BaseForecaster):
    """
    Implementación del algoritmo LSTM para pronósticos de series temporales
    """
    
    def __init__(self, hyperparameters: Optional[Dict[str, Any]] = None):
        """
        Inicializa el forecaster LSTM
        
        Args:
            hyperparameters: Parámetros específicos del modelo
        """
        if not TENSORFLOW_AVAILABLE:
            raise ImportError("TensorFlow no está instalado. Instálalo con: pip install tensorflow")
            
        # Hiperparámetros por defecto
        default_params = {
            # Arquitectura del modelo
            'sequence_length': 30,  # Longitud de secuencia de entrada
            'lstm_units': [50, 25],  # Unidades LSTM por capa
            'dense_units': [25],  # Unidades densas
            'dropout_rate': 0.2,  # Tasa de dropout
            'recurrent_dropout': 0.1,  # Dropout recurrente
            'use_batch_norm': True,  # Normalización por lotes
            
            # Entrenamiento
            'epochs': 100,  # Número máximo de épocas
            'batch_size': 32,  # Tamaño del lote
            'learning_rate': 0.001,  # Tasa de aprendizaje
            'validation_split': 0.2,  # Fracción para validación
            'early_stopping_patience': 10,  # Paciencia para early stopping
            'reduce_lr_patience': 5,  # Paciencia para reducir learning rate
            'min_lr': 1e-6,  # Learning rate mínimo
            
            # Preprocesamiento
            'normalize_features': True,  # Normalizar datos
            'add_features': True,  # Añadir features adicionales
            'feature_columns': ['trend', 'seasonality'],  # Features adicionales
            
            # Configuración
            'random_state': 42,
            'verbose': 0  # Verbosidad del entrenamiento
        }
        
        if hyperparameters:
            default_params.update(hyperparameters)
            
        super().__init__(default_params)
        
        self.scaler = MinMaxScaler() if default_params['normalize_features'] else None
        self.feature_scaler = MinMaxScaler() if default_params['add_features'] else None
        self.model = None
        self.history = None
        
        # Configurar TensorFlow para uso de memoria eficiente
        if TENSORFLOW_AVAILABLE:
            tf.random.set_seed(default_params['random_state'])
            # Configurar GPU si está disponible
            try:
                gpus = tf.config.experimental.list_physical_devices('GPU')
                if gpus:
                    for gpu in gpus:
                        tf.config.experimental.set_memory_growth(gpu, True)
            except Exception:
                pass
    
    def get_model_name(self) -> str:
        """Retorna el nombre del modelo"""
        return "LSTM Neural Network"
    
    def _create_additional_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Crea features adicionales para mejorar el rendimiento del LSTM
        """
        features = pd.DataFrame(index=data.index)
        
        # Tendencia
        features['trend'] = np.arange(len(data)) / len(data)
        
        # Features temporales normalizados
        features['day_of_week'] = data.index.dayofweek / 6.0
        features['day_of_month'] = (data.index.day - 1) / 30.0
        features['month'] = (data.index.month - 1) / 11.0
        features['quarter'] = (data.index.quarter - 1) / 3.0
        
        # Estacionalidad sinusoidal
        features['sin_week'] = np.sin(2 * np.pi * data.index.dayofweek / 7.0)
        features['cos_week'] = np.cos(2 * np.pi * data.index.dayofweek / 7.0)
        features['sin_month'] = np.sin(2 * np.pi * data.index.month / 12.0)
        features['cos_month'] = np.cos(2 * np.pi * data.index.month / 12.0)
        features['sin_year'] = np.sin(2 * np.pi * data.index.dayofyear / 365.0)
        features['cos_year'] = np.cos(2 * np.pi * data.index.dayofyear / 365.0)
        
        # Features booleanos como flotantes
        features['is_weekend'] = (data.index.dayofweek >= 5).astype(float)
        features['is_month_end'] = data.index.is_month_end.astype(float)
        features['is_month_start'] = data.index.is_month_start.astype(float)
        
        return features
    
    def _create_sequences(self, data: np.ndarray, target: np.ndarray, 
                         sequence_length: int) -> Tuple[np.ndarray, np.ndarray]:
        """
        Crea secuencias para entrenamiento del LSTM
        
        Args:
            data: Datos de entrada (features)
            target: Variable objetivo
            sequence_length: Longitud de la secuencia
            
        Returns:
            Tupla con (X, y) para entrenamiento
        """
        X, y = [], []
        
        for i in range(sequence_length, len(data)):
            X.append(data[i-sequence_length:i])
            y.append(target[i])
        
        return np.array(X), np.array(y)
    
    def _build_model(self, input_shape: Tuple[int, int]) -> tf.keras.Model:
        """
        Construye la arquitectura del modelo LSTM
        
        Args:
            input_shape: Forma de los datos de entrada (sequence_length, n_features)
            
        Returns:
            Modelo LSTM compilado
        """
        model = Sequential()
        
        lstm_units = self.hyperparameters.get('lstm_units', [50, 25])
        dropout_rate = self.hyperparameters.get('dropout_rate', 0.2)
        recurrent_dropout = self.hyperparameters.get('recurrent_dropout', 0.1)
        use_batch_norm = self.hyperparameters.get('use_batch_norm', True)
        
        # Primera capa LSTM
        model.add(LSTM(
            units=lstm_units[0],
            return_sequences=len(lstm_units) > 1,
            input_shape=input_shape,
            dropout=dropout_rate,
            recurrent_dropout=recurrent_dropout
        ))
        
        if use_batch_norm:
            model.add(BatchNormalization())
        
        # Capas LSTM adicionales
        for i, units in enumerate(lstm_units[1:], 1):
            return_sequences = i < len(lstm_units) - 1
            model.add(LSTM(
                units=units,
                return_sequences=return_sequences,
                dropout=dropout_rate,
                recurrent_dropout=recurrent_dropout
            ))
            
            if use_batch_norm:
                model.add(BatchNormalization())
        
        # Capas densas
        dense_units = self.hyperparameters.get('dense_units', [25])
        for units in dense_units:
            model.add(Dense(units, activation='relu'))
            model.add(Dropout(dropout_rate))
            
            if use_batch_norm:
                model.add(BatchNormalization())
        
        # Capa de salida
        model.add(Dense(1, activation='linear'))
        
        # Compilar modelo
        optimizer = Adam(learning_rate=self.hyperparameters.get('learning_rate', 0.001))
        model.compile(
            optimizer=optimizer,
            loss='mse',
            metrics=['mae']
        )
        
        return model
    
    def fit(self, data: pd.DataFrame, target_column: str = 'demand') -> 'LSTMForecaster':
        """
        Entrena el modelo LSTM
        """
        try:
            # Valida los datos
            self.validate_data(data, target_column)
            
            # Preprocesa los datos
            processed_data = self.preprocess_data(data, target_column)
            self.training_data = processed_data.copy()
            
            sequence_length = self.hyperparameters.get('sequence_length', 30)
            
            if len(processed_data) < sequence_length + 10:
                raise ValueError(f"Insuficientes datos para LSTM (mínimo {sequence_length + 10} observaciones)")
            
            logger.info(f"Entrenando modelo LSTM con {len(processed_data)} observaciones")
            
            # Prepara datos target
            target_values = processed_data[target_column].values.reshape(-1, 1)
            
            # Normaliza target
            if self.scaler is not None:
                target_values = self.scaler.fit_transform(target_values)
            
            # Prepara features adicionales si se especifica
            if self.hyperparameters.get('add_features', True):
                additional_features = self._create_additional_features(processed_data)
                
                if self.feature_scaler is not None:
                    additional_features_scaled = self.feature_scaler.fit_transform(additional_features)
                else:
                    additional_features_scaled = additional_features.values
                
                # Combina target con features adicionales
                all_features = np.column_stack([target_values.flatten(), additional_features_scaled])
            else:
                all_features = target_values
            
            # Crea secuencias
            X, y = self._create_sequences(
                all_features, 
                target_values.flatten(), 
                sequence_length
            )
            
            if len(X) == 0:
                raise ValueError("No se pudieron crear secuencias de entrenamiento")
            
            logger.info(f"Creadas {len(X)} secuencias de entrenamiento con forma {X.shape}")
            
            # Construye el modelo
            input_shape = (X.shape[1], X.shape[2])
            self.model = self._build_model(input_shape)
            
            logger.info(f"Modelo LSTM construido con {self.model.count_params()} parámetros")
            
            # Callbacks
            callbacks = []
            
            # Early stopping
            early_stopping = EarlyStopping(
                monitor='val_loss',
                patience=self.hyperparameters.get('early_stopping_patience', 10),
                restore_best_weights=True,
                verbose=self.hyperparameters.get('verbose', 0)
            )
            callbacks.append(early_stopping)
            
            # Reduce learning rate
            reduce_lr = ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=self.hyperparameters.get('reduce_lr_patience', 5),
                min_lr=self.hyperparameters.get('min_lr', 1e-6),
                verbose=self.hyperparameters.get('verbose', 0)
            )
            callbacks.append(reduce_lr)
            
            # Entrena el modelo
            self.history = self.model.fit(
                X, y,
                epochs=self.hyperparameters.get('epochs', 100),
                batch_size=self.hyperparameters.get('batch_size', 32),
                validation_split=self.hyperparameters.get('validation_split', 0.2),
                callbacks=callbacks,
                verbose=self.hyperparameters.get('verbose', 0),
                shuffle=True
            )
            
            self.is_fitted = True
            
            # Calcula métricas en el conjunto de entrenamiento
            y_pred = self.model.predict(X, verbose=0)
            
            # Desnormaliza si es necesario
            if self.scaler is not None:
                y_pred = self.scaler.inverse_transform(y_pred.reshape(-1, 1)).flatten()
                y_true = self.scaler.inverse_transform(y.reshape(-1, 1)).flatten()
            else:
                y_pred = y_pred.flatten()
                y_true = y
            
            self.metrics = self.calculate_metrics(y_true, y_pred)
            
            # Añade métricas específicas del entrenamiento
            final_loss = self.history.history['loss'][-1]
            final_val_loss = self.history.history['val_loss'][-1] if 'val_loss' in self.history.history else None
            
            self.metrics['training_loss'] = final_loss
            if final_val_loss is not None:
                self.metrics['validation_loss'] = final_val_loss
            
            logger.info(f"Modelo LSTM entrenado exitosamente.")
            logger.info(f"R²: {self.metrics['r2']:.3f}, MAE: {self.metrics['mae']:.2f}, MAPE: {self.metrics['mape']:.2f}%")
            logger.info(f"Training Loss: {final_loss:.6f}")
            if final_val_loss:
                logger.info(f"Validation Loss: {final_val_loss:.6f}")
            
            return self
            
        except Exception as e:
            logger.error(f"Error entrenando modelo LSTM: {str(e)}")
            raise
    
    def predict(self, periods: int, confidence_interval: float = 0.95) -> pd.DataFrame:
        """
        Genera pronósticos usando LSTM
        """
        if not self.is_fitted:
            raise ValueError("El modelo debe ser entrenado antes de hacer predicciones")
        
        try:
            sequence_length = self.hyperparameters.get('sequence_length', 30)
            
            # Prepara datos iniciales
            target_values = self.training_data.iloc[:, 0].values.reshape(-1, 1)
            
            if self.scaler is not None:
                target_values = self.scaler.transform(target_values)
            
            # Prepara features adicionales si se usan
            if self.hyperparameters.get('add_features', True):
                # Para predicciones futuras, extendemos las features
                last_date = self.training_data.index[-1]
                future_dates = pd.date_range(
                    start=last_date + pd.Timedelta(days=1),
                    periods=periods,
                    freq='D'
                )
                
                # Crea DataFrame extendido para generar features futuras
                extended_index = self.training_data.index.union(future_dates)
                extended_df = pd.DataFrame(index=extended_index)
                
                # Genera features para todo el período extendido
                all_features = self._create_additional_features(extended_df)
                
                if self.feature_scaler is not None:
                    all_features_scaled = self.feature_scaler.transform(all_features)
                else:
                    all_features_scaled = all_features.values
                
                # Combina datos históricos con features
                historical_features = all_features_scaled[:len(self.training_data)]
                future_features = all_features_scaled[len(self.training_data):]
                
                # Datos históricos combinados
                historical_data = np.column_stack([target_values.flatten(), historical_features])
            else:
                historical_data = target_values
                future_features = None
            
            # Genera predicciones iterativamente
            predictions = []
            current_sequence = historical_data[-sequence_length:].copy()
            
            for i in range(periods):
                # Prepara secuencia para predicción
                sequence_input = current_sequence.reshape(1, sequence_length, -1)
                
                # Hace predicción
                pred = self.model.predict(sequence_input, verbose=0)[0, 0]
                predictions.append(pred)
                
                # Actualiza secuencia para próxima predicción
                if self.hyperparameters.get('add_features', True) and future_features is not None:
                    # Combina predicción con features futuras
                    next_features = future_features[i]
                    next_input = np.concatenate([[pred], next_features])
                else:
                    next_input = np.array([pred])
                
                # Actualiza secuencia deslizante
                current_sequence = np.vstack([current_sequence[1:], next_input.reshape(1, -1)])
            
            # Desnormaliza predicciones
            if self.scaler is not None:
                predictions = self.scaler.inverse_transform(
                    np.array(predictions).reshape(-1, 1)
                ).flatten()
            
            # Asegura valores no negativos
            predictions = np.maximum(predictions, 0)
            
            # Estima intervalos de confianza
            # Para LSTM, usamos la variabilidad histórica como aproximación
            historical_errors = []
            if len(self.training_data) > sequence_length:
                # Calcula errores en predicciones retrospectivas
                for i in range(sequence_length, min(len(self.training_data), sequence_length + 50)):
                    seq_input = historical_data[i-sequence_length:i].reshape(1, sequence_length, -1)
                    pred = self.model.predict(seq_input, verbose=0)[0, 0]
                    
                    if self.scaler is not None:
                        pred = self.scaler.inverse_transform([[pred]])[0, 0]
                        actual = self.scaler.inverse_transform(target_values[i:i+1])[0, 0]
                    else:
                        actual = target_values[i, 0]
                    
                    historical_errors.append(abs(pred - actual))
            
            # Calcula margen de error
            if historical_errors:
                error_std = np.std(historical_errors)
            else:
                error_std = np.std(predictions) * 0.1  # Fallback
            
            z_score = 1.96 if confidence_interval >= 0.95 else 1.645
            margin = z_score * error_std
            
            # Prepara fechas futuras
            last_date = self.training_data.index[-1]
            future_dates = pd.date_range(
                start=last_date + pd.Timedelta(days=1),
                periods=periods,
                freq='D'
            )
            
            # Prepara resultado
            result = pd.DataFrame({
                'date': future_dates,
                'predicted_demand': predictions,
                'lower_bound': np.maximum(predictions - margin, 0),
                'upper_bound': predictions + margin,
                'confidence_level': confidence_interval
            })
            
            result.set_index('date', inplace=True)
            
            logger.info(f"Generados {periods} pronósticos LSTM")
            
            return result
            
        except Exception as e:
            logger.error(f"Error generando pronósticos LSTM: {str(e)}")
            raise
    
    def get_training_history(self) -> Optional[Dict[str, List[float]]]:
        """
        Obtiene el historial de entrenamiento
        """
        if self.history is not None:
            return self.history.history
        return None
    
    def get_model_summary(self) -> Dict[str, Any]:
        """
        Obtiene un resumen del modelo
        """
        if not self.is_fitted:
            return {}
        
        summary = {
            'sequence_length': self.hyperparameters.get('sequence_length', 30),
            'lstm_units': self.hyperparameters.get('lstm_units', [50, 25]),
            'total_parameters': self.model.count_params(),
            'epochs_trained': len(self.history.history['loss']) if self.history else 0,
            'final_loss': self.history.history['loss'][-1] if self.history else None,
            'r2_score': self.metrics.get('r2', 0),
            'mae': self.metrics.get('mae', 0),
            'mape': self.metrics.get('mape', 0)
        }
        
        if self.history and 'val_loss' in self.history.history:
            summary['final_val_loss'] = self.history.history['val_loss'][-1]
        
        return summary
    
    def save_model(self, filepath: str) -> bool:
        """
        Guarda el modelo LSTM entrenado
        """
        if not self.is_fitted:
            return False
        
        try:
            self.model.save(filepath)
            logger.info(f"Modelo LSTM guardado en {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error guardando modelo LSTM: {str(e)}")
            return False
    
    def load_model(self, filepath: str) -> bool:
        """
        Carga un modelo LSTM previamente guardado
        """
        try:
            self.model = tf.keras.models.load_model(filepath)
            self.is_fitted = True
            logger.info(f"Modelo LSTM cargado desde {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error cargando modelo LSTM: {str(e)}")
            return False