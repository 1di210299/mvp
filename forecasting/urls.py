from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'models', views.ForecastModelViewSet)
router.register(r'forecasts', views.DemandForecastViewSet)
router.register(r'reorder-recommendations', views.ReorderRecommendationViewSet)

urlpatterns = [
    # Custom endpoints
    path('predict/', views.PredictDemandView.as_view(), name='predict_demand'),
    path('train-model/', views.TrainModelView.as_view(), name='train_model'),
    path('models/<int:model_id>/accuracy/', views.ModelAccuracyView.as_view(), name='model_accuracy'),
    path('products/<int:product_id>/forecast/', views.ProductForecastView.as_view(), name='product_forecast'),
    path('generate-recommendations/', views.GenerateRecommendationsView.as_view(), name='generate_recommendations'),
    
    # ViewSets
    path('', include(router.urls)),
]
