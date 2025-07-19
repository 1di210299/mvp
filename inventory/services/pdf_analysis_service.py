"""
PDF Analysis Service - Servicio para análisis de documentos PDF
Extrae datos de facturas, confirmaciones de envío y otros documentos PDF
"""
import json
import logging
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import os

# PyPDF2 para lectura de PDFs
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# OpenAI para análisis inteligente de contenido
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone

logger = logging.getLogger(__name__)

@dataclass
class PDFAnalysisResult:
    """Resultado del análisis de PDF"""
    document_type: str  # 'invoice', 'shipping_confirmation', 'purchase_order', 'other'
    confidence: float
    extracted_data: Dict[str, Any]
    text_content: str
    metadata: Dict[str, Any]
    status_updates: List[Dict[str, Any]]  # Actualizaciones de estado sugeridas

@dataclass
class InvoiceData:
    """Datos extraídos de una factura"""
    invoice_number: Optional[str] = None
    invoice_date: Optional[datetime] = None
    vendor_name: Optional[str] = None
    vendor_email: Optional[str] = None
    total_amount: Optional[float] = None
    currency: Optional[str] = None
    line_items: List[Dict[str, Any]] = None
    payment_terms: Optional[str] = None
    due_date: Optional[datetime] = None

@dataclass
class ShippingConfirmationData:
    """Datos extraídos de confirmación de envío"""
    tracking_number: Optional[str] = None
    shipping_date: Optional[datetime] = None
    carrier: Optional[str] = None
    delivery_date: Optional[datetime] = None
    items_shipped: List[Dict[str, Any]] = None
    shipping_address: Optional[str] = None
    status: Optional[str] = None


