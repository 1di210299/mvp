# Sistema de Pronósticos con Machine Learning - DataLens

## Descripción General

El sistema de pronósticos de DataLens implementa algoritmos de Machine Learning avanzados para predecir la demanda de productos y generar recomendaciones de reorden inteligentes. Utiliza Prophet de Facebook y ARIMA para crear modelos precisos y robustos.

## Características Principales

### 🤖 Algoritmos de ML Implementados

1. **Prophet (Facebook)**
   - Manejo automático de estacionalidad
   - Detección de tendencias
   - Robustez ante datos faltantes
   - Intervalos de confianza

2. **ARIMA (AutoRegressive Integrated Moving Average)**
   - Selección automática de parámetros (auto_arima)
   - Análisis de series temporales clásico
   - Validación estadística

3. **Ensemble (Combinación)**
   - Combina Prophet y ARIMA
   - Ponderación inteligente por precisión
   - Mayor robustez y precisión

### 📊 Servicios Principales

#### MLModelService
- Entrenamiento automático de modelos
- Gestión del ciclo de vida de modelos
- Optimización de hiperparámetros
- Reentrenamiento programado

#### ForecastService
- Generación de pronósticos
- Cálculo de intervalos de confianza
- Recomendaciones de reorden
- Agregación de predicciones

#### EvaluationService
- Métricas de precisión (MAPE, MAE, RMSE)
- Comparación de modelos
- Reportes de rendimiento
- Validación cruzada

## APIs Disponibles

### 1. Gestión de Modelos

#### Listar Modelos
```http
GET /api/forecasting/models/
```

**Parámetros de consulta:**
- `algorithm`: prophet, arima, ensemble
- `is_active`: true/false
- `product_id`: ID del producto

**Respuesta:**
```json
{
  "count": 10,
  "results": [
    {
      "id": 1,
      "name": "Product ABC - Prophet Model",
      "algorithm": "prophet",
      "algorithm_display": "Prophet",
      "product": 123,
      "accuracy_percentage": 85.5,
      "is_active": true,
      "created_at": "2024-01-15T10:30:00Z",
      "last_trained_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

#### Entrenar Modelos (Masivo)
```http
POST /api/forecasting/models/train_models/
```

**Payload:**
```json
{
  "product_ids": [123, 456, 789],
  "algorithm": "ensemble",
  "retrain_existing": false,
  "async_training": true
}
```

**Respuesta:**
```json
{
  "message": "Entrenamiento de modelos iniciado en segundo plano",
  "task_id": "abc123-def456",
  "status": "started"
}
```

#### Comparar Modelos
```http
GET /api/forecasting/models/comparison/?product_id=123
```

**Respuesta:**
```json
{
  "comparison": [
    {
      "model_id": 1,
      "model_name": "Prophet Model",
      "algorithm": "prophet",
      "product_name": "Product ABC",
      "accuracy_metrics": {
        "mape": 14.5,
        "mae": 5.2,
        "rmse": 7.8
      },
      "training_time": 45.2,
      "last_trained": "2024-01-15T10:30:00Z"
    }
  ]
}
```

### 2. Generación de Pronósticos

#### Predecir Demanda
```http
POST /api/forecasting/predict/
```

**Payload:**
```json
{
  "product_ids": [123, 456],
  "forecast_horizon": 30,
  "include_confidence_intervals": true
}
```

**Respuesta:**
```json
{
  "message": "Pronósticos generados para 2 productos",
  "results": [
    {
      "product_id": 123,
      "product_name": "Product ABC",
      "forecasts_count": 30,
      "status": "success"
    }
  ],
  "forecast_horizon_days": 30
}
```

#### Obtener Pronósticos
```http
GET /api/forecasting/forecasts/?product_id=123
```

**Respuesta:**
```json
{
  "count": 30,
  "results": [
    {
      "id": 1,
      "product": 123,
      "product_name": "Product ABC",
      "model_name": "Prophet Model",
      "forecast_date": "2024-01-16",
      "predicted_demand": 15.5,
      "confidence_interval_display": "12.3 - 18.7",
      "accuracy_score": 0.85
    }
  ]
}
```

### 3. Recomendaciones de Reorden

#### Generar Recomendaciones
```http
POST /api/forecasting/generate-recommendations/
```

**Payload:**
```json
{
  "product_ids": [123, 456]
}
```

**Respuesta:**
```json
{
  "message": "Recomendaciones generadas para 2 productos",
  "recommendations": [
    {
      "product_id": 123,
      "product_name": "Product ABC",
      "recommendation_id": 1,
      "urgency": "high",
      "quantity": 100.0
    }
  ]
}
```

#### Listar Recomendaciones
```http
GET /api/forecasting/reorder-recommendations/?urgency=high
```

**Respuesta:**
```json
{
  "count": 5,
  "results": [
    {
      "id": 1,
      "product": 123,
      "product_name": "Product ABC",
      "current_stock": 25,
      "recommended_order_quantity": 100,
      "urgency": "high",
      "urgency_display": "Alta",
      "estimated_stockout_date": "2024-01-20",
      "reason": "High demand forecast indicates potential stockout"
    }
  ]
}
```

### 4. Análisis por Producto

#### Resumen Completo de Producto
```http
GET /api/forecasting/products/123/forecast/
```

**Respuesta:**
```json
{
  "product_id": 123,
  "product_name": "Product ABC",
  "product_sku": "ABC001",
  "current_stock": 75.5,
  "forecasts": [...],
  "recommendations": [...],
  "best_model": {
    "id": 1,
    "name": "Prophet Model",
    "algorithm": "prophet",
    "accuracy_percentage": 85.5
  },
  "chart_data": {
    "dates": [...],
    "historical_demand": [...],
    "predicted_demand": [...],
    "confidence_lower": [...],
    "confidence_upper": [...]
  }
}
```

### 5. Evaluación de Modelos

#### Precisión de Modelo
```http
GET /api/forecasting/models/1/accuracy/
```

**Respuesta:**
```json
{
  "model_id": 1,
  "model_name": "Prophet Model",
  "algorithm": "prophet",
  "product": {
    "id": 123,
    "name": "Product ABC",
    "sku": "ABC001"
  },
  "accuracy_metrics": {
    "mape": 14.5,
    "mae": 5.2,
    "rmse": 7.8,
    "accuracy_percentage": 85.5
  },
  "detailed_report": {
    "validation_period": 30,
    "predictions_count": 30,
    "mean_error": 2.1,
    "std_error": 3.5
  },
  "last_trained": "2024-01-15T10:30:00Z"
}
```

## Comandos de Administración

### Entrenar Modelos desde CLI

```bash
# Entrenar todos los modelos
python manage.py train_ml_models

