import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.main import app
from app.db.models import Product, Order, Customer, OrderItem, SecurityIncident
from app.db.models import OrderStatus, PaymentMethod

# Cliente de prueba
client = TestClient(app)

# Mock para session de base de datos
@pytest.fixture
def mock_db_session():
    mock_session = MagicMock(spec=Session)
    return mock_session

# Test para el endpoint de estadísticas del dashboard
@patch("app.api.client.get_db")
def test_get_dashboard_stats(mock_get_db, mock_db_session):
    # Configurar mock
    mock_get_db.return_value = mock_db_session
    
    # Configurar resultados de consultas
    mock_db_session.query.return_value.count.return_value = 10  # Simular 10 clientes
    mock_db_session.query.return_value.filter.return_value.all.return_value = [
        MagicMock(total_amount=100), MagicMock(total_amount=200)
    ]  # Simular órdenes completadas
    
    # Configurar consulta para top productos
    mock_product_query = MagicMock()
    mock_product_query.all.return_value = [
        MagicMock(id=1, name="Producto 1", price=50.0, total_sold=5),
        MagicMock(id=2, name="Producto 2", price=75.0, total_sold=3)
    ]
    mock_db_session.query.return_value.join.return_value.join.return_value.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value = mock_product_query
    
    # Configurar consulta para incidentes recientes
    mock_incidents = [
        MagicMock(
            id=1, 
            type="phishing", 
            severity="high", 
            phone_number="+123456789", 
            is_resolved=False,
            timestamp=datetime.now()
        )
    ]
    mock_db_session.query.return_value.order_by.return_value.limit.return_value.all.return_value = mock_incidents
    
    # Hacer solicitud al endpoint
    response = client.get("/api/client/dashboard/stats")
    
    # Verificar respuesta
    assert response.status_code == 200
    data = response.json()
    assert "total_customers" in data
    assert "total_sales" in data
    assert "top_products" in data
    assert "recent_incidents" in data

# Test para el endpoint de listado de productos
@patch("app.api.client.get_db")
def test_get_products(mock_get_db, mock_db_session):
    # Configurar mock
    mock_get_db.return_value = mock_db_session
    
    # Configurar resultados de consultas
    mock_products = [
        MagicMock(
            id=1, 
            code="PROD1",
            name="Producto 1", 
            description="Descripción 1",
            price=100.0,
            stock=10,
            image_url="http://example.com/prod1.jpg",
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        MagicMock(
            id=2, 
            code="PROD2",
            name="Producto 2", 
            description="Descripción 2",
            price=200.0,
            stock=5,
            image_url="http://example.com/prod2.jpg",
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    ]
    mock_db_session.query.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = mock_products
    
    # Hacer solicitud al endpoint
    response = client.get("/api/client/products?active_only=true&skip=0&limit=10")
    
    # Verificar respuesta
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["id"] == 1
    assert data[0]["name"] == "Producto 1"
    assert data[1]["id"] == 2
    assert data[1]["name"] == "Producto 2"

# Test para el endpoint de listado de órdenes
@patch("app.api.client.get_db")
def test_get_orders(mock_get_db, mock_db_session):
    # Configurar mock
    mock_get_db.return_value = mock_db_session
    
    # Configurar resultados de consultas
    mock_orders = [
        MagicMock(
            id=1,
            customer_id=1,
            total_amount=300.0,
            status="completed",
            payment_method="credit_card",
            payment_status="completed",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    ]
    mock_db_session.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_orders
    
    # Mock para cliente
    mock_customer = MagicMock(id=1, name="Cliente 1", phone_number="+123456789")
    mock_db_session.query.return_value.filter.return_value.first.return_value = mock_customer
    
    # Mock para items de orden
    mock_items = [
        MagicMock(id=1, order_id=1, product_id=1, quantity=2, unit_price=100.0, subtotal=200.0),
        MagicMock(id=2, order_id=1, product_id=2, quantity=1, unit_price=100.0, subtotal=100.0)
    ]
    mock_db_session.query.return_value.filter.return_value.all.side_effect = [mock_items]
    
    # Mock para productos
    mock_product = MagicMock(id=1, name="Producto 1")
    mock_db_session.query.return_value.filter.return_value.first.side_effect = [mock_customer, mock_product, mock_product]
    
    # Hacer solicitud al endpoint
    response = client.get("/api/client/orders?status=completed&skip=0&limit=10")
    
    # Verificar respuesta
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == 1
    assert data[0]["customer"]["name"] == "Cliente 1"
    assert data[0]["total_amount"] == 300.0
    assert data[0]["status"] == "completed"

# Test para el endpoint de actualización de estado de una orden
@patch("app.api.client.get_db")
def test_update_order_status(mock_get_db, mock_db_session):
    # Configurar mock
    mock_get_db.return_value = mock_db_session
    
    # Mock para la orden
    mock_order = MagicMock(
        id=1,
        customer_id=1,
        status="pending",
        payment_status="pending"
    )
    mock_db_session.query.return_value.filter.return_value.first.return_value = mock_order
    
    # Mock para el cliente
    mock_customer = MagicMock(id=1, name="Cliente 1", phone_number="+123456789")
    mock_db_session.query.return_value.filter.return_value.first.side_effect = [mock_order, mock_customer]
    
    # Patch para queue_notification
    with patch("app.api.client.queue_notification") as mock_queue:
        # Hacer solicitud al endpoint
        response = client.put("/api/client/orders/1/status?status=processing")
        
        # Verificar respuesta
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["order_id"] == 1
        assert data["old_status"] == "pending"
        assert data["new_status"] == "processing"
        
        # Verificar llamada a commit
        mock_db_session.commit.assert_called_once()
        
        # Verificar llamada a queue_notification
        mock_queue.assert_called_once()

# Test para el endpoint de reporte de ventas
@patch("app.api.client.get_db")
def test_get_sales_report(mock_get_db, mock_db_session):
    # Configurar mock
    mock_get_db.return_value = mock_db_session
    
    # Configurar resultados de consultas
    mock_orders = [
        MagicMock(
            created_at=datetime.now() - timedelta(days=1),
            total_amount=100.0,
            payment_method="credit_card"
        ),
        MagicMock(
            created_at=datetime.now(),
            total_amount=200.0,
            payment_method="transfer"
        )
    ]
    mock_db_session.query.return_value.filter.return_value.all.return_value = mock_orders
    
    # Hacer solicitud al endpoint
    response = client.get("/api/client/sales/report?period=daily")
    
    # Verificar respuesta
    assert response.status_code == 200
    data = response.json()
    assert "total_sales" in data
    assert "total_orders" in data
    assert "data" in data
    assert len(data["data"]) > 0