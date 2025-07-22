"""
Tests para OAuth2 y configuración de tenants
"""
import json
from django.test import TestCase, Client
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from authentication.models import User, Company
from inventory.models import TenantConfig
from oauth2_provider.models import Application


class TenantConfigOAuth2Tests(APITestCase):
    """Tests para configuración OAuth2 de tenants"""
    
    def setUp(self):
        """Setup inicial para tests"""
        # Crear company y user
        self.company = Company.objects.create(
            name="Test Company",
            subscription_type="basic",
            is_active=True
        )
        
        self.user = User.objects.create_user(
            username="testuser@example.com",
            email="testuser@example.com",
            password="testpass123",
            company=self.company
        )
        
        # Crear configuración OAuth2
        self.oauth_app = Application.objects.create(
            name="Test n8n Integration",
            client_type=Application.CLIENT_CONFIDENTIAL,
            authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE,
        )
        
        # Crear configuración de tenant
        self.tenant_config = TenantConfig.objects.create(
            company=self.company,
            oauth2_client_id=self.oauth_app.client_id,
            oauth2_client_secret=self.oauth_app.client_secret,
            oauth2_token_url="http://testserver/oauth/token/",
            is_whatsapp_active=True,
            is_gmail_active=False,
            twilio_account_sid="test_sid",
            twilio_auth_token="test_token",
            whatsapp_from_number="+1234567890"
        )
    
    def test_get_tenant_config(self):
        """Test GET /api/tenant/config/"""
        self.client.force_authenticate(user=self.user)
        
        url = reverse('tenant_config')  # inventory.urls.n8n_api_urls
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data['company'], self.company.id)
        self.assertEqual(data['oauth2_client_id'], self.oauth_app.client_id)
        self.assertTrue(data['is_whatsapp_active'])
        self.assertFalse(data['is_gmail_active'])
        
        # Verificar que secrets no se muestran en GET
        self.assertNotIn('oauth2_client_secret', data)
        self.assertNotIn('twilio_auth_token', data)
    
    def test_put_tenant_config(self):
        """Test PUT /api/tenant/config/"""
        self.client.force_authenticate(user=self.user)
        
        url = reverse('tenant_config')
        update_data = {
            'is_gmail_active': True,
            'gmail_client_id': 'new_gmail_client_id',
            'gmail_client_secret': 'new_gmail_secret',
            'gmail_email': 'test@gmail.com'
        }
        
        response = self.client.put(url, update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar actualización en BD
        self.tenant_config.refresh_from_db()
        self.assertTrue(self.tenant_config.is_gmail_active)
        self.assertEqual(self.tenant_config.gmail_client_id, 'new_gmail_client_id')
        self.assertEqual(self.tenant_config.gmail_email, 'test@gmail.com')
    
    def test_oauth_token_generation(self):
        """Test generación de token OAuth2"""
        # Mock del endpoint OAuth2 (usando Client Credentials)
        from unittest.mock import patch, Mock
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'access_token': 'test_access_token_12345',
            'token_type': 'Bearer',
            'expires_in': 3600,
            'scope': 'read write'
        }
        
        with patch('requests.post', return_value=mock_response):
            from inventory.services.n8n_integration_service import N8nIntegrationService
            
            result = N8nIntegrationService.get_oauth_token(self.company.id)
            
            self.assertTrue(result['success'])
            self.assertEqual(result['access_token'], 'test_access_token_12345')
            self.assertEqual(result['token_type'], 'Bearer')
            self.assertEqual(result['expires_in'], 3600)
    
    def test_oauth_token_failure(self):
        """Test fallo en generación de token OAuth2"""
        from unittest.mock import patch, Mock
        
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = 'invalid_client'
        
        with patch('requests.post', return_value=mock_response):
            from inventory.services.n8n_integration_service import N8nIntegrationService
            
            result = N8nIntegrationService.get_oauth_token(self.company.id)
            
            self.assertFalse(result['success'])
            self.assertIn('Token request failed', result['error'])
    
    def test_get_tenant_config_service(self):
        """Test servicio get_tenant_config"""
        from inventory.services.n8n_integration_service import N8nIntegrationService
        
        config = N8nIntegrationService.get_tenant_config(self.company.id)
        
        self.assertIsNotNone(config)
        self.assertEqual(config['tenant_id'], self.company.id)
        self.assertEqual(config['oauth2_client_id'], self.oauth_app.client_id)
        self.assertTrue(config['is_whatsapp_active'])
        self.assertFalse(config['is_gmail_active'])
        self.assertTrue(config['is_configured'])
    
    def test_get_tenant_config_not_found(self):
        """Test get_tenant_config con tenant inexistente"""
        from inventory.services.n8n_integration_service import N8nIntegrationService
        
        config = N8nIntegrationService.get_tenant_config(99999)
        
        self.assertIsNone(config)
    
    def test_tenant_config_validation(self):
        """Test validaciones del modelo TenantConfig"""
        # Test validación WhatsApp activo sin credenciales
        config = TenantConfig(
            company=self.company,
            is_whatsapp_active=True,
            twilio_account_sid="",  # Vacío
            twilio_auth_token=""
        )
        
        with self.assertRaises(Exception):
            config.full_clean()
    
    def test_oauth_test_endpoints(self):
        """Test endpoints de testing OAuth2"""
        # Test endpoint de test OAuth token
        url = '/api/inventory/oauth-test/test-oauth-token/'
        response = self.client.get(url)
        
        self.assertIn(response.status_code, [200, 400])  # Puede fallar por configuración
        
        # Test endpoint de configuración completa
        url = '/api/inventory/oauth-test/test-full-config/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('total_tenants', data)
        self.assertIn('tenants', data)