# Entrenar productos específicos
python manage.py train_ml_models --products 123,456,789

# Entrenar con algoritmo específico
python manage.py train_ml_models --algorithm prophet

# Re-entrenar modelos existentes
python manage.py train_ml_models --retrain-existing

# Entrenamiento con configuración personalizada
python manage.py train_ml_models --algorithm ensemble --products 123 --retrain-existing --verbose
```

### Evaluar Modelos desde CLI

```bash
# Evaluar todos los modelos
python manage.py evaluate_ml_models

# Evaluar modelos de productos específicos
python manage.py evaluate_ml_models --products 123,456

# Generar reporte completo
python manage.py evaluate_ml_models --generate-report

# Comparar algoritmos
python manage.py evaluate_ml_models --compare-algorithms
```

## Tareas Celery (Procesamiento Asíncrono)

### Tareas Disponibles

1. **train_ml_models_task**: Entrenamiento masivo de modelos
2. **generate_forecasts_task**: Generación de pronósticos
3. **evaluate_models_task**: Evaluación de modelos
4. **compare_models_task**: Comparación de algoritmos

### Monitoreo de Tareas

```python
from forecasting.tasks import train_ml_models_task

# Iniciar tarea
task = train_ml_models_task.delay(company_id=1, algorithm='prophet')

# Verificar estado
print(task.status)  # PENDING, STARTED, SUCCESS, FAILURE

# Obtener resultado
result = task.get()
```

## Configuración

### Variables de Configuración (settings.py)

```python
# Configuración de Machine Learning
ML_CONFIG = {
    'MODEL_STORAGE_PATH': os.path.join(BASE_DIR, 'ml_models'),
    'EXPERIMENTS_PATH': os.path.join(BASE_DIR, 'ml_experiments'),
    'CHARTS_PATH': os.path.join(MEDIA_ROOT, 'forecast_charts'),
    
    'PROPHET_PARAMS': {
        'daily_seasonality': True,
        'weekly_seasonality': True,
        'yearly_seasonality': True,
        'seasonality_mode': 'multiplicative',
        'interval_width': 0.95,
        'changepoint_prior_scale': 0.05
    },
    
    'ARIMA_PARAMS': {
        'max_p': 5,
        'max_d': 2,
        'max_q': 5,
        'seasonal': True,
        'stepwise': True,
        'suppress_warnings': True,
        'error_action': 'ignore'
    },
    
    'ENSEMBLE_PARAMS': {
        'min_models': 2,
        'weight_by_accuracy': True,
        'accuracy_threshold': 0.7
    }
}

