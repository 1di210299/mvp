from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import json

from authentication.models import Company
from inventory.models import Product, Category, Transaction
from .models import ForecastModel, DemandForecast, ReorderRecommendation
from .services.ml_model_service import MLModelService
from .services.forecast_service import ForecastService
from .services.evaluation_service import EvaluationService

User = get_user_model()


class MLModelServiceTest(TestCase):
    """Tests para el servicio de modelos ML"""
    
    def setUp(self):
        self.company = Company.objects.create(
            name="Test Company",
            ruc="12345678901"
        )
        self.user = User.objects.create_user(
            email="test@test.com",
            password="testpass123",
            company=self.company
        )
        self.category = Category.objects.create(
            company=self.company,
            name="Test Category"
        )
        self.product = Product.objects.create(
            company=self.company,
            sku="TEST001",
            name="Test Product",
            category=self.category,
            cost_price=10.00,
            sale_price=15.00
        )
        
        # Crear transacciones de prueba
        base_date = datetime.now() - timedelta(days=100)
        for i in range(50):
            Transaction.objects.create(
                company=self.company,
                transaction_type='sale',
                reference_number=f"SALE{i:03d}",
                product=self.product,
                location_id=1,  # Asumiendo que existe una ubicación
                quantity=10 + (i % 5),
                unit_cost=10.00,
                transaction_date=base_date + timedelta(days=i*2),
                user=self.user
            )
    
    def test_ml_model_service_initialization(self):
        """Test inicialización del servicio ML"""
        service = MLModelService()
        self.assertIsNotNone(service)
    
    @patch('forecasting.ml_algorithms.prophet_forecaster.ProphetForecaster.train')
    def test_train_prophet_model(self, mock_train):
        """Test entrenamiento de modelo Prophet"""
        mock_train.return_value = {'accuracy': 0.85, 'mape': 15.0}
        
        service = MLModelService()
        model = service.train_model_for_product(self.product, 'prophet')
        
        self.assertIsNotNone(model)
        self.assertEqual(model.algorithm, 'prophet')
        self.assertEqual(model.product, self.product)
        mock_train.assert_called_once()
    
    @patch('forecasting.ml_algorithms.arima_forecaster.ARIMAForecaster.train')
    def test_train_arima_model(self, mock_train):
        """Test entrenamiento de modelo ARIMA"""
        mock_train.return_value = {'accuracy': 0.80, 'mape': 20.0}
        
        service = MLModelService()
        model = service.train_model_for_product(self.product, 'arima')
        
        self.assertIsNotNone(model)
        self.assertEqual(model.algorithm, 'arima')
        self.assertEqual(model.product, self.product)
        mock_train.assert_called_once()


class ForecastServiceTest(TestCase):
    """Tests para el servicio de pronósticos"""
    
    def setUp(self):
        self.company = Company.objects.create(
            name="Test Company",
            ruc="12345678901"
        )
        self.user = User.objects.create_user(
            email="test@test.com",
            password="testpass123",
            company=self.company
        )
        self.category = Category.objects.create(
            company=self.company,
            name="Test Category"
        )
        self.product = Product.objects.create(
            company=self.company,
            sku="TEST001",
            name="Test Product",
            category=self.category,
            cost_price=10.00,
            sale_price=15.00,
            min_stock=50,
            reorder_point=100
        )
        self.model = ForecastModel.objects.create(
            product=self.product,
            name="Test Prophet Model",
            algorithm='prophet',
            parameters={'seasonality_mode': 'multiplicative'},
            accuracy_metrics={'mape': 15.0, 'mae': 5.0}
        )
    
    @patch('forecasting.ml_algorithms.prophet_forecaster.ProphetForecaster.predict')
    def test_generate_forecasts(self, mock_predict):
        """Test generación de pronósticos"""
        # Mock de predicciones
        mock_predict.return_value = {
            'dates': [(datetime.now() + timedelta(days=i)).date() for i in range(1, 31)],
            'predictions': [15.0 + i*0.5 for i in range(30)],
            'confidence_intervals': {
                'lower': [10.0 + i*0.3 for i in range(30)],
                'upper': [20.0 + i*0.7 for i in range(30)]
            }
        }
        
        service = ForecastService()
        forecasts = service.generate_forecasts(self.product, 30, True)
        
        self.assertIsNotNone(forecasts)
        self.assertGreater(len(forecasts), 0)
        mock_predict.assert_called_once()
    
    def test_generate_reorder_recommendations(self):
        """Test generación de recomendaciones de reorden"""
        # Crear pronósticos que indiquen alta demanda
        for i in range(5):
            DemandForecast.objects.create(
                product=self.product,
                model=self.model,
                forecast_date=(datetime.now() + timedelta(days=i+1)).date(),
                forecast_horizon_days=30,
                predicted_demand=25.0,  # Demanda alta
                confidence_interval={'lower': 20.0, 'upper': 30.0},
                accuracy_score=0.85
            )
        
        service = ForecastService()
        recommendations = service.generate_reorder_recommendations(self.product)
        
        self.assertIsNotNone(recommendations)