class PDFAnalysisService:
    """
    Servicio principal para análisis de archivos PDF
    """
    
    def __init__(self):
        """Inicializar el servicio"""
        self.openai_client = None
        
        # Inicializar OpenAI si está disponible
        if OPENAI_AVAILABLE:
            api_key = getattr(settings, 'OPENAI_API_KEY', None)
            if api_key:
                self.openai_client = OpenAI(api_key=api_key)
        
        # Patrones de expresiones regulares para extracción de datos
        self.patterns = {
            'invoice_number': [
                r'invoice\s*#?\s*:?\s*([A-Z0-9\-]+)',
                r'factura\s*#?\s*:?\s*([A-Z0-9\-]+)',
                r'inv\s*#?\s*:?\s*([A-Z0-9\-]+)',
            ],
            'tracking_number': [
                r'tracking\s*#?\s*:?\s*([A-Z0-9\-]+)',
                r'rastreo\s*#?\s*:?\s*([A-Z0-9\-]+)',
                r'seguimiento\s*#?\s*:?\s*([A-Z0-9\-]+)',
            ],
            'email': [
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            ],
            'amount': [
                r'\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
                r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*USD',
                r'total\s*:?\s*\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            ],
            'date': [
                r'(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
                r'(\d{2,4}[\/\-]\d{1,2}[\/\-]\d{1,2})',
                r'([A-Za-z]{3,9}\s+\d{1,2},?\s+\d{2,4})',
            ]
        }
    
    def analyze_pdf(self, pdf_path: str, context: Dict[str, Any] = None) -> PDFAnalysisResult:
        """
        Analizar un archivo PDF y extraer información relevante
        
        Args:
            pdf_path: Ruta al archivo PDF
            context: Contexto adicional (purchase order, supplier info, etc.)
        
        Returns:
            PDFAnalysisResult con toda la información extraída
        """
        if not PDF_AVAILABLE:
            raise Exception("PyPDF2 no está disponible. Instale con: pip install PyPDF2")
        
        try:
            # Extraer texto del PDF
            text_content = self._extract_text_from_pdf(pdf_path)
            
            if not text_content.strip():
                return PDFAnalysisResult(
                    document_type='unknown',
                    confidence=0.0,
                    extracted_data={},
                    text_content='',
                    metadata={'error': 'No se pudo extraer texto del PDF'},
                    status_updates=[]
                )
            
            # Detectar tipo de documento
            doc_type, confidence = self._detect_document_type(text_content)
            
            # Extraer datos según el tipo de documento
            extracted_data = {}
            status_updates = []
            
            if doc_type == 'invoice':
                extracted_data = self._extract_invoice_data(text_content)
                status_updates = self._generate_invoice_status_updates(extracted_data, context)
            elif doc_type == 'shipping_confirmation':
                extracted_data = self._extract_shipping_data(text_content)
                status_updates = self._generate_shipping_status_updates(extracted_data, context)
            elif doc_type == 'purchase_order':
                extracted_data = self._extract_purchase_order_data(text_content)
                status_updates = self._generate_po_status_updates(extracted_data, context)
            
            # Análisis adicional con IA si está disponible
            if self.openai_client and confidence < 0.8:
                ai_analysis = self._analyze_with_ai(text_content, doc_type, context)
                extracted_data.update(ai_analysis.get('data', {}))
                status_updates.extend(ai_analysis.get('status_updates', []))
                confidence = max(confidence, ai_analysis.get('confidence', confidence))
            
            metadata = {
                'file_path': pdf_path,
                'analyzed_at': timezone.now().isoformat(),
                'text_length': len(text_content),
                'analysis_method': 'regex + ai' if self.openai_client else 'regex_only'
            }
            
            return PDFAnalysisResult(
                document_type=doc_type,
                confidence=confidence,
                extracted_data=extracted_data,
                text_content=text_content,
                metadata=metadata,
                status_updates=status_updates
            )
            
        except Exception as e:
            logger.error(f"Error analizando PDF {pdf_path}: {e}")
            return PDFAnalysisResult(
                document_type='error',
                confidence=0.0,
                extracted_data={},
                text_content='',
                metadata={'error': str(e)},
                status_updates=[]
            )
    
    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extraer texto completo del PDF"""
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text() + "\n"
                    
        except Exception as e:
            logger.error(f"Error extrayendo texto de PDF: {e}")
            raise
            
        return text
    
    def _detect_document_type(self, text: str) -> Tuple[str, float]:
        """Detectar el tipo de documento basado en contenido"""
        text_lower = text.lower()
        
        # Palabras clave para cada tipo de documento
        keywords = {
            'invoice': [
                'invoice', 'factura', 'bill', 'payment due', 'total amount',
                'subtotal', 'tax', 'due date', 'billing address'
            ],
            'shipping_confirmation': [
                'shipping', 'shipped', 'tracking', 'delivery', 'carrier',
                'enviado', 'rastreo', 'entrega', 'transportista'
            ],
            'purchase_order': [
                'purchase order', 'po number', 'orden de compra',
                'qty', 'quantity', 'unit price', 'item description'
            ]
        }
        
        scores = {}
        for doc_type, words in keywords.items():
            score = sum(1 for word in words if word in text_lower)
            scores[doc_type] = score / len(words)  # Normalizar por número de palabras
        
        # Tipo con mayor score
        best_type = max(scores, key=scores.get)
        confidence = scores[best_type]
        
        # Si confidence es muy baja, es documento desconocido
        if confidence < 0.1:
            return 'other', confidence
        
        return best_type, confidence
    
    def _extract_invoice_data(self, text: str) -> Dict[str, Any]:
        """Extraer datos específicos de facturas"""
        data = {}
        
        # Buscar número de factura
        for pattern in self.patterns['invoice_number']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data['invoice_number'] = match.group(1)
                break
        
        # Buscar email del proveedor
        for pattern in self.patterns['email']:
            match = re.search(pattern, text)
            if match:
                data['vendor_email'] = match.group(0)
                break
        
        # Buscar monto total
        for pattern in self.patterns['amount']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '')
                try:
                    data['total_amount'] = float(amount_str)
                except ValueError:
                    pass
                break
        
        # Buscar fechas
        dates = []
        for pattern in self.patterns['date']:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                dates.append(match.group(0))
        
        if dates:
            data['dates_found'] = dates[:3]  # Primeras 3 fechas encontradas
        
        return data
    
    def _extract_shipping_data(self, text: str) -> Dict[str, Any]:
        """Extraer datos específicos de confirmaciones de envío"""
        data = {}
        
        # Buscar número de tracking
        for pattern in self.patterns['tracking_number']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data['tracking_number'] = match.group(1)
                break
        
        # Buscar transportista
        carriers = ['ups', 'fedex', 'dhl', 'usps', 'tnt', 'aramex']
        for carrier in carriers:
            if carrier in text.lower():
                data['carrier'] = carrier.upper()
                break
        
        # Buscar fechas
        dates = []
        for pattern in self.patterns['date']:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                dates.append(match.group(0))
        
        if dates:
            data['shipping_date'] = dates[0] if dates else None
            data['delivery_date'] = dates[1] if len(dates) > 1 else None
        
        return data
    
    def _extract_purchase_order_data(self, text: str) -> Dict[str, Any]:
        """Extraer datos de órdenes de compra"""
        data = {}
        
        # Buscar número de PO
        po_patterns = [
            r'po\s*#?\s*:?\s*([A-Z0-9\-]+)',
            r'purchase\s*order\s*#?\s*:?\s*([A-Z0-9\-]+)',
            r'orden\s*#?\s*:?\s*([A-Z0-9\-]+)',
        ]
        
        for pattern in po_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data['po_number'] = match.group(1)
                break
        
        # Buscar fechas
        dates = []
        for pattern in self.patterns['date']:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                dates.append(match.group(0))
        
        if dates:
            data['order_date'] = dates[0] if dates else None
        
        return data
    
    def _generate_invoice_status_updates(self, data: Dict[str, Any], context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Generar actualizaciones de estado sugeridas para facturas"""
        updates = []
        
        if data.get('invoice_number') and context and context.get('purchase_order_id'):
            updates.append({
                'action': 'update_purchase_order_status',
                'purchase_order_id': context['purchase_order_id'],
                'new_status': 'invoiced',
                'data': {
                    'invoice_number': data['invoice_number'],
                    'invoice_amount': data.get('total_amount'),
                    'vendor_email': data.get('vendor_email')
                }
            })
        
        return updates
    
    def _generate_shipping_status_updates(self, data: Dict[str, Any], context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Generar actualizaciones de estado sugeridas para confirmaciones de envío"""
        updates = []
        
        if data.get('tracking_number') and context and context.get('purchase_order_id'):
            updates.append({
                'action': 'update_purchase_order_status',
                'purchase_order_id': context['purchase_order_id'],
                'new_status': 'shipped',
                'data': {
                    'tracking_number': data['tracking_number'],
                    'carrier': data.get('carrier'),
                    'shipping_date': data.get('shipping_date')
                }
            })
        
        return updates
    
    def _generate_po_status_updates(self, data: Dict[str, Any], context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Generar actualizaciones de estado sugeridas para órdenes de compra"""
        updates = []
        
        if data.get('po_number') and context and context.get('purchase_order_id'):
            updates.append({
                'action': 'confirm_purchase_order',
                'purchase_order_id': context['purchase_order_id'],
                'new_status': 'confirmed',
                'data': {
                    'confirmed_po_number': data['po_number'],
                    'order_date': data.get('order_date')
                }
            })
        
        return updates
    
    def _analyze_with_ai(self, text: str, doc_type: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Análisis adicional con OpenAI para mejorar extracción de datos"""
        try:
            prompt = f"""
            Analiza el siguiente documento PDF de tipo "{doc_type}" y extrae información estructurada:

            TEXTO DEL DOCUMENTO:
            {text[:4000]}  # Limitar a 4000 caracteres para no exceder límites

            CONTEXTO ADICIONAL:
            {json.dumps(context or {}, default=str)}

            Extrae:
            1. Datos específicos según el tipo de documento
            2. Fechas importantes
            3. Números de referencia (facturas, tracking, etc.)
            4. Información de contacto
            5. Montos o cantidades
            6. Estado o actualizaciones sugeridas

            Responde en formato JSON con:
            {{
                "data": {{
                    // datos extraídos específicos
                }},
                "confidence": 0.8,  // nivel de confianza 0-1
                "status_updates": [
                    // actualizaciones de estado sugeridas
                ]
            }}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Eres un experto en análisis de documentos empresariales. Extrae información de manera precisa y estructurada."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            
            result = response.choices[0].message.content
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                # Si no es JSON válido, extraer información básica
                return {
                    "data": {"ai_analysis": result},
                    "confidence": 0.5,
                    "status_updates": []
                }
                
        except Exception as e:
            logger.error(f"Error en análisis con IA: {e}")
            return {
                "data": {},
                "confidence": 0.0,
                "status_updates": []
            }
    
    def analyze_email_attachment(self, email_data: Dict[str, Any], attachment_path: str) -> Optional[PDFAnalysisResult]:
        """
        Analizar adjunto PDF de un email
        
        Args:
            email_data: Datos del email (remitente, asunto, etc.)
            attachment_path: Ruta al archivo PDF adjunto
        
        Returns:
            PDFAnalysisResult o None si no es PDF o error
        """
        if not attachment_path.lower().endswith('.pdf'):
            return None
        
        context = {
            'email_sender': email_data.get('sender'),
            'email_subject': email_data.get('subject'),
            'email_date': email_data.get('date'),
            'email_tracking_id': email_data.get('tracking_id')
        }
        
        return self.analyze_pdf(attachment_path, context)


# ==============================================
# FUNCIÓN DE UTILIDAD GLOBAL
# ==============================================

def get_pdf_analysis_service() -> PDFAnalysisService:
    """Obtener instancia del servicio de análisis PDF"""
    return PDFAnalysisService()

def analyze_pdf_document(pdf_path: str, context: Dict[str, Any] = None) -> PDFAnalysisResult:
    """Función de utilidad para analizar un documento PDF"""
    service = get_pdf_analysis_service()
    return service.analyze_pdf(pdf_path, context)