# Configuración de pronósticos
FORECAST_CONFIG = {
    'DEFAULT_HORIZON_DAYS': 30,
    'MAX_HORIZON_DAYS': 365,
    'MIN_HISTORICAL_DAYS': 60,
    'CONFIDENCE_INTERVAL': 0.95,
    'REORDER_URGENCY_THRESHOLDS': {
        'high': 7,    # días hasta stockout
        'medium': 14,
        'low': 30
    }
}
```

### Dependencias Requeridas

```txt
# Machine Learning
prophet>=1.1.4
statsmodels>=0.14.0
pmdarima>=2.0.3

# Visualización
matplotlib>=3.7.0
seaborn>=0.12.0
plotly>=5.15.0

# Utilidades ML
joblib>=1.3.0
numpy>=1.24.0
pandas>=2.0.0
scikit-learn>=1.3.0
```

## Métricas de Evaluación

### MAPE (Mean Absolute Percentage Error)
- **Ideal**: < 10%
- **Bueno**: 10-20%
- **Aceptable**: 20-30%
- **Pobre**: > 30%

### MAE (Mean Absolute Error)
- Error promedio absoluto en unidades originales
- Más interpretable que RMSE

### RMSE (Root Mean Square Error)
- Penaliza más los errores grandes
- Útil para detectar outliers

## Casos de Uso Comunes

### 1. Configuración Inicial

```python
# 1. Entrenar modelos para todos los productos
from forecasting.services.ml_model_service import MLModelService

ml_service = MLModelService()
results = ml_service.train_models_for_company(company)

# 2. Generar pronósticos iniciales
from forecasting.services.forecast_service import ForecastService

forecast_service = ForecastService()
for product in company.products.filter(is_active=True):
    forecast_service.generate_forecasts(product, days=30)
```

### 2. Monitoreo y Reentrenamiento

```python
# Evaluar modelos existentes
from forecasting.services.evaluation_service import EvaluationService

eval_service = EvaluationService()
report = eval_service.generate_performance_report(company)

# Re-entrenar modelos con baja precisión
for model in report['underperforming_models']:
    ml_service.retrain_model(model)
```

### 3. Integración con Frontend

```javascript
// Obtener pronósticos para dashboard
fetch('/api/forecasting/products/123/forecast/')
  .then(response => response.json())
  .then(data => {
    // Mostrar gráficos de pronóstico
    renderForecastChart(data.chart_data);
    
    // Mostrar recomendaciones
    displayRecommendations(data.recommendations);
  });

// Entrenar modelos desde UI
const trainModels = async (productIds, algorithm) => {
  const response = await fetch('/api/forecasting/models/train_models/', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      product_ids: productIds,
      algorithm: algorithm,
      async_training: true
    })
  });
  
  const result = await response.json();
  // Mostrar progreso o resultado
  return result;
};
```

## Troubleshooting

### Problemas Comunes

1. **Error de datos insuficientes**
   - Verificar que haya al menos 60 días de transacciones
   - Revisar que las transacciones tengan fechas válidas

2. **Modelos con baja precisión**
   - Aumentar periodo de entrenamiento
   - Ajustar hiperparámetros
   - Considerar factores externos (promociones, estacionalidad)

3. **Predicciones inconsistentes**
   - Validar calidad de datos históricos
   - Revisar outliers en las transacciones
   - Evaluar cambios en patrones de demanda

### Logs y Debugging

```python
import logging

# Configurar logging para ML
logging.getLogger('forecasting.ml_algorithms').setLevel(logging.DEBUG)
logging.getLogger('forecasting.services').setLevel(logging.INFO)

# Ver logs específicos
logger = logging.getLogger('forecasting.ml_algorithms.prophet_forecaster')
logger.info("Iniciando entrenamiento de Prophet...")
```

## Roadmap y Mejoras Futuras

### Próximas Características

1. **Algoritmos Adicionales**
   - LSTM (Long Short-Term Memory)
   - XGBoost para series temporales
   - Transformer models

2. **Factores Externos**
   - Integración con datos de clima
   - Eventos especiales y promociones
   - Análisis de sentimientos de mercado

3. **Optimización**
   - Auto-tuning de hiperparámetros
   - Ensemble adaptativo
   - Detección automática de anomalías

4. **Visualización Avanzada**
   - Dashboards interactivos
   - Mapas de calor de precisión
   - Análisis de contribución de factores

## Soporte

Para soporte técnico o preguntas sobre el sistema de pronósticos:
- Documentación técnica: `/docs/forecasting/`
- Logs del sistema: `/logs/forecasting.log`
- Tests: `python manage.py test forecasting`
