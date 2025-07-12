import pandas as pd
import numpy as np
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os
from typing import Dict, List, Tuple, Any
import difflib
from decimal import Decimal
from datetime import datetime, date
import re
from .models import DataImportSession, ColumnMapping, FieldDefinition, FIELD_DEFINITIONS


class FileAnalysisService:
    """Servicio para analizar archivos Excel/CSV"""
    
    @staticmethod
    def analyze_file(file_path: str, header_row: int = 1) -> Dict[str, Any]:
        """Analiza un archivo y extrae información sobre las columnas"""
        try:
            # Leer el archivo
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path, header=header_row-1, nrows=100)  # Solo leer primeras 100 filas para análisis
            else:
                df = pd.read_excel(file_path, header=header_row-1, nrows=100)
            
            # Obtener información básica
            detected_columns = df.columns.tolist()
            total_rows = len(df)
            
            # Obtener datos de muestra (primeras 5 filas)
            sample_data = []
            for idx, row in df.head(5).iterrows():
                sample_data.append(row.fillna('').to_dict())
            
            # Analizar tipos de datos
            column_info = {}
            for col in detected_columns:
                col_data = df[col].dropna()
                
                # Inferir tipo de dato
                inferred_type = FileAnalysisService._infer_column_type(col_data)
                
                # Obtener estadísticas
                stats = FileAnalysisService._get_column_stats(col_data, inferred_type)
                
                column_info[col] = {
                    'inferred_type': inferred_type,
                    'non_null_count': len(col_data),
                    'null_count': df[col].isnull().sum(),
                    'unique_count': col_data.nunique(),
                    'sample_values': col_data.head(10).tolist(),
                    'stats': stats
                }
            
            return {
                'detected_columns': detected_columns,
                'total_rows': total_rows,
                'sample_data': sample_data,
                'column_info': column_info
            }
            
        except Exception as e:
            raise Exception(f"Error al analizar el archivo: {str(e)}")
    
    @staticmethod
    def _infer_column_type(series: pd.Series) -> str:
        """Infiere el tipo de dato de una columna"""
        # Convertir a string para análisis
        string_series = series.astype(str).str.strip()
        
        # Remover valores vacíos
        clean_series = string_series[string_series != '']
        
        if len(clean_series) == 0:
            return 'text'
        
        # Verificar booleanos
        bool_values = {'true', 'false', 'verdadero', 'falso', 'sí', 'no', 'si', '1', '0', 'yes', 'no'}
        if all(val.lower() in bool_values for val in clean_series.head(20)):
            return 'boolean'
        
        # Verificar números enteros
        try:
            pd.to_numeric(clean_series, errors='raise')
            # Si todos los valores son enteros
            if all(float(val).is_integer() for val in clean_series.head(20) if val != ''):
                return 'number'
            else:
                return 'decimal'
        except:
            pass
        
        # Verificar fechas
        if FileAnalysisService._is_date_column(clean_series):
            return 'date'
        
        # Verificar emails
        if FileAnalysisService._is_email_column(clean_series):
            return 'email'
        
        # Verificar teléfonos
        if FileAnalysisService._is_phone_column(clean_series):
            return 'phone'
        
        # Por defecto, texto
        return 'text'
    
    @staticmethod
    def _is_date_column(series: pd.Series) -> bool:
        """Verifica si una columna contiene fechas"""
        try:
            # Intentar convertir a fecha
            pd.to_datetime(series.head(10), errors='raise')
            return True
        except:
            return False
    
    @staticmethod
    def _is_email_column(series: pd.Series) -> bool:
        """Verifica si una columna contiene emails"""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        sample_values = series.head(10).tolist()
        
        valid_emails = 0
        for value in sample_values:
            if isinstance(value, str) and re.match(email_pattern, value):
                valid_emails += 1
        
        # Si al menos 70% son emails válidos
        return valid_emails >= len(sample_values) * 0.7
    
    @staticmethod
    def _is_phone_column(series: pd.Series) -> bool:
        """Verifica si una columna contiene teléfonos"""
        phone_pattern = r'^[\+]?[\d\s\-\(\)]{7,15}$'
        sample_values = series.head(10).tolist()
        
        valid_phones = 0
        for value in sample_values:
            if isinstance(value, str) and re.match(phone_pattern, value.strip()):
                valid_phones += 1
        
        # Si al menos 70% son teléfonos válidos
        return valid_phones >= len(sample_values) * 0.7
    
    @staticmethod
    def _get_column_stats(series: pd.Series, data_type: str) -> Dict[str, Any]:
        """Obtiene estadísticas de una columna"""
        stats = {}
        
        if data_type in ['number', 'decimal']:
            try:
                numeric_series = pd.to_numeric(series, errors='coerce')
                stats.update({
                    'min': float(numeric_series.min()) if not numeric_series.empty else None,
                    'max': float(numeric_series.max()) if not numeric_series.empty else None,
                    'mean': float(numeric_series.mean()) if not numeric_series.empty else None,
                })
            except:
                pass
        
        if data_type == 'text':
            try:
                lengths = series.astype(str).str.len()
                stats.update({
                    'min_length': int(lengths.min()),
                    'max_length': int(lengths.max()),
                    'avg_length': float(lengths.mean()),
                })
            except:
                pass
        
        return stats


