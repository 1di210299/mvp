import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from django.conf import settings
from django.db.models import Count  # FIX: Importar Count correctamente
from django.db import models
import os
import io
import base64
from typing import Dict, List, Optional, Tuple

from ..models import DemandForecast, ForecastModel
from inventory.models import Product, Location
import logging

logger = logging.getLogger(__name__)

class ChartService:
    """
    Servicio para generar gráficos de pronósticos y análisis de demanda
    """
    
    def __init__(self):
        # Configurar estilo de matplotlib
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
        # Configurar matplotlib para no usar GUI
        plt.switch_backend('Agg')
        
    def generate_demand_forecast_chart(self, 
                                     company_id: int,
                                     product_ids: Optional[List[int]] = None,
                                     location_ids: Optional[List[int]] = None,
                                     days_ahead: int = 30,
                                     chart_type: str = 'line') -> Dict:
        """
        Genera gráfico de proyecciones de demanda
        
        Args:
            company_id: ID de la empresa
            product_ids: Lista de IDs de productos (opcional)
            location_ids: Lista de IDs de ubicaciones (opcional)
            days_ahead: Días a proyectar
            chart_type: Tipo de gráfico ('line', 'bar', 'area')
            
        Returns:
            Dict con datos del gráfico y imagen base64
        """
        try:
            # Obtener datos de pronósticos
            data = self._get_forecast_data(company_id, product_ids, location_ids, days_ahead)
            
            if data.empty:
                return {
                    'error': 'No hay datos de pronósticos disponibles',
                    'data': [],
                    'chart_image': None
                }
            
            # Generar gráfico según el tipo
            if chart_type == 'line':
                chart_image = self._create_line_chart(data)
            elif chart_type == 'bar':
                chart_image = self._create_bar_chart(data)
            elif chart_type == 'area':
                chart_image = self._create_area_chart(data)
            else:
                chart_image = self._create_line_chart(data)
            
            # Preparar datos para respuesta
            chart_data = self._prepare_chart_data(data)
            
            return {
                'success': True,
                'data': chart_data,
                'chart_image': chart_image,
                'stats': self._calculate_stats(data),
                'total_points': len(data)
            }
            
        except Exception as e:
            logger.error(f"Error generando gráfico de demanda: {str(e)}")
            return {
                'error': f'Error generando gráfico: {str(e)}',
                'data': [],
                'chart_image': None
            }
    
    def _get_forecast_data(self, company_id: int, product_ids: Optional[List[int]], 
                          location_ids: Optional[List[int]], days_ahead: int) -> pd.DataFrame:
        """
        Obtiene datos de pronósticos de la base de datos
        """
        # Filtros base
        filters = {
            'model__company_id': company_id,
            'forecast_date__gte': datetime.now().date(),
            'forecast_date__lte': datetime.now().date() + timedelta(days=days_ahead)
        }
        
        # Filtros opcionales
        if product_ids:
            filters['product_id__in'] = product_ids
        if location_ids:
            filters['location_id__in'] = location_ids
        
        # Consulta optimizada
        queryset = DemandForecast.objects.filter(**filters).select_related(
            'product', 'location', 'model'
        ).values(
            'forecast_date',
            'predicted_demand',
            'lower_bound', 
            'upper_bound',
            'product__name',
            'location__name',
            'model__model_type',
            'model__name'
        ).order_by('forecast_date', 'product__name')
        
        # Convertir a DataFrame
        if not queryset.exists():
            return pd.DataFrame()
        
        df = pd.DataFrame(list(queryset))
        df['forecast_date'] = pd.to_datetime(df['forecast_date'])
        
        return df
    
    def _create_line_chart(self, data: pd.DataFrame) -> str:
        """
        Crea gráfico de líneas para proyecciones de demanda
        """
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Agrupar datos por producto y ubicación para múltiples líneas
        grouped = data.groupby(['product__name', 'location__name'])
        
        colors = plt.cm.Set3(np.linspace(0, 1, len(grouped)))
        
        for i, ((product, location), group) in enumerate(grouped):
            if len(group) > 1:  # Solo mostrar si hay múltiples puntos
                label = f"{product} - {location}"
                ax.plot(group['forecast_date'], group['predicted_demand'], 
                       marker='o', linewidth=2, label=label, color=colors[i], alpha=0.8)
                
                # Agregar banda de confianza si hay datos
                if 'lower_bound' in group.columns and 'upper_bound' in group.columns:
                    ax.fill_between(group['forecast_date'], 
                                  group['lower_bound'], 
                                  group['upper_bound'], 
                                  alpha=0.2, color=colors[i])
        
        # Configuración del gráfico
        ax.set_title('Proyecciones de Demanda por Producto y Ubicación', 
                    fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel('Fecha', fontsize=12)
        ax.set_ylabel('Demanda Proyectada (unidades)', fontsize=12)
        
        # Formato de fechas en eje X
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
        plt.xticks(rotation=45)
        
        # Leyenda
        if len(grouped) <= 10:  # Solo mostrar leyenda si no hay demasiadas líneas
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        
        # Grid
        ax.grid(True, alpha=0.3)
        
        # Ajustar layout
        plt.tight_layout()
        
        # Convertir a base64
        return self._fig_to_base64(fig)
    
    def _create_bar_chart(self, data: pd.DataFrame) -> str:
        """
        Crea gráfico de barras para proyecciones de demanda por día
        """
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Agrupar por fecha y sumar demanda total
        daily_demand = data.groupby('forecast_date')['predicted_demand'].sum().reset_index()
        
        # Crear gráfico de barras
        bars = ax.bar(daily_demand['forecast_date'], daily_demand['predicted_demand'], 
                     color='skyblue', alpha=0.8, edgecolor='navy')
        
        # Agregar valores en las barras
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f'{height:.1f}',
                       xy=(bar.get_x() + bar.get_width() / 2, height),
                       xytext=(0, 3),  # 3 points vertical offset
                       textcoords="offset points",
                       ha='center', va='bottom', fontsize=10)
        
        # Configuración
        ax.set_title('Demanda Total Proyectada por Día', 
                    fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel('Fecha', fontsize=12)
        ax.set_ylabel('Demanda Total (unidades)', fontsize=12)
        
        # Formato de fechas
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        plt.xticks(rotation=45)
        
        # Grid
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        return self._fig_to_base64(fig)
    
    def _create_area_chart(self, data: pd.DataFrame) -> str:
        """
        Crea gráfico de área apilada por modelo
        """
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Agrupar por fecha y modelo
        pivot_data = data.groupby(['forecast_date', 'model__model_type'])['predicted_demand'].sum().unstack(fill_value=0)
        
        # Crear gráfico de área apilada
        ax.stackplot(pivot_data.index, *[pivot_data[col] for col in pivot_data.columns], 
                    labels=pivot_data.columns, alpha=0.8)
        
        # Configuración
        ax.set_title('Proyecciones de Demanda por Modelo ML', 
                    fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel('Fecha', fontsize=12)
        ax.set_ylabel('Demanda Proyectada (unidades)', fontsize=12)
        
        # Formato de fechas
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        plt.xticks(rotation=45)
        
        # Leyenda
        ax.legend(loc='upper left')
        
        # Grid
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return self._fig_to_base64(fig)
    
    def _prepare_chart_data(self, data: pd.DataFrame) -> List[Dict]:
        """
        Prepara datos para el frontend
        """
        chart_data = []
        
        for _, row in data.iterrows():
            chart_data.append({
                'date': row['forecast_date'].strftime('%Y-%m-%d'),
                'predicted_demand': float(row['predicted_demand']),
                'lower_bound': float(row.get('lower_bound', 0)),
                'upper_bound': float(row.get('upper_bound', 0)),
                'product': row['product__name'],
                'location': row['location__name'],
                'model_type': row['model__model_type']
            })
        
        return chart_data
    
    def _calculate_stats(self, data: pd.DataFrame) -> Dict:
        """
        Calcula estadísticas de los pronósticos
        """
        stats = {
            'total_demand': float(data['predicted_demand'].sum()),
            'avg_daily_demand': float(data.groupby('forecast_date')['predicted_demand'].sum().mean()),
            'max_daily_demand': float(data.groupby('forecast_date')['predicted_demand'].sum().max()),
            'min_daily_demand': float(data.groupby('forecast_date')['predicted_demand'].sum().min()),
            'products_count': data['product__name'].nunique(),
            'locations_count': data['location__name'].nunique(),
            'date_range': {
                'start': data['forecast_date'].min().strftime('%Y-%m-%d'),
                'end': data['forecast_date'].max().strftime('%Y-%m-%d')
            }
        }
        
        return stats
    
    def _fig_to_base64(self, fig) -> str:
        """
        Convierte figura matplotlib a string base64
        """
        buffer = io.BytesIO()
        fig.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        
        image_png = buffer.getvalue()
        buffer.close()
        plt.close(fig)
        
        graphic = base64.b64encode(image_png)
        return graphic.decode('utf-8')
    
    def generate_model_comparison_chart(self, company_id: int) -> Dict:
        """
        Genera gráfico comparativo entre modelos ML
        """
        try:
            # Obtener métricas de modelos
            models = ForecastModel.objects.filter(
                company_id=company_id,
                status='active'
            ).values('name', 'model_type', 'mae', 'mape', 'rmse')
            
            if not models:
                return {
                    'error': 'No hay modelos activos para comparar',
                    'chart_image': None
                }
            
            df = pd.DataFrame(list(models))
            
            # Crear gráfico de comparación
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
            
            # MAE
            ax1.bar(df['model_type'], df['mae'], color='lightcoral')
            ax1.set_title('Mean Absolute Error (MAE)')
            ax1.set_ylabel('MAE')
            plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
            
            # MAPE
            ax2.bar(df['model_type'], df['mape'], color='lightblue')
            ax2.set_title('Mean Absolute Percentage Error (MAPE)')
            ax2.set_ylabel('MAPE (%)')
            plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
            
            # RMSE
            ax3.bar(df['model_type'], df['rmse'], color='lightgreen')
            ax3.set_title('Root Mean Square Error (RMSE)')
            ax3.set_ylabel('RMSE')
            plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45)
            
            # Pronósticos por modelo
            forecast_counts = DemandForecast.objects.filter(
                model__company_id=company_id
            ).values('model__model_type').annotate(
                count=Count('id')  # FIX: Usar Count importado
            )
            
            if forecast_counts:
                forecast_df = pd.DataFrame(list(forecast_counts))
                ax4.pie(forecast_df['count'], labels=forecast_df['model__model_type'], autopct='%1.1f%%')
                ax4.set_title('Distribución de Pronósticos por Modelo')
            
            plt.suptitle('Comparación de Modelos ML', fontsize=16, fontweight='bold')
            plt.tight_layout()
            
            chart_image = self._fig_to_base64(fig)
            
            return {
                'success': True,
                'chart_image': chart_image,
                'models_data': list(models)
            }
            
        except Exception as e:
            logger.error(f"Error generando gráfico de comparación: {str(e)}")
            return {
                'error': f'Error generando gráfico: {str(e)}',
                'chart_image': None
            }