class EvaluationServiceTest(TestCase):
    """Tests para el servicio de evaluación"""
    
    def setUp(self):
        self.company = Company.objects.create(
            name="Test Company",
            ruc="12345678901"
        )
        self.user = User.objects.create_user(
            email="test@test.com",
            password="testpass123",
            company=self.company
        )
        self.category = Category.objects.create(
            company=self.company,
            name="Test Category"
        )
        self.product = Product.objects.create(
            company=self.company,
            sku="TEST001",
            name="Test Product",
            category=self.category,
            cost_price=10.00,
            sale_price=15.00
        )
        self.model = ForecastModel.objects.create(
            product=self.product,
            name="Test Model",
            algorithm='prophet',
            parameters={},
            accuracy_metrics={'mape': 15.0, 'mae': 5.0, 'rmse': 7.5}
        )
    
    def test_evaluate_model_accuracy(self):
        """Test evaluación de precisión de modelo"""
        service = EvaluationService()
        report = service.evaluate_model_accuracy(self.model)
        
        self.assertIsNotNone(report)
        self.assertIn('accuracy_metrics', report)
        self.assertIn('mape', report['accuracy_metrics'])


class ForecastingAPITest(APITestCase):
    """Tests para las APIs de pronósticos"""
    
    def setUp(self):
        self.company = Company.objects.create(
            name="Test Company",
            ruc="12345678901"
        )
        self.user = User.objects.create_user(
            email="test@test.com",
            password="testpass123",
            company=self.company
        )
        self.category = Category.objects.create(
            company=self.company,
            name="Test Category"
        )
        self.product = Product.objects.create(
            company=self.company,
            sku="TEST001",
            name="Test Product",
            category=self.category,
            cost_price=10.00,
            sale_price=15.00
        )
        self.model = ForecastModel.objects.create(
            product=self.product,
            name="Test Model",
            algorithm='prophet',
            parameters={},
            accuracy_metrics={'mape': 15.0}
        )
        
        # Autenticar usuario
        self.client.force_authenticate(user=self.user)
    
    def test_forecast_models_list(self):
        """Test listado de modelos de pronóstico"""
        url = reverse('forecastmodel-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_forecast_models_filter_by_algorithm(self):
        """Test filtrado de modelos por algoritmo"""
        url = reverse('forecastmodel-list')
        response = self.client.get(url, {'algorithm': 'prophet'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    @patch('forecasting.services.ml_model_service.MLModelService.train_model_for_product')
    def test_train_model_api(self, mock_train):
        """Test API de entrenamiento de modelos"""
        mock_train.return_value = self.model
        
        url = reverse('train_model')
        data = {
            'product_ids': [self.product.id],
            'algorithm': 'prophet',
            'retrain_existing': False,
            'async_training': False
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        mock_train.assert_called()
    
    @patch('forecasting.services.forecast_service.ForecastService.generate_forecasts')
    def test_predict_demand_api(self, mock_generate):
        """Test API de predicción de demanda"""
        mock_generate.return_value = [
            DemandForecast(
                product=self.product,
                model=self.model,
                forecast_date=datetime.now().date(),
                predicted_demand=15.0
            )
        ]
        
        url = reverse('predict_demand')
        data = {
            'product_ids': [self.product.id],
            'forecast_horizon': 30,
            'include_confidence_intervals': True
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        mock_generate.assert_called()
    
    def test_model_accuracy_api(self):
        """Test API de precisión de modelo"""
        url = reverse('model_accuracy', kwargs={'model_id': self.model.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['model_id'], self.model.id)
        self.assertIn('accuracy_metrics', response.data)
    
    def test_product_forecast_api(self):
        """Test API de pronósticos por producto"""
        url = reverse('product_forecast', kwargs={'product_id': self.product.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['product_id'], self.product.id)
        self.assertIn('forecasts', response.data)
    
    @patch('forecasting.services.forecast_service.ForecastService.generate_reorder_recommendations')
    def test_generate_recommendations_api(self, mock_generate):
        """Test API de generación de recomendaciones"""
        mock_generate.return_value = [
            ReorderRecommendation(
                product=self.product,
                current_stock=50,
                recommended_order_quantity=100,
                urgency='medium'
            )
        ]
        
        url = reverse('generate_recommendations')
        data = {'product_ids': [self.product.id]}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        mock_generate.assert_called()
    
    def test_unauthorized_access(self):
        """Test acceso no autorizado"""
        self.client.force_authenticate(user=None)
        
        url = reverse('forecastmodel-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ModelIntegrationTest(TestCase):
    """Tests de integración entre modelos"""
    
    def setUp(self):
        self.company = Company.objects.create(
            name="Test Company",
            ruc="12345678901"
        )
        self.user = User.objects.create_user(
            email="test@test.com",
            password="testpass123",
            company=self.company
        )
        self.category = Category.objects.create(
            company=self.company,
            name="Test Category"
        )
        self.product = Product.objects.create(
            company=self.company,
            sku="TEST001",
            name="Test Product",
            category=self.category,
            cost_price=10.00,
            sale_price=15.00
        )
    
    def test_forecast_model_creation(self):
        """Test creación de modelo de pronóstico"""
        model = ForecastModel.objects.create(
            product=self.product,
            name="Integration Test Model",
            algorithm='prophet',
            parameters={'seasonality_mode': 'additive'},
            accuracy_metrics={'mape': 12.5}
        )
        
        self.assertEqual(model.product, self.product)
        self.assertEqual(model.algorithm, 'prophet')
        self.assertTrue(model.is_active)
    
    def test_demand_forecast_creation(self):
        """Test creación de pronóstico de demanda"""
        model = ForecastModel.objects.create(
            product=self.product,
            name="Test Model",
            algorithm='prophet',
            parameters={},
            accuracy_metrics={}
        )
        
        forecast = DemandForecast.objects.create(
            product=self.product,
            model=model,
            forecast_date=datetime.now().date(),
            forecast_horizon_days=30,
            predicted_demand=15.5,
            confidence_interval={'lower': 10.0, 'upper': 20.0},
            accuracy_score=0.88
        )
        
        self.assertEqual(forecast.product, self.product)
        self.assertEqual(forecast.model, model)
        self.assertEqual(forecast.predicted_demand, 15.5)
    
    def test_reorder_recommendation_creation(self):
        """Test creación de recomendación de reorden"""
        recommendation = ReorderRecommendation.objects.create(
            product=self.product,
            current_stock=25,
            recommended_order_quantity=75,
            urgency='high',
            estimated_stockout_date=datetime.now().date() + timedelta(days=5),
            reason="High demand forecast indicates potential stockout"
        )
        
        self.assertEqual(recommendation.product, self.product)
        self.assertEqual(recommendation.urgency, 'high')
        self.assertEqual(recommendation.recommended_order_quantity, 75)