class ColumnMappingService:
    """Servicio para sugerir mapeos de columnas"""
    
    @staticmethod
    def suggest_mappings(detected_columns: List[str], import_type: str) -> Dict[str, str]:
        """Sugiere mapeos automáticos basados en similitud de nombres"""
        # Obtener campos disponibles para el tipo de importación
        if import_type not in FIELD_DEFINITIONS:
            return {}
        
        available_fields = FIELD_DEFINITIONS[import_type]
        suggestions = {}
        
        for col in detected_columns:
            best_match = ColumnMappingService._find_best_match(col, available_fields)
            if best_match:
                suggestions[col] = best_match
        
        return suggestions
    
    @staticmethod
    def _find_best_match(column_name: str, available_fields: List[Dict]) -> str:
        """Encuentra el mejor match para una columna"""
        column_name_clean = column_name.lower().strip()
        
        # Mapeos exactos
        exact_mappings = {
            'sku': 'sku',
            'codigo': 'sku',
            'código': 'sku',
            'producto': 'name',
            'nombre': 'name',
            'descripcion': 'description',
            'descripción': 'description',
            'categoria': 'category',
            'categoría': 'category',
            'proveedor': 'supplier',
            'precio': 'sale_price',
            'costo': 'cost_price',
            'stock': 'min_stock',
            'email': 'email',
            'correo': 'email',
            'telefono': 'phone',
            'teléfono': 'phone',
            'celular': 'mobile',
            'direccion': 'address',
            'dirección': 'address',
            'ruc': 'ruc',
            'empresa': 'business_name',
            'razon_social': 'business_name',
            'razón_social': 'business_name',
            'nombres': 'first_name',
            'apellidos': 'last_name',
            'documento': 'document_number',
            'dni': 'document_number',
        }
        
        # Buscar mapeo exacto
        if column_name_clean in exact_mappings:
            field_name = exact_mappings[column_name_clean]
            # Verificar que el campo existe en los campos disponibles
            for field in available_fields:
                if field['field_name'] == field_name:
                    return field_name
        
        # Buscar por similitud
        best_similarity = 0
        best_field = None
        
        for field in available_fields:
            # Comparar con nombre del campo
            similarity1 = difflib.SequenceMatcher(None, column_name_clean, field['field_name']).ratio()
            
            # Comparar con nombre de display
            display_name_clean = field['display_name'].lower()
            similarity2 = difflib.SequenceMatcher(None, column_name_clean, display_name_clean).ratio()
            
            # Tomar la mejor similitud
            max_similarity = max(similarity1, similarity2)
            
            # Si la similitud es mayor al umbral y mejor que la anterior
            if max_similarity > 0.6 and max_similarity > best_similarity:
                best_similarity = max_similarity
                best_field = field['field_name']
        
        return best_field


