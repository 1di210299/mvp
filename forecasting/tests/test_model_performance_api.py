"""
Tests para el endpoint de Model Performance
"""

import pytest
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone

from authentication.models import User, Company
from inventory.models import Product, Category, Location
from forecasting.models import ForecastModel, DemandForecast, ForecastAccuracy


class ModelPerformanceAPITest(TestCase):
    """Tests para el endpoint de performance de modelos"""
    
    def setUp(self):
        """Setup inicial para los tests"""
        self.client = APIClient()
        
        # Crear empresa de prueba primero
        self.company = Company.objects.create(
            name='Test Company',
            ruc='12345678901',
            address='Test Address',
            email='company@test.com',
            is_active=True
        )
        
        # Crear usuario y empresa de prueba
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            company=self.company
        )
        
        # Autenticar cliente
        self.client.force_authenticate(user=self.user)
        
        # Crear categoría y ubicación
        self.category = Category.objects.create(
            name='Test Category'
        )
        
        self.location = Location.objects.create(
            name='Test Location',
            code='TEST_LOC',
            warehouse='Test Warehouse',
            is_active=True
        )
        
        # Crear productos de prueba
        self.product1 = Product.objects.create(
            name='Test Product 1',
            sku='TEST001',
            category=self.category,
            company=self.company,
            sale_price=Decimal('10.00'),
            is_active=True
        )
        
        self.product2 = Product.objects.create(
            name='Test Product 2',
            sku='TEST002',
            category=self.category,
            company=self.company,
            sale_price=Decimal('15.00'),
            is_active=True
        )
        
        # Crear modelos de prueba con métricas
        self.model1 = ForecastModel.objects.create(
            name='Prophet Model',
            company=self.company,
            model_type='prophet',
            status='active',
            mae=Decimal('2.5'),
            mape=Decimal('15.2'),
            rmse=Decimal('3.1'),
            r2_score=Decimal('0.85'),
            training_completed_at=timezone.now() - timedelta(days=1)
        )
        self.model1.products.add(self.product1)
        
        self.model2 = ForecastModel.objects.create(
            name='ARIMA Model',
            company=self.company,
            model_type='arima',
            status='active',
            mae=Decimal('3.2'),
            mape=Decimal('18.5'),
            rmse=Decimal('4.0'),
            r2_score=Decimal('0.78'),
            training_completed_at=timezone.now() - timedelta(days=2)
        )
        self.model2.products.add(self.product2)
        
        # Crear pronósticos de prueba
        forecast_date = timezone.now().date() - timedelta(days=3)
        self.forecast1 = DemandForecast.objects.create(
            model=self.model1,
            product=self.product1,
            location=self.location,
            forecast_date=forecast_date,
            predicted_demand=Decimal('100.0'),
            lower_bound=Decimal('80.0'),
            upper_bound=Decimal('120.0'),
            confidence_level=Decimal('95.0')
        )
        
        # Crear registro de precisión
        self.accuracy1 = ForecastAccuracy.objects.create(
            forecast=self.forecast1,
            actual_demand=Decimal('95.0'),
            absolute_error=Decimal('5.0'),
            percentage_error=Decimal('5.26'),
            within_bounds=True,
            bias=Decimal('5.26')
        )
        
        # URL del endpoint
        self.url = reverse('model_performance')
    
    def test_get_all_models_performance(self):
        """Test obtener performance de todos los modelos"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        
        # Verificar estructura de respuesta
        self.assertIn('overall_metrics', data)
        self.assertIn('models_performance', data)
        self.assertIn('evaluation_period_days', data)
        self.assertIn('generated_at', data)
        
        # Verificar métricas generales
        overall_metrics = data['overall_metrics']
        self.assertEqual(overall_metrics['total_models'], 2)
        self.assertEqual(overall_metrics['active_models'], 2)
        self.assertIsNotNone(overall_metrics['average_mae'])
        self.assertIsNotNone(overall_metrics['average_mape'])
        self.assertIsNotNone(overall_metrics['average_rmse'])
        self.assertIsNotNone(overall_metrics['average_r2'])
        self.assertIsNotNone(overall_metrics['best_performing_model'])
        
        # Verificar mejor modelo (debe ser model1 con mejor R²)
        best_model = overall_metrics['best_performing_model']
        self.assertEqual(best_model['model_id'], self.model1.id)
        self.assertEqual(best_model['model_name'], 'Prophet Model')
        self.assertEqual(best_model['r2_score'], 0.85)
        
        # Verificar datos de modelos individuales
        models_performance = data['models_performance']
        self.assertEqual(len(models_performance), 2)
        
        # Verificar que los modelos están ordenados por fecha de entrenamiento
        model_data = models_performance[0]
        self.assertIn('model_id', model_data)
        self.assertIn('model_name', model_data)
        self.assertIn('model_type', model_data)
        self.assertIn('status', model_data)
        self.assertIn('metrics', model_data)
        
        # Verificar métricas del modelo
        metrics = model_data['metrics']
        self.assertIn('mae', metrics)
        self.assertIn('mape', metrics)
        self.assertIn('rmse', metrics)
        self.assertIn('r2_score', metrics)
    
    def test_get_specific_model_performance(self):
        """Test obtener performance de un modelo específico"""
        response = self.client.get(self.url, {'model_id': self.model1.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        
        # Verificar estructura de respuesta
        self.assertIn('performance', data)
        self.assertIn('evaluation_period_days', data)
        self.assertIn('generated_at', data)
        
        # Verificar datos del modelo
        performance = data['performance']
        self.assertEqual(performance['model_id'], self.model1.id)
        self.assertEqual(performance['model_name'], 'Prophet Model')
        self.assertEqual(performance['model_type'], 'prophet')
        self.assertEqual(performance['status'], 'active')
        
        # Verificar métricas almacenadas
        stored_metrics = performance['stored_metrics']
        self.assertEqual(stored_metrics['mae'], 2.5)
        self.assertEqual(stored_metrics['mape'], 15.2)
        self.assertEqual(stored_metrics['rmse'], 3.1)
        self.assertEqual(stored_metrics['r2_score'], 0.85)
        
        # Verificar que incluye métricas en tiempo real por defecto
        self.assertIn('realtime_metrics', performance)
    
    def test_get_performance_without_realtime(self):
        """Test obtener performance sin métricas en tiempo real"""
        response = self.client.get(self.url, {
            'model_id': self.model1.id,
            'include_realtime': 'false'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        performance = data['performance']
        
        # No debe incluir métricas en tiempo real
        self.assertNotIn('realtime_metrics', performance)
    
    def test_get_performance_custom_days_back(self):
        """Test obtener performance con período personalizado"""
        response = self.client.get(self.url, {'days_back': 7})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data['evaluation_period_days'], 7)
    
    def test_get_nonexistent_model_performance(self):
        """Test obtener performance de modelo inexistente"""
        response = self.client.get(self.url, {'model_id': 99999})
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        data = response.json()
        self.assertIn('error', data)
        self.assertIn('no encontrado', data['error'])
    
    def test_get_performance_invalid_model_id(self):
        """Test obtener performance con model_id inválido"""
        response = self.client.get(self.url, {'model_id': 'invalid'})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        data = response.json()
        self.assertIn('error', data)
        self.assertIn('número entero válido', data['error'])
    
    def test_unauthorized_access(self):
        """Test acceso no autorizado"""
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_performance_with_no_models(self):
        """Test performance cuando no hay modelos"""
        # Eliminar todos los modelos
        ForecastModel.objects.all().delete()
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        overall_metrics = data['overall_metrics']
        
        self.assertEqual(overall_metrics['total_models'], 0)
        self.assertEqual(overall_metrics['active_models'], 0)
        self.assertEqual(len(data['models_performance']), 0)
    
    def test_performance_different_company_isolation(self):
        """Test que los modelos están aislados por empresa"""
        # Crear otra empresa y usuario
        other_company = Company.objects.create(
            name='Other Company',
            ruc='98765432109',
            address='Other Address',
            email='other@test.com',
            is_active=True
        )
        
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123',
            company=other_company
        )
        
        # Autenticar con el otro usuario
        self.client.force_authenticate(user=other_user)
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        # No debe ver los modelos de la primera empresa
        self.assertEqual(data['overall_metrics']['total_models'], 0)
        self.assertEqual(len(data['models_performance']), 0)


@pytest.mark.django_db
class TestModelPerformanceIntegration:
    """Tests de integración para el endpoint de model performance"""
    
    def test_performance_endpoint_url_resolution(self):
        """Test que la URL se resuelve correctamente"""
        url = reverse('model_performance')
        assert url == '/api/forecasting/model-performance/'
    
    def test_performance_with_filter_parameters(self, client, django_user_model):
        """Test performance con múltiples parámetros de filtro"""
        # Este test verificaría casos más complejos de filtrado
        # Se puede expandir según necesidades específicas
        pass
