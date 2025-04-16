import pytest
import sys
import os
import json
from unittest.mock import patch, MagicMock

# Añadir el directorio raíz al path para importar módulos de la aplicación
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.security.threat_detection import analyze_message_content, calculate_threat_score
from app.security.blacklist import is_blacklisted, add_to_blacklist
from app.security.honeypot import create_honeypot_link, track_honeypot_click
from app.db.models import SecurityIncident, BlacklistEntry, HoneypotRecord


class TestThreatDetection:
    
    def test_analyze_message_content_with_suspicious_text(self):
        """Prueba la detección de texto sospechoso en mensajes."""
        # Simulamos palabras sospechosas
        suspicious_words = ["extorsión", "amenaza", "pago", "urgente", "inmediato"]
        
        with patch('app.security.threat_detection.load_suspicious_words', return_value=suspicious_words):
            # Mensaje normal
            normal_message = "Hola, ¿cómo estás? Me gustaría saber el precio de sus productos."
            normal_result = analyze_message_content(normal_message)
            
            # Mensaje sospechoso
            suspicious_message = "URGENTE: Realiza un pago inmediato o sufrirás consecuencias. Amenaza seria."
            suspicious_result = analyze_message_content(suspicious_message)
            
            assert normal_result['score'] < 0.5, "Un mensaje normal no debería tener un score alto"
            assert suspicious_result['score'] > 0.7, "Un mensaje sospechoso debería tener un score alto"
            assert len(suspicious_result['detected_words']) >= 3, "Debería detectar al menos 3 palabras sospechosas"
    
    def test_calculate_threat_score(self):
        """Prueba el cálculo de puntuación de amenaza basado en múltiples factores."""
        # Caso de bajo riesgo
        low_risk = {
            'message_score': 0.1,
            'is_blacklisted': False,
            'message_frequency': 3,
            'time_pattern_score': 0.2,
            'honeypot_interactions': 0
        }
        
        # Caso de riesgo medio
        medium_risk = {
            'message_score': 0.5,
            'is_blacklisted': False,
            'message_frequency': 8,
            'time_pattern_score': 0.4,
            'honeypot_interactions': 1
        }
        
        # Caso de alto riesgo
        high_risk = {
            'message_score': 0.8,
            'is_blacklisted': True,
            'message_frequency': 15,
            'time_pattern_score': 0.7,
            'honeypot_interactions': 3
        }
        
        low_score = calculate_threat_score(**low_risk)
        medium_score = calculate_threat_score(**medium_risk)
        high_score = calculate_threat_score(**high_risk)
        
        assert low_score < 0.3, "Un caso de bajo riesgo debería tener una puntuación baja"
        assert 0.3 <= medium_score <= 0.7, "Un caso de riesgo medio debería tener una puntuación media"
        assert high_score > 0.7, "Un caso de alto riesgo debería tener una puntuación alta"


class TestBlacklist:
    
    @pytest.fixture
    def mock_db_session(self):
        """Fixture para crear una sesión de BD simulada."""
        mock_session = MagicMock()
        return mock_session
    
    def test_is_blacklisted(self, mock_db_session):
        """Prueba la verificación de números en la lista negra."""
        # Configurar el mock para simular un número en la lista negra
        mock_db_session.query().filter().first.side_effect = [
            BlacklistEntry(phone_number="+123456789", is_active=True),  # Para el primer caso
            None  # Para el segundo caso
        ]
        
        # Caso: Número en la lista negra
        assert is_blacklisted("+123456789", mock_db_session) is True
        
        # Caso: Número no en la lista negra
        assert is_blacklisted("+987654321", mock_db_session) is False
    
    def test_add_to_blacklist(self, mock_db_session):
        """Prueba añadir un número a la lista negra."""
        # Configurar el mock para simular que el número no existe en la lista negra
        mock_db_session.query().filter().first.return_value = None
        
        # Añadir a la lista negra
        result = add_to_blacklist(
            phone_number="+123456789",
            reason="Comportamiento sospechoso",
            source="automatic",
            db=mock_db_session
        )
        
        # Verificaciones
        assert result["success"] is True
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        
        # Ahora simulamos que el número ya existe
        mock_db_session.reset_mock()
        mock_db_session.query().filter().first.return_value = BlacklistEntry(phone_number="+123456789")
        
        result = add_to_blacklist(
            phone_number="+123456789",
            reason="Comportamiento sospechoso 2",
            source="automatic",
            db=mock_db_session
        )
        
        # Verificaciones para actualización
        assert result["success"] is True
        assert "already exists" in result["message"]
        mock_db_session.commit.assert_called_once()


class TestHoneypot:
    
    @pytest.fixture
    def mock_db_session(self):
        """Fixture para crear una sesión de BD simulada."""
        mock_session = MagicMock()
        return mock_session
    
    def test_create_honeypot_link(self, mock_db_session):
        """Prueba la creación de enlaces de honeypot."""
        phone_number = "+123456789"
        
        with patch('app.security.honeypot.uuid.uuid4', return_value="test-uuid-123"):
            link = create_honeypot_link(phone_number, mock_db_session)
            
            assert "test-uuid-123" in link
            mock_db_session.add.assert_called_once()
            mock_db_session.commit.assert_called_once()
            
            # Verificar que se creó el registro en la base de datos
            added_record = mock_db_session.add.call_args[0][0]
            assert isinstance(added_record, HoneypotRecord)
            assert added_record.phone_number == phone_number
            assert added_record.tracking_id == "test-uuid-123"
    
    def test_track_honeypot_click(self, mock_db_session):
        """Prueba el seguimiento de clics en enlaces de honeypot."""
        # Configurar el mock para simular un registro existente
        mock_record = MagicMock(spec=HoneypotRecord)
        mock_record.clicks = 0
        mock_record.ip_addresses = []
        mock_record.user_agents = []
        
        mock_db_session.query().filter().first.return_value = mock_record
        
        # Simular un clic
        request_data = {
            "ip": "192.168.1.1",
            "user_agent": "Mozilla/5.0 (Test Browser)",
            "referer": "https://example.com",
        }
        
        result = track_honeypot_click("test-uuid-123", request_data, mock_db_session)
        
        assert result["success"] is True
        assert mock_record.clicks == 1
        assert "192.168.1.1" in mock_record.ip_addresses
        assert "Mozilla/5.0 (Test Browser)" in mock_record.user_agents
        mock_db_session.commit.assert_called_once()
        
        # Caso: ID de seguimiento inválido
        mock_db_session.reset_mock()
        mock_db_session.query().filter().first.return_value = None
        
        result = track_honeypot_click("invalid-id", request_data, mock_db_session)
        
        assert result["success"] is False
        assert "not found" in result["message"]
        mock_db_session.commit.assert_not_called()


# Si se ejecuta directamente este archivo
if __name__ == "__main__":
    pytest.main(["-v"])