class OAuth2IntegrationTests(TestCase):
    """Tests de integración OAuth2 con endpoints reales"""
    
    def setUp(self):
        """Setup para tests de integración"""
        self.client = Client()
        
        # Crear aplicación OAuth2
        self.oauth_app = Application.objects.create(
            name="Integration Test App",
            client_type=Application.CLIENT_CONFIDENTIAL,
            authorization_grant_type=Application.GRANT_CLIENT_CREDENTIALS,
        )
    
    def test_oauth_token_endpoint_client_credentials(self):
        """Test real del endpoint /oauth/token/ con Client Credentials"""
        url = '/oauth/token/'
        
        data = {
            'grant_type': 'client_credentials',
            'client_id': self.oauth_app.client_id,
            'client_secret': self.oauth_app.client_secret,
            'scope': 'read write'
        }
        
        response = self.client.post(
            url,
            data,
            content_type='application/x-www-form-urlencoded'
        )
        
        self.assertEqual(response.status_code, 200)
        
        response_data = response.json()
        self.assertIn('access_token', response_data)
        self.assertIn('token_type', response_data)
        self.assertIn('expires_in', response_data)
        self.assertEqual(response_data['token_type'], 'Bearer')
    
    def test_oauth_token_endpoint_invalid_credentials(self):
        """Test endpoint /oauth/token/ con credenciales inválidas"""
        url = '/oauth/token/'
        
        data = {
            'grant_type': 'client_credentials',
            'client_id': 'invalid_client_id',
            'client_secret': 'invalid_secret',
            'scope': 'read write'
        }
        
        response = self.client.post(
            url,
            data,
            content_type='application/x-www-form-urlencoded'
        )
        
        self.assertEqual(response.status_code, 401)
        
        response_data = response.json()
        self.assertEqual(response_data['error'], 'invalid_client')
    
    def test_oauth_authorize_endpoint_redirect(self):
        """Test endpoint /oauth/authorize/ redirige a login"""
        url = '/oauth/authorize/'
        
        response = self.client.get(url)
        
        # Debe redirigir a login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)


class MultiTenantTests(APITestCase):
    """Tests para multi-tenant scenarios"""
    
    def setUp(self):
        """Setup para tests multi-tenant"""
        # Crear múltiples companies
        self.company1 = Company.objects.create(name="Company 1", subscription_type="basic")
        self.company2 = Company.objects.create(name="Company 2", subscription_type="premium")
        
        # Usuarios para cada company
        self.user1 = User.objects.create_user(
            username="user1@company1.com",
            email="user1@company1.com",
            password="test123",
            company=self.company1
        )
        
        self.user2 = User.objects.create_user(
            username="user2@company2.com",
            email="user2@company2.com",
            password="test123",
            company=self.company2
        )
        
        # Configuraciones diferentes por tenant
        TenantConfig.objects.create(
            company=self.company1,
            is_whatsapp_active=True,
            is_gmail_active=False,
            twilio_account_sid="company1_sid",
            twilio_auth_token="company1_token"
        )
        
        TenantConfig.objects.create(
            company=self.company2,
            is_whatsapp_active=False,
            is_gmail_active=True,
            gmail_client_id="company2_gmail_id",
            gmail_client_secret="company2_gmail_secret"
        )
    
    def test_isolated_tenant_configs(self):
        """Test que cada tenant ve solo su configuración"""
        url = reverse('tenant_config')
        
        # Usuario 1 ve configuración de Company 1
        self.client.force_authenticate(user=self.user1)
        response1 = self.client.get(url)
        self.assertEqual(response1.status_code, 200)
        data1 = response1.json()
        
        # Usuario 2 ve configuración de Company 2
        self.client.force_authenticate(user=self.user2)
        response2 = self.client.get(url)
        self.assertEqual(response2.status_code, 200)
        data2 = response2.json()
        
        # Verificar aislamiento
        self.assertEqual(data1['company'], self.company1.id)
        self.assertEqual(data2['company'], self.company2.id)
        self.assertTrue(data1['is_whatsapp_active'])
        self.assertTrue(data2['is_gmail_active'])
        self.assertFalse(data1['is_gmail_active'])
        self.assertFalse(data2['is_whatsapp_active'])
