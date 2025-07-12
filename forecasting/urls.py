from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'models', views.ForecastModelViewSet, basename='forecastmodel')
router.register(r'forecasts', views.DemandForecastViewSet, basename='demandforecast')
router.register(r'reorder-recommendations', views.ReorderRecommendationViewSet, basename='reorderrecommendation')

urlpatterns = [
    # ML Model Management
    path('predict/', views.PredictDemandView.as_view(), name='predict_demand'),
    path('train-model/', views.TrainModelView.as_view(), name='train_model'),
    path('models/<int:model_id>/accuracy/', views.ModelAccuracyView.as_view(), name='model_accuracy'),
    path('generate-recommendations/', views.GenerateRecommendationsView.as_view(), name='generate_recommendations'),
    
    # Product-specific endpoints
    path('products/<int:product_id>/forecast/', views.ProductForecastView.as_view(), name='product_forecast'),
    
    # Gráficos de pronósticos
    path('charts/demand/', views.DemandForecastChartView.as_view(), name='demand-forecast-chart'),
    path('charts/models/', views.ModelComparisonChartView.as_view(), name='model-comparison-chart'),
    path('data/', views.ForecastDataView.as_view(), name='forecast-data'),

    # Bulk operations (available through viewset actions)
    # /api/forecasting/models/train_models/ - POST para entrenamiento masivo
    # /api/forecasting/models/comparison/ - GET para comparación de modelos
    
    # ViewSets (include CRUD operations)
    path('', include(router.urls)),
]
