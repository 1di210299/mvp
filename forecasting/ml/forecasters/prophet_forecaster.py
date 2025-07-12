import math
import pandas as pd
from typing import Dict, Any
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error
from ml.forecasters.base_forecaster import BaseForecaster
import logging

logger = logging.getLogger(__name__)

class ProphetForecaster(BaseForecaster):
    # ...existing code...
    
    def _calculate_metrics(self, y_true, y_pred):
        """Calcula métricas de evaluación del modelo"""
        mae = mean_absolute_error(y_true, y_pred)
        mape = mean_absolute_percentage_error(y_true, y_pred) * 100
        
        # Handle infinite MAPE values
        if math.isinf(mape) or math.isnan(mape):
            mape = None
            
        return mae, mape
    
    def train(self, df: pd.DataFrame) -> Dict[str, Any]:
        # ...existing code...
        
        # En la parte donde se calculan las métricas
        mae, mape = self._calculate_metrics(y_test, y_pred)
        
        # Log with proper handling of None values
        mape_str = f"{mape:.2f}%" if mape is not None else "N/A"
        logger.info(f"Modelo Prophet entrenado exitosamente. MAE: {mae:.2f}, MAPE: {mape_str}")
        
        return {
            'model': self.model,
            'mae': mae,
            'mape': mape,  # This can now be None
            'train_size': len(train_data),
            'test_size': len(y_test)
        }