class DataImportService:
    """Servicio para procesar la importación de datos"""
    
    @staticmethod
    def process_import(session: DataImportSession, start_row: int = 2, end_row: int = None) -> Dict[str, Any]:
        """Procesa la importación de datos"""
        try:
            # Leer el archivo completo
            if session.file_path.endswith('.csv'):
                df = pd.read_csv(session.file_path, header=session.header_row-1)
            else:
                df = pd.read_excel(session.file_path, header=session.header_row-1)
            
            # Filtrar filas si se especifica
            if end_row:
                df = df.iloc[start_row-2:end_row-1]  # -2 porque ya tiene header
            else:
                df = df.iloc[start_row-2:]  # -2 porque ya tiene header
            
            # Obtener mapeos de columnas
            mappings = {cm.source_column: cm for cm in session.column_mappings.all()}
            
            # Procesar cada fila
            results = {
                'total_rows': len(df),
                'processed_rows': 0,
                'successful_rows': 0,
                'failed_rows': 0,
                'errors': []
            }
            
            for idx, row in df.iterrows():
                try:
                    # Convertir fila a datos mapeados
                    mapped_data = DataImportService._map_row_data(row, mappings, session.import_type)
                    
                    # Crear el objeto
                    success = DataImportService._create_object(mapped_data, session)
                    
                    if success:
                        results['successful_rows'] += 1
                    else:
                        results['failed_rows'] += 1
                        results['errors'].append({
                            'row': idx + start_row,
                            'error': 'Error al crear el objeto'
                        })
                
                except Exception as e:
                    results['failed_rows'] += 1
                    results['errors'].append({
                        'row': idx + start_row,
                        'error': str(e)
                    })
                
                results['processed_rows'] += 1
            
            # Actualizar sesión
            session.processed_rows = results['processed_rows']
            session.successful_rows = results['successful_rows']
            session.failed_rows = results['failed_rows']
            session.error_log = results['errors']
            session.status = 'completed' if results['failed_rows'] == 0 else 'completed'
            session.completed_at = datetime.now()
            session.save()
            
            return results
            
        except Exception as e:
            session.status = 'failed'
            session.error_log = [{'error': str(e)}]
            session.save()
            raise Exception(f"Error al procesar importación: {str(e)}")
    
    @staticmethod
    def _map_row_data(row: pd.Series, mappings: Dict[str, ColumnMapping], import_type: str) -> Dict[str, Any]:
        """Mapea los datos de una fila según los mapeos configurados"""
        mapped_data = {}
        
        for source_col, mapping in mappings.items():
            if source_col in row.index:
                raw_value = row[source_col]
                
                # Convertir valor según el tipo de campo
                converted_value = DataImportService._convert_value(
                    raw_value, 
                    mapping.field_type, 
                    mapping.default_value
                )
                
                mapped_data[mapping.target_field] = converted_value
        
        return mapped_data
    
    @staticmethod
    def _convert_value(raw_value: Any, field_type: str, default_value: str = '') -> Any:
        """Convierte un valor al tipo apropiado"""
        # Si el valor es nulo o vacío
        if pd.isna(raw_value) or str(raw_value).strip() == '':
            if default_value:
                raw_value = default_value
            else:
                return None if field_type not in ['text', 'boolean'] else ''
        
        try:
            if field_type == 'text':
                return str(raw_value).strip()
            
            elif field_type == 'number':
                return int(float(raw_value))
            
            elif field_type == 'decimal':
                return Decimal(str(raw_value))
            
            elif field_type == 'boolean':
                if isinstance(raw_value, bool):
                    return raw_value
                value_str = str(raw_value).lower().strip()
                return value_str in ['true', 'verdadero', 'sí', 'si', 'yes', '1']
            
            elif field_type == 'date':
                if isinstance(raw_value, (date, datetime)):
                    return raw_value.date() if isinstance(raw_value, datetime) else raw_value
                return pd.to_datetime(raw_value).date()
            
            elif field_type == 'datetime':
                if isinstance(raw_value, datetime):
                    return raw_value
                return pd.to_datetime(raw_value)
            
            elif field_type in ['email', 'phone']:
                return str(raw_value).strip()
            
            else:
                return str(raw_value).strip()
                
        except Exception:
            # Si no se puede convertir, devolver el valor como string
            return str(raw_value).strip() if raw_value is not None else ''
    
    @staticmethod
    def _create_object(mapped_data: Dict[str, Any], session: DataImportSession) -> bool:
        """Crea un objeto en la base de datos según el tipo de importación"""
        try:
            from inventory.models import Product, Supplier, Category, Customer, Lead, Location, InventoryItem, Transaction
            from datalens_backend.utils import get_default_company
            
            if session.import_type == 'products':
                # Validar campos requeridos
                if 'sku' not in mapped_data or 'name' not in mapped_data:
                    return False
                
                # Manejar relaciones
                if 'category' in mapped_data and mapped_data['category']:
                    try:
                        category = Category.objects.get(name=mapped_data['category'])
                        mapped_data['category'] = category
                    except Category.DoesNotExist:
                        mapped_data.pop('category', None)
                
                if 'supplier' in mapped_data and mapped_data['supplier']:
                    try:
                        supplier = Supplier.objects.get(name=mapped_data['supplier'])
                        mapped_data['supplier'] = supplier
                    except Supplier.DoesNotExist:
                        mapped_data.pop('supplier', None)
                
                # Agregar company
                mapped_data['company'] = session.company
                
                # Sincronizar price con sale_price si no se proporciona
                if 'sale_price' in mapped_data and 'price' not in mapped_data:
                    mapped_data['price'] = mapped_data['sale_price']
                
                # Crear o actualizar producto
                if session.skip_duplicates:
                    product, created = Product.objects.get_or_create(
                        sku=mapped_data['sku'],
                        defaults=mapped_data
                    )
                    if not created and session.update_existing:
                        for key, value in mapped_data.items():
                            setattr(product, key, value)
                        product.save()
                else:
                    Product.objects.create(**mapped_data)
                
                return True
            
            elif session.import_type == 'suppliers':
                if 'name' not in mapped_data:
                    return False
                
                # Validar campos únicos
                unique_fields = {}
                if 'tax_id' in mapped_data and mapped_data['tax_id']:
                    unique_fields['tax_id'] = mapped_data['tax_id']
                
                if session.skip_duplicates and unique_fields:
                    supplier, created = Supplier.objects.get_or_create(
                        **unique_fields,
                        defaults=mapped_data
                    )
                    if not created and session.update_existing:
                        for key, value in mapped_data.items():
                            setattr(supplier, key, value)
                        supplier.save()
                else:
                    Supplier.objects.create(**mapped_data)
                
                return True
            
            elif session.import_type == 'categories':
                if 'name' not in mapped_data:
                    return False
                
                if session.skip_duplicates:
                    category, created = Category.objects.get_or_create(
                        name=mapped_data['name'],
                        defaults=mapped_data
                    )
                    if not created and session.update_existing:
                        for key, value in mapped_data.items():
                            setattr(category, key, value)
                        category.save()
                else:
                    Category.objects.create(**mapped_data)
                
                return True
            
            elif session.import_type == 'customers':
                if 'name' not in mapped_data:
                    return False
                
                # Validar campos únicos
                unique_fields = {}
                if 'tax_id' in mapped_data and mapped_data['tax_id']:
                    unique_fields['tax_id'] = mapped_data['tax_id']
                elif 'email' in mapped_data and mapped_data['email']:
                    unique_fields['email'] = mapped_data['email']
                
                if session.skip_duplicates and unique_fields:
                    customer, created = Customer.objects.get_or_create(
                        **unique_fields,
                        defaults=mapped_data
                    )
                    if not created and session.update_existing:
                        for key, value in mapped_data.items():
                            setattr(customer, key, value)
                        customer.save()
                else:
                    Customer.objects.create(**mapped_data)
                
                return True
            
            elif session.import_type == 'leads':
                if 'name' not in mapped_data or 'email' not in mapped_data:
                    return False
                
                # Asignar usuario responsable por defecto
                if 'assigned_to' not in mapped_data:
                    mapped_data['assigned_to'] = session.user
                
                if session.skip_duplicates:
                    lead, created = Lead.objects.get_or_create(
                        email=mapped_data['email'],
                        defaults=mapped_data
                    )
                    if not created and session.update_existing:
                        for key, value in mapped_data.items():
                            setattr(lead, key, value)
                        lead.save()
                else:
                    Lead.objects.create(**mapped_data)
                
                return True
            
            elif session.import_type == 'locations':
                if 'name' not in mapped_data or 'code' not in mapped_data:
                    return False
                
                if session.skip_duplicates:
                    location, created = Location.objects.get_or_create(
                        code=mapped_data['code'],
                        defaults=mapped_data
                    )
                    if not created and session.update_existing:
                        for key, value in mapped_data.items():
                            setattr(location, key, value)
                        location.save()
                else:
                    Location.objects.create(**mapped_data)
                
                return True
            
            elif session.import_type == 'inventory_items':
                # Validar campos requeridos
                if 'product' not in mapped_data or 'location' not in mapped_data or 'quantity' not in mapped_data:
                    return False
                
                # Resolver relaciones
                try:
                    if isinstance(mapped_data['product'], str):
                        product = Product.objects.get(sku=mapped_data['product'])
                        mapped_data['product'] = product
                    
                    if isinstance(mapped_data['location'], str):
                        location = Location.objects.get(code=mapped_data['location'])
                        mapped_data['location'] = location
                except (Product.DoesNotExist, Location.DoesNotExist):
                    return False
                
                # Verificar si ya existe el item
                if session.skip_duplicates:
                    item, created = InventoryItem.objects.get_or_create(
                        product=mapped_data['product'],
                        location=mapped_data['location'],
                        batch_number=mapped_data.get('batch_number', ''),
                        defaults=mapped_data
                    )
                    if not created and session.update_existing:
                        for key, value in mapped_data.items():
                            setattr(item, key, value)
                        item.save()
                else:
                    InventoryItem.objects.create(**mapped_data)
                
                return True
            
            elif session.import_type == 'transactions':
                # Validar campos requeridos
                if 'product' not in mapped_data or 'transaction_type' not in mapped_data or 'quantity' not in mapped_data:
                    return False
                
                # Resolver relaciones
                try:
                    if isinstance(mapped_data['product'], str):
                        product = Product.objects.get(sku=mapped_data['product'])
                        mapped_data['product'] = product
                    
                    if 'location' in mapped_data and isinstance(mapped_data['location'], str):
                        location = Location.objects.get(code=mapped_data['location'])
                        mapped_data['location'] = location
                except (Product.DoesNotExist, Location.DoesNotExist):
                    return False
                
                # Agregar usuario creador
                mapped_data['created_by'] = session.user
                
                # Establecer fecha por defecto si no se proporciona
                if 'transaction_date' not in mapped_data:
                    mapped_data['transaction_date'] = datetime.now()
                
                Transaction.objects.create(**mapped_data)
                return True
            
            return False
            
        except Exception as e:
            print(f"Error creating object: {e}")
            return False