from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error
import numpy as np
import pandas as pd
from typing import Dict, Any
from my_logging_module import logger  # Adjust the import based on your project structure
from base_forecaster import BaseForecaster  # Adjust the import based on your project structure

class LinearRegressionForecaster(BaseForecaster):
    """Simple linear regression forecaster for basic trend analysis"""
    
    def __init__(self):
        super().__init__()
        self.model = LinearRegression()
        self.scaler = StandardScaler()
        
    def train(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Entrena el modelo de regresión lineal"""
        logger.info(f"Entrenando modelo Linear Regression con {len(df)} observaciones")
        
        # Prepare features (just time index for simple trend)
        X = np.arange(len(df)).reshape(-1, 1)
        y = df['y'].values
        
        # Split data
        split_idx = int(len(df) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train model
        self.model.fit(X_train_scaled, y_train)
        
        # Make predictions
        y_pred = self.model.predict(X_test_scaled)
        
        # Calculate metrics
        mae, mape = self._calculate_metrics(y_test, y_pred)
        
        mape_str = f"{mape:.2f}%" if mape is not None else "N/A"
        logger.info(f"Modelo Linear Regression entrenado exitosamente. MAE: {mae:.2f}, MAPE: {mape_str}")
        
        return {
            'model': self.model,
            'scaler': self.scaler,
            'mae': mae,
            'mape': mape,
            'train_size': len(y_train),
            'test_size': len(y_test)
        }
    
    def _calculate_metrics(self, y_true, y_pred):
        """Calculate evaluation metrics"""
        mae = mean_absolute_error(y_true, y_pred)
        
        # Calculate MAPE safely
        mask = y_true != 0
        if mask.sum() > 0:
            mape = np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100
            if np.isinf(mape) or np.isnan(mape):
                mape = None
        else:
            mape = None
            
        return mae, mape

class ModelTrainer:
    # ...existing code...
    
    def __init__(self):
        self.forecasters = {
            'prophet': ProphetForecaster,
            'arima': ARIMAForecaster,
            'ensemble': EnsembleForecaster,
            'linear_regression': LinearRegressionForecaster,
        }