from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Sum, Count, Q, F, DecimalField, Case, When, Value, Avg, Max, Min
from django.db.models.functions import TruncDate
from django.db import transaction
from django.utils import timezone
from datetime import datetime, timedelta
from drf_spectacular.utils import extend_schema
from datalens_backend.utils import get_default_company, get_company_for_user
from ..models import Category, Supplier, Product, Sale, Alert, InventoryHistory, Transaction, Customer, Lead, InventoryItem, Location

# Import forecasting models
from forecasting.models import DemandForecast, ReorderRecommendation

from ..serializers import (
    CategorySerializer, SupplierSerializer, ProductSerializer, SaleSerializer, 
    AlertSerializer, InventoryHistorySerializer, DashboardStatsSerializer, TransactionSerializer,
    CustomerSerializer, LeadSerializer, LocationSerializer, InventoryItemSerializer, OpportunitySerializer
)

import json
import openai
from django.conf import settings
from alerts.services import NotificationService
from alerts.models import Alert, AlertRule


class CategoryViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de categorías"""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Category.objects.filter(is_active=True).order_by('name')
    
    @action(detail=False, methods=['get'])
    def analytics(self, request):
        """
        🎯 ENDPOINT ESTRATÉGICO: Analytics completas por categoría
        Convierte datos administrativos en inteligencia de negocio
        """
        try:
            # Obtener filtros temporales del request (compatible con DRF y WSGIRequest)
            if hasattr(request, 'query_params'):
                # DRF Request
                start_date = request.query_params.get('start_date')
                end_date = request.query_params.get('end_date')
                compare_period = request.query_params.get('compare_period', 'previous_month')
            else:
                # WSGIRequest (para testing)
                start_date = request.GET.get('start_date')
                end_date = request.GET.get('end_date')
                compare_period = request.GET.get('compare_period', 'previous_month')
            
            print(f"🎯 CategoryAnalytics: Iniciando análisis estratégico de categorías...")
            
            # Calcular fechas para comparación
            if end_date:
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
            else:
                end_date_obj = timezone.now().date()
                
            if start_date:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
            else:
                # Por defecto: último mes
                start_date_obj = end_date_obj - timedelta(days=30)
            
            # Período anterior para comparación
            period_days = (end_date_obj - start_date_obj).days
            previous_start = start_date_obj - timedelta(days=period_days)
            previous_end = start_date_obj
            
            # REUTILIZAR lógica existente del DashboardView y extenderla
            categories_data = self._calculate_category_analytics(
                start_date_obj, end_date_obj, previous_start, previous_end
            )
            
            # Identificar categorías estratégicas
            strategic_insights = self._generate_strategic_insights(categories_data)
            
            response_data = {
                'strategic_metrics': strategic_insights['strategic_metrics'],
                'categories_performance': categories_data,
                'categories': categories_data,  # ALIAS para compatibilidad con frontend
                'period_info': {
                    'current_period': {
                        'start': start_date_obj.isoformat(),
                        'end': end_date_obj.isoformat(),
                        'days': period_days
                    },
                    'comparison_period': {
                        'start': previous_start.isoformat(),
                        'end': previous_end.isoformat(),
                        'days': period_days
                    }
                },
                'executive_summary': strategic_insights['executive_summary'],
                'quick_actions': strategic_insights['quick_actions'],
                'general_analytics': {  # ALIAS para compatibilidad con frontend
                    'avg_margin_percentage': strategic_insights['strategic_metrics'].get('average_margin', {}).get('numeric_value', 0)
                }
            }
            
            print(f"✅ CategoryAnalytics: Análisis completado para {len(categories_data)} categorías")
            return Response(response_data)
            
        except Exception as e:
            print(f"❌ Error en CategoryAnalytics: {str(e)}")
            return Response({
                'error': f'Error calculando analytics de categorías: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _calculate_category_analytics(self, start_date, end_date, previous_start, previous_end):
        """
        🔢 Calcula métricas financieras y operacionales por categoría
        REUTILIZA y EXTIENDE lógica del DashboardView existente
        """
        # Base query reutilizando DashboardView pattern
        categories_queryset = Category.objects.filter(is_active=True).prefetch_related('products')
        
        categories_data = []
        
        for category in categories_queryset:
            # Productos de la categoría
            products = category.products.filter(is_active=True)
            products_count = products.count()
            
            # Incluir todas las categorías, incluso sin productos
            if products_count == 0:
                # Categoría sin productos - valores en 0
                category_data = {
                    'category_id': category.id,
                    'category_name': category.name,
                    'description': category.description,
                    
                    # Métricas financieras en 0
                    'sales_current_period': 0.0,
                    'sales_previous_period': 0.0,
                    'sales_change_percentage': 0.0,
                    'avg_margin_percentage': 0.0,
                    
                    # Métricas operacionales en 0
                    'products_count': 0,
                    'products_with_alerts': 0,
                    'critical_products': 0,
                    'total_inventory_value': 0.0,
                    
                    # Indicadores visuales
                    'trend': 'stable',
                    'trend_icon': '➡️',
                    'operational_status': 'good',
                    'status_color': 'gray',
                    
                    # Datos para gráficos
                    'chart_data': {
                        'sales_trend': [0.0, 0.0],
                        'margin_vs_average': 0.0
                    }
                }
                
                categories_data.append(category_data)
                continue
                
            # MÉTRICAS FINANCIERAS - Reutilizar patrón de DashboardView
            # Ventas período actual
            current_sales = Transaction.objects.filter(
                product__in=products,
                transaction_type='sale',
                transaction_date__gte=start_date,
                transaction_date__lte=end_date
            ).aggregate(
                total_quantity=Sum('quantity') * -1,  # Convertir a positivo
                total_value=Sum(
                    Case(
                        When(product__sale_price__isnull=False,
                             then=F('quantity') * F('product__sale_price') * -1),
                        default=Value(0),
                        output_field=DecimalField(max_digits=15, decimal_places=2)
                    )
                )
            )
            
            # Ventas período anterior
            previous_sales = Transaction.objects.filter(
                product__in=products,
                transaction_type='sale',
                transaction_date__gte=previous_start,
                transaction_date__lte=previous_end
            ).aggregate(
                total_quantity=Sum('quantity') * -1,
                total_value=Sum(
                    Case(
                        When(product__sale_price__isnull=False,
                             then=F('quantity') * F('product__sale_price') * -1),
                        default=Value(0),
                        output_field=DecimalField(max_digits=15, decimal_places=2)
                    )
                )
            )
            
            # Calcular cambio porcentual
            current_value = float(current_sales['total_value'] or 0)
            previous_value = float(previous_sales['total_value'] or 0)
            
            if previous_value > 0:
                sales_change = ((current_value - previous_value) / previous_value) * 100
            else:
                sales_change = 100 if current_value > 0 else 0
            
            # MARGEN PROMEDIO - Cálculo manual más confiable
            total_margin = 0
            valid_products_for_margin = 0
            
            for product in products:
                if product.sale_price and product.cost_price and product.sale_price > 0:
                    margin = ((product.sale_price - product.cost_price) / product.sale_price) * 100
                    total_margin += margin
                    valid_products_for_margin += 1
            
            avg_margin = (total_margin / valid_products_for_margin) if valid_products_for_margin > 0 else 0
            
            # ALERTAS POR CATEGORÍA - Reutilizar patrón existente
            products_with_alerts = 0
            critical_products = 0
            
            for product in products:
                # Stock crítico
                if product.stock <= product.min_stock:
                    products_with_alerts += 1
                    if product.stock <= (product.min_stock * 0.5):
                        critical_products += 1
            
            # VALOR TOTAL DE INVENTARIO - Reutilizar DashboardView calculation
            total_inventory_value = products.aggregate(
                total_value=Sum(
                    Case(
                        When(stock__gt=0,
                             then=F('stock') * F('cost_price')),
                        default=Value(0),
                        output_field=DecimalField(max_digits=15, decimal_places=2)
                    )
                )
            )['total_value'] or 0
            
            # Determinar tendencia visual
            if sales_change > 5:
                trend = 'up'
                trend_icon = '📈'
            elif sales_change < -5:
                trend = 'down'
                trend_icon = '📉'
            else:
                trend = 'stable'
                trend_icon = '➡️'
            
            # Determinar estado operacional
            if critical_products > 0:
                operational_status = 'critical'
                status_color = 'red'
            elif products_with_alerts > 0:
                operational_status = 'warning'
                status_color = 'yellow'
            else:
                operational_status = 'good'
                status_color = 'green'
            
            category_data = {
                'category_id': category.id,
                'category_name': category.name,  # Usar category_name para consistencia
                'description': category.description,
                
                # Métricas financieras
                'sales_current_period': float(current_value),
                'sales_previous_period': float(previous_value),
                'sales_change_percentage': round(sales_change, 1),
                'avg_margin_percentage': float(avg_margin),
                
                # Métricas operacionales
                'products_count': products_count,
                'products_with_alerts': products_with_alerts,
                'critical_products': critical_products,
                'total_inventory_value': float(total_inventory_value),
                
                # Indicadores visuales
                'trend': trend,
                'trend_icon': trend_icon,
                'operational_status': operational_status,
                'status_color': status_color,
                
                # Datos para gráficos (reutilizar patrón existente)
                'chart_data': {
                    'sales_trend': [current_value, previous_value],
                    'margin_vs_average': float(avg_margin)
                }
            }
            
            categories_data.append(category_data)
        
        # Ordenar por valor de ventas descendente
        categories_data.sort(key=lambda x: x['sales_current_period'], reverse=True)
        
        return categories_data
    
    def _generate_strategic_insights(self, categories_data):
        """
        🧠 Genera insights estratégicos estilo Carlos Empresario
        REUTILIZA patrones del IntelligenceService existente
        """
        if not categories_data:
            return {
                'strategic_metrics': {},
                'executive_summary': 'No hay datos de categorías disponibles',
                'quick_actions': []
            }
        
        # Top performer
        top_category = categories_data[0]
        
        # Categoría con más problemas
        problem_category = max(
            categories_data, 
            key=lambda x: x['critical_products'] + x['products_with_alerts']
        )
        
        # Mejor oportunidad (mayor crecimiento)
        opportunity_category = max(
            categories_data,
            key=lambda x: x['sales_change_percentage'] if x['sales_change_percentage'] > 0 else -100
        )
        
        # Margen promedio general (calculado correctamente con todos los productos)
        all_products = Product.objects.filter(is_active=True)
        total_margin = 0
        valid_products = 0
        
        for product in all_products:
            if product.sale_price and product.cost_price and product.sale_price > 0:
                margin = ((product.sale_price - product.cost_price) / product.sale_price) * 100
                total_margin += margin
                valid_products += 1
        
        avg_margin_general = (total_margin / valid_products) if valid_products > 0 else 0
        
        strategic_metrics = {
            'top_sales_category': {
                'name': top_category['category_name'],
                'change': f"+{top_category['sales_change_percentage']:.1f}% vs mes anterior" if top_category['sales_change_percentage'] > 0 else f"{top_category['sales_change_percentage']:.1f}% vs mes anterior",
                'icon': '🏆'
            },
            'most_alerts_category': {
                'name': problem_category['category_name'],
                'critical_count': problem_category['critical_products'],
                'total_alerts': problem_category['products_with_alerts'],
                'icon': '🚨'
            },
            'average_margin': {
                'value': f"{avg_margin_general:.1f}%",
                'numeric_value': round(avg_margin_general, 1),  # Para compatibilidad con frontend
                'description': 'general',
                'icon': '💰'
            },
            'opportunity_category': {
                'name': opportunity_category['category_name'],
                'growth': f"+{opportunity_category['sales_change_percentage']:.1f}%" if opportunity_category['sales_change_percentage'] > 0 else "demanda estable",
                'icon': '🚀'
            }
        }
        
        # Executive summary estilo briefing matutino
        executive_summary = f"""
        📊 **Análisis Estratégico de Categorías:**
        
        🏆 **Mejor performance:** {top_category['category_name']} lidera con {top_category['sales_change_percentage']:+.1f}%
        
        🚨 **Requiere atención:** {problem_category['category_name']} tiene {problem_category['critical_products']} productos críticos
        
        🚀 **Oportunidad detectada:** {opportunity_category['category_name']} {f"creciendo +{opportunity_category['sales_change_percentage']:.1f}%" if opportunity_category['sales_change_percentage'] > 0 else "lista para impulso"}
        
        💰 **Margen promedio:** {avg_margin_general:.1f}% general
        """.strip()
        
        # Quick actions accionables
        quick_actions = [
            {
                'category_id': top_category['category_id'],
                'action': 'analyze_trends',
                'title': f'Analizar {top_category["category_name"]}',
                'description': 'Ver detalles del top performer',
                'priority': 'medium'
            },
            {
                'category_id': problem_category['category_id'],
                'action': 'review_critical',
                'title': f'Revisar {problem_category["category_name"]}',
                'description': f'{problem_category["critical_products"]} productos necesitan atención',
                'priority': 'high'
            },
            {
                'category_id': opportunity_category['category_id'],
                'action': 'expand_inventory',
                'title': f'Ampliar {opportunity_category["category_name"]}',
                'description': 'Aprovechar tendencia de crecimiento',
                'priority': 'medium'
            }
        ]
        
        return {
            'strategic_metrics': strategic_metrics,
            'executive_summary': executive_summary,
            'quick_actions': quick_actions
        }
    
    @action(detail=False, methods=['get'])
    def sales_trends(self, request):
        """
        📈 ENDPOINT OPTIMIZADO: Tendencias de ventas por categoría con comparación temporal
        REUTILIZA y EXTIENDE lógica existente del DashboardView
        """
        try:
            # Obtener parámetros temporales
            period = request.query_params.get('period', '30days')  # 30days, 90days, 12months
            compare_with = request.query_params.get('compare_with', 'previous_period')
            
            print(f"📈 CategorySalesTrends: Calculando tendencias para período {period}")
            
            # Calcular fechas según período
            end_date = timezone.now().date()
            
            if period == '90days':
                start_date = end_date - timedelta(days=90)
                period_days = 90
            elif period == '12months':
                start_date = end_date - timedelta(days=365)
                period_days = 365
            else:  # 30days default
                start_date = end_date - timedelta(days=30)
                period_days = 30
            
            # Período anterior para comparación
            previous_start = start_date - timedelta(days=period_days)
            previous_end = start_date
            
            # REUTILIZAR y EXTENDER lógica del DashboardView
            trends_data = self._calculate_category_sales_trends(
                start_date, end_date, previous_start, previous_end, period_days
            )
            
            response_data = {
                'period_info': {
                    'current_period': {
                        'start': start_date.isoformat(),
                        'end': end_date.isoformat(),
                        'days': period_days
                    },
                    'comparison_period': {
                        'start': previous_start.isoformat(),
                        'end': previous_end.isoformat(),
                        'days': period_days
                    }
                },
                'categories_trends': trends_data,
                'summary': self._generate_trends_summary(trends_data),
                'generated_at': timezone.now().isoformat()
            }
            
            print(f"✅ CategorySalesTrends: Análisis completado para {len(trends_data)} categorías")
            return Response(response_data)
            
        except Exception as e:
            print(f"❌ Error en CategorySalesTrends: {str(e)}")
            return Response({
                'error': f'Error calculando tendencias de ventas: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _calculate_category_sales_trends(self, start_date, end_date, previous_start, previous_end, period_days):
        """
        📊 Calcular tendencias de ventas por categoría con comparación temporal
        REUTILIZA patrón del DashboardView.stock_by_category y lo extiende
        """
        # Base query REUTILIZANDO patrón existente del DashboardView
        categories_queryset = Category.objects.filter(is_active=True).prefetch_related('products')
        
        trends_data = []
        
        for category in categories_queryset:
            # Productos de la categoría (REUTILIZAR filtrado existente)
            products = category.products.filter(is_active=True)
            products_count = products.count()
            
            if products_count == 0:
                continue
            
            # VENTAS PERÍODO ACTUAL - Usando patrón del CategoryViewSet.analytics
            current_sales = Transaction.objects.filter(
                product__in=products,
                transaction_type='sale',
                transaction_date__gte=start_date,
                transaction_date__lte=end_date
            ).aggregate(
                total_quantity=Sum('quantity') * -1,  # Convertir a positivo
                total_transactions=Count('id'),
                total_value=Sum(
                    Case(
                        When(product__sale_price__isnull=False,
                             then=F('quantity') * F('product__sale_price') * -1),
                        default=Value(0),
                        output_field=DecimalField(max_digits=15, decimal_places=2)
                    )
                ),
                avg_transaction_value=Avg(
                    Case(
                        When(product__sale_price__isnull=False,
                             then=F('quantity') * F('product__sale_price') * -1),
                        default=Value(0),
                        output_field=DecimalField(max_digits=15, decimal_places=2)
                    )
                )
            )
            
            # VENTAS PERÍODO ANTERIOR - Para comparación
            previous_sales = Transaction.objects.filter(
                product__in=products,
                transaction_type='sale',
                transaction_date__gte=previous_start,
                transaction_date__lte=previous_end
            ).aggregate(
                total_quantity=Sum('quantity') * -1,
                total_transactions=Count('id'),
                total_value=Sum(
                    Case(
                        When(product__sale_price__isnull=False,
                             then=F('quantity') * F('product__sale_price') * -1),
                        default=Value(0),
                        output_field=DecimalField(max_digits=15, decimal_places=2)
                    )
                )
            )
            
            # CALCULAR MÉTRICAS DE COMPARACIÓN
            current_quantity = float(current_sales['total_quantity'] or 0)
            current_value = float(current_sales['total_value'] or 0)
            current_transactions = current_sales['total_transactions'] or 0
            
            previous_quantity = float(previous_sales['total_quantity'] or 0)
            previous_value = float(previous_sales['total_value'] or 0)
            previous_transactions = previous_sales['total_transactions'] or 0
            
            # Calcular cambios porcentuales
            quantity_change = self._calculate_percentage_change(current_quantity, previous_quantity)
            value_change = self._calculate_percentage_change(current_value, previous_value)
            transactions_change = self._calculate_percentage_change(current_transactions, previous_transactions)
            
            # TENDENCIA SEMANAL - Breakdown más granular
            weekly_trend = self._calculate_weekly_breakdown(
                products, start_date, end_date, period_days
            )
            
            # VALOR PROMEDIO POR TRANSACCIÓN
            avg_transaction_current = current_value / current_transactions if current_transactions > 0 else 0
            avg_transaction_previous = previous_value / previous_transactions if previous_transactions > 0 else 0
            avg_transaction_change = self._calculate_percentage_change(avg_transaction_current, avg_transaction_previous)
            
            # DETERMINAR TENDENCIA VISUAL (REUTILIZAR patrón de CategoryViewSet.analytics)
            if value_change > 10:
                trend_direction = 'strong_growth'
                trend_icon = '🚀'
                trend_color = 'green'
            elif value_change > 5:
                trend_direction = 'growth'
                trend_icon = '📈'
                trend_color = 'light-green'
            elif value_change > -5:
                trend_direction = 'stable'
                trend_icon = '➡️'
                trend_color = 'blue'
            elif value_change > -10:
                trend_direction = 'decline'
                trend_icon = '📉'
                trend_color = 'orange'
            else:
                trend_direction = 'strong_decline'
                trend_icon = '🔻'
                trend_color = 'red'
            
            # PERFORMANCE SCORE - Métrica compuesta para ranking
            performance_score = self._calculate_performance_score(
                current_value, value_change, current_transactions, transactions_change
            )
            
            category_trend = {
                'category_id': category.id,
                'category_name': category.name,
                'products_count': products_count,
                
                # Métricas del período actual
                'current_period': {
                    'quantity_sold': current_quantity,
                    'sales_value': current_value,
                    'transactions_count': current_transactions,
                    'avg_transaction_value': float(current_sales['avg_transaction_value'] or 0)
                },
                
                # Métricas del período anterior
                'previous_period': {
                    'quantity_sold': previous_quantity,
                    'sales_value': previous_value,
                    'transactions_count': previous_transactions
                },
                
                # Análisis de cambios
                'changes': {
                    'quantity_change_pct': quantity_change,
                    'value_change_pct': value_change,
                    'transactions_change_pct': transactions_change,
                    'avg_transaction_change_pct': avg_transaction_change
                },
                
                # Indicadores visuales
                'trend': {
                    'direction': trend_direction,
                    'icon': trend_icon,
                    'color': trend_color
                },
                
                # Datos para gráficos
                'weekly_breakdown': weekly_trend,
                'performance_score': performance_score
            }
            
            trends_data.append(category_trend)
        
        # Ordenar por performance score (mejores primero)
        trends_data.sort(key=lambda x: x['performance_score'], reverse=True)
        
        return trends_data
    
    def _calculate_percentage_change(self, current, previous):
        """Calcular cambio porcentual de manera segura"""
        if previous == 0:
            return 100 if current > 0 else 0
        return round(((current - previous) / previous) * 100, 1)
    
    def _calculate_weekly_breakdown(self, products, start_date, end_date, period_days):
        """Calcular breakdown semanal de ventas"""
        weeks = min(period_days // 7, 8)  # Máximo 8 semanas para performance
        weekly_data = []
        
        for week in range(weeks):
            week_start = end_date - timedelta(days=(week + 1) * 7)
            week_end = end_date - timedelta(days=week * 7)
            
            week_sales = Transaction.objects.filter(
                product__in=products,
                transaction_type='sale',
                transaction_date__gte=week_start,
                transaction_date__lt=week_end
            ).aggregate(
                value=Sum(
                    Case(
                        When(product__sale_price__isnull=False,
                             then=F('quantity') * F('product__sale_price') * -1),
                        default=Value(0),
                        output_field=DecimalField(max_digits=15, decimal_places=2)
                    )
                )
            )['value'] or 0
            
            weekly_data.append({
                'week_label': f'Sem {weeks - week}',
                'week_start': week_start.isoformat(),
                'week_end': week_end.isoformat(),
                'sales_value': float(week_sales)
            })
        
        return list(reversed(weekly_data))  # Orden cronológico
    
    def _calculate_performance_score(self, current_value, value_change, current_transactions, transactions_change):
        """Calcular score de performance para ranking"""
        # Combinar valor absoluto y crecimiento
        value_score = current_value * 0.7  # 70% peso al valor actual
        growth_score = max(0, value_change) * current_value * 0.01  # 30% peso al crecimiento
        transaction_bonus = current_transactions * 10  # Bonus por volumen de transacciones
        
        return round(value_score + growth_score + transaction_bonus, 2)
    
    def _generate_trends_summary(self, trends_data):
        """Generar resumen de tendencias estilo Carlos Empresario"""
        if not trends_data:
            return "No hay datos de tendencias disponibles"
        
        # Métricas generales
        total_categories = len(trends_data)
        growing_categories = len([t for t in trends_data if t['changes']['value_change_pct'] > 5])
        declining_categories = len([t for t in trends_data if t['changes']['value_change_pct'] < -5])
        stable_categories = total_categories - growing_categories - declining_categories
        
        # Top performer
        top_performer = trends_data[0] if trends_data else None
        
        # Categoría con mayor crecimiento
        best_growth = max(trends_data, key=lambda x: x['changes']['value_change_pct']) if trends_data else None
        
        summary = f"""
        📊 **Resumen de Tendencias por Categorías:**
        
        🎯 **Top performer:** {top_performer['category_name']} (S/{top_performer['current_period']['sales_value']:.2f})
        
        🚀 **Mayor crecimiento:** {best_growth['category_name']} ({best_growth['changes']['value_change_pct']:+.1f}%)
        
        📈 **Creciendo:** {growing_categories} categorías (+5% o más)
        📉 **Declinando:** {declining_categories} categorías (-5% o menos) 
        ➡️ **Estables:** {stable_categories} categorías
        
        💡 **Insight:** {growing_categories / total_categories * 100:.0f}% de categorías en crecimiento
        """.strip()
        
        return summary


class SupplierViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de proveedores"""
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        try:
            return Supplier.objects.filter(is_active=True).order_by('name')
        except Exception as e:
            print(f"Error in SupplierViewSet.get_queryset: {e}")
            return Supplier.objects.none()
    
    def list(self, request, *args, **kwargs):
        """Override del método list para manejo robusto de errores"""
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return Response({
                'count': queryset.count(),
                'results': serializer.data
            })
        except Exception as e:
            return Response({
                'count': 0,
                'results': [],
                'error': f'Suppliers service temporarily unavailable: {str(e)}'
            })


class ProductViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de productos"""
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        """Override del método create para agregar logging detallado"""
        print(f"🚀 ProductViewSet.create() - Iniciando creación de producto...")
        print(f"📝 request.data: {request.data}")
        print(f"🔍 request.user: {request.user}")
        print(f"🔍 request.headers: {dict(request.headers)}")
        print(f"🔍 request.method: {request.method}")
        
        try:
            # Validar datos con el serializer
            serializer = self.get_serializer(data=request.data)
            print(f"🔧 Serializer creado: {type(serializer).__name__}")
            
            print(f"🔍 Validando datos del serializer...")
            if serializer.is_valid():
                print(f"✅ Datos válidos: {serializer.validated_data}")
                
                # Llamar al método perform_create
                print(f"💾 Llamando a perform_create...")
                self.perform_create(serializer)
                
                headers = self.get_success_headers(serializer.data)
                response_data = serializer.data
                print(f"✅ Producto creado exitosamente: {response_data}")
                
                return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)
            else:
                print(f"❌ ERRORES DE VALIDACIÓN:")
                for field, errors in serializer.errors.items():
                    print(f"   🔥 Campo '{field}': {errors}")
                print(f"❌ serializer.errors completo: {serializer.errors}")
                
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            print(f"❌ EXCEPCIÓN en ProductViewSet.create: {str(e)}")
            print(f"📋 Tipo de error: {type(e).__name__}")
            import traceback
            print(f"🔍 Traceback completo: {traceback.format_exc()}")
            
            return Response({
                'error': 'Error interno al crear producto',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def get_queryset(self):
        try:
            user = self.request.user
            
            # Si es superadmin, mostrar TODOS los productos sin filtro de empresa
            if hasattr(user, 'role') and user.role == 'superadmin':
                return Product.objects.filter(
                    is_active=True
                ).select_related('category', 'supplier').order_by('name')
            
            # Para otros usuarios, filtrar por empresa si tienen una
            if hasattr(user, 'company') and user.company:
                return Product.objects.filter(
                    is_active=True,
                    company=user.company
                ).select_related('category', 'supplier').order_by('name')
            
            # Fallback: mostrar todos los productos si no hay empresa definida
            return Product.objects.filter(
                is_active=True
            ).select_related('category', 'supplier').order_by('name')
            
        except Exception as e:
            print(f"Error in ProductViewSet.get_queryset: {e}")
            # En caso de error, superadmin ve todo, otros ven productos sin empresa
            if hasattr(self.request.user, 'role') and self.request.user.role == 'superadmin':
                return Product.objects.filter(is_active=True)
            return Product.objects.none()
    
    def list(self, request, *args, **kwargs):
        """Override del método list para manejo robusto de errores"""
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return Response({
                'count': queryset.count(),
                'results': serializer.data
            })
        except Exception as e:
            return Response({
                'count': 0,
                'results': [],
                'error': f'Products service temporarily unavailable: {str(e)}'
            })
    
    def perform_create(self, serializer):
        print(f"🔍 ProductViewSet.perform_create() - Iniciando creación de producto...")
        print(f"📝 Datos recibidos: {self.request.data}")
        print(f"🔍 Usuario: {self.request.user}")
        
        try:
            # FIX: Mostrar datos validados
            validated_data = serializer.validated_data
            print(f"✅ Datos validados: {validated_data}")
            
            # Asegurar que price se sincronice con sale_price si no se proporciona
            if not validated_data.get('price') and validated_data.get('sale_price'):
                validated_data['price'] = validated_data['sale_price']
                print(f"🔄 Sincronizando price con sale_price: {validated_data['price']}")
            
            # FIX: Asignar empresa por defecto
            try:
                from datalens_backend.utils import get_default_company
                company = get_default_company()
                if company:
                    validated_data['company'] = company
                    print(f"🏢 Asignando empresa por defecto: {company.name}")
                else:
                    print("⚠️ No se encontró empresa por defecto")
            except Exception as e:
                print(f"⚠️ Error obteniendo empresa: {e}")
            
            # FIX: Valores por defecto para campos requeridos si no se proporcionan
            defaults = {
                'stock': 0,
                'min_stock': 0,
                'max_stock': 0,
                'cost_price': 0.0,
                'sale_price': 0.0,
                'unit': 'unidad',
                'is_active': True
            }
            
            for field, default_value in defaults.items():
                if field not in validated_data or validated_data[field] is None:
                    validated_data[field] = default_value
                    print(f"🔧 Asignando valor por defecto {field}: {default_value}")
            
            print(f"💾 Guardando producto con datos finales: {validated_data}")
            product = serializer.save()
            print(f"✅ Producto creado exitosamente: {product.id} - {product.name}")
            
        except Exception as e:
            print(f"❌ Error en ProductViewSet.perform_create: {str(e)}")
            print(f"📋 Tipo de error: {type(e).__name__}")
            import traceback
            print(f"🔍 Traceback completo: {traceback.format_exc()}")
            raise  # Re-lanzar el error para que DRF lo maneje correctamente
    
    def perform_update(self, serializer):
        # Mantener sincronización de precios
        if 'sale_price' in serializer.validated_data and 'price' not in serializer.validated_data:
            serializer.validated_data['price'] = serializer.validated_data['sale_price']
        serializer.save()
    
    @action(detail=True, methods=['get'])
    def stock(self, request, pk=None):
        """Obtener información detallada del stock de un producto"""
        product = self.get_object()
        stock_data = {
            'product_id': product.id,
            'product_name': product.name,
            'product_sku': product.sku,
            'current_stock': product.current_stock,
            'min_stock': product.min_stock,
            'max_stock': product.max_stock,
            'stock_value': product.stock_value,
            'stock_status': self._get_stock_status(product)
        }
        return Response(stock_data)
    
    def _get_stock_status(self, product):
        """Determinar el estado del stock"""
        current = product.current_stock
        if current <= 0:
            return 'out_of_stock'
        elif current <= product.min_stock:
            return 'low_stock'
        elif current >= product.max_stock:
            return 'high_stock'
        return 'normal'

    def destroy(self, request, *args, **kwargs):
        """Override del método destroy para eliminación completa"""
        try:
            product = self.get_object()
            product_name = product.name
            product_id = product.id
            
            # Log de la eliminación
            print(f"🗑️ Eliminando producto {product_id}: {product_name}")
            
            # Eliminación en transacción atómica
            with transaction.atomic():
                # Eliminar registros relacionados primero
                if hasattr(product, 'sales'):
                    product.sales.all().delete()
                if hasattr(product, 'inventory_items'):
                    product.inventory_items.all().delete()
                if hasattr(product, 'alert_set'):
                    product.alert_set.all().delete()
                if hasattr(product, 'demand_forecasts'):
                    product.demand_forecasts.all().delete()
                
                # Eliminar el producto
                product.delete()
                
            print(f"✅ Producto {product_name} eliminado completamente")
            
            return Response({
                'message': f'Producto "{product_name}" eliminado exitosamente',
                'deleted_product_id': product_id
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"❌ Error eliminando producto: {str(e)}")
            return Response({
                'error': f'Error al eliminar producto: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def update(self, request, *args, **kwargs):
        """Override del método update para asegurar actualización completa"""
        try:
            product = self.get_object()
            original_name = product.name
            
            print(f"✏️ Actualizando producto {product.id}: {original_name}")
            print(f"📝 Datos nuevos: {request.data}")
            
            # Actualización estándar
            partial = kwargs.pop('partial', False)
            serializer = self.get_serializer(product, data=request.data, partial=partial)
            
            if serializer.is_valid():
                self.perform_update(serializer)
                
                updated_product = serializer.instance
                print(f"✅ Producto actualizado: {updated_product.name}")
                
                # Respuesta con datos completos
                return Response({
                    'message': f'Producto "{updated_product.name}" actualizado exitosamente',
                    'product': serializer.data
                }, status=status.HTTP_200_OK)
            else:
                print(f"❌ Errores de validación: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            print(f"❌ Error actualizando producto: {str(e)}")
            return Response({
                'error': f'Error al actualizar producto: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SaleViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de ventas"""
    queryset = Sale.objects.all()
    serializer_class = SaleSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Sale.objects.select_related('product').order_by('-date_sold')
    
    def perform_create(self, serializer):
        # Actualizar stock del producto
        with transaction.atomic():
            sale = serializer.save()
            product = sale.product
            
            # Registrar cambio en historial
            InventoryHistory.objects.create(
                product=product,
                stock_before=product.stock,
                stock_after=product.stock - sale.quantity,
                change_reason=f"Venta #{sale.id}",
                user=self.request.user
            )
            
            # Actualizar stock
            product.stock = F('stock') - sale.quantity
            product.save()


class AlertViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de alertas"""
    queryset = Alert.objects.all()
    serializer_class = AlertSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Alert.objects.select_related('product').order_by('-created_at')
    
    @action(detail=False, methods=['post'])
    def check_alerts(self, request):
        """Verificar y crear alertas automáticas"""
        alerts_created = []
        
        # Alertas de stock bajo
        low_stock_products = Product.objects.filter(
            is_active=True,
            stock__lte=F('min_stock')
        )
        
        for product in low_stock_products:
            alert, created = Alert.objects.get_or_create(
                product=product,
                severity='medium',
                is_active=True,
                defaults={
                    'message': f'Stock bajo para {product.name} (SKU: {product.sku}). Stock actual: {product.stock}, mínimo: {product.min_stock}'
                }
            )
            if created:
                alerts_created.append(alert.id)
        
        return Response({
            'alerts_created': len(alerts_created),
            'alert_ids': alerts_created
        })


class InventoryHistoryViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de historial de inventario"""
    queryset = InventoryHistory.objects.all()
    serializer_class = InventoryHistorySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return InventoryHistory.objects.select_related('product', 'user').order_by('-date_changed')


class TransactionViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de transacciones"""
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Transaction.objects.select_related('product', 'location', 'created_by').order_by('-transaction_date')
    
    def list(self, request, *args, **kwargs):
        """Override del método list con paginación completa"""
        try:
            # Parámetros de paginación
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 20))
            
            queryset = self.get_queryset()
            total_count = queryset.count()
            
            # Calcular offset
            start = (page - 1) * page_size
            end = start + page_size
            
            # Obtener transacciones para la página actual
            transactions = queryset[start:end]
            serializer = self.get_serializer(transactions, many=True)
            
            # Calcular información de paginación
            total_pages = (total_count + page_size - 1) // page_size
            has_next = page < total_pages
            has_previous = page > 1
            
            return Response({
                'count': total_count,
                'results': serializer.data,
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total_pages': total_pages,
                    'has_next': has_next,
                    'has_previous': has_previous,
                    'showing_from': start + 1,
                    'showing_to': min(end, total_count),
                    'total_count': total_count
                }
            })
        except Exception as e:
            return Response({
                'count': 0,
                'results': [],
                'error': f'Transactions service temporarily unavailable: {str(e)}'
            })
    
    def perform_create(self, serializer):
        # Asignar el usuario current como creador
        serializer.save(created_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Obtener transacciones recientes (últimos 30 días)"""
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_transactions = self.get_queryset().filter(
            transaction_date__gte=thirty_days_ago
        )[:20]
        
        serializer = self.get_serializer(recent_transactions, many=True)
        return Response({
            'count': recent_transactions.count(),
            'results': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def by_product(self, request):
        """Obtener transacciones por producto"""
        product_id = request.query_params.get('product_id')
        if not product_id:
            return Response({'error': 'product_id is required'}, status=400)
        
        transactions = self.get_queryset().filter(product_id=product_id)
        serializer = self.get_serializer(transactions, many=True)
        return Response({
            'count': transactions.count(),
            'results': serializer.data
        })


class DashboardView(APIView):
    """Vista para el dashboard principal de inventario con soporte para filtros"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Obtener estadísticas del dashboard",
        description="Retorna métricas y estadísticas principales del inventario con soporte para filtros"
    )
    def get(self, request):
        print(f"🔍 DashboardView.get() - Iniciando cálculo de estadísticas...")
        try:
            # Obtener filtros de la request
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')
            category = request.query_params.get('category')
            warehouse = request.query_params.get('warehouse')
            
            # Procesar filtros de fecha
            date_filter = {}
            if start_date:
                try:
                    date_filter['transaction_date__gte'] = datetime.strptime(start_date, '%Y-%m-%d')
                except ValueError:
                    pass
            if end_date:
                try:
                    date_filter['transaction_date__lte'] = datetime.strptime(end_date, '%Y-%m-%d')
                except ValueError:
                    pass
            
            # Filtros para productos
            product_filter = {'is_active': True}
            if category and category != 'all':
                product_filter['category__name__icontains'] = category
            
            # Filtros para inventory items
            inventory_filter = {'product__is_active': True}
            if warehouse and warehouse != 'all':
                inventory_filter['location__name__icontains'] = warehouse
            
            from inventory.models import InventoryItem
            
            # Estadísticas básicas con filtros
            total_products = Product.objects.filter(**product_filter).count()
            total_categories = Category.objects.filter(is_active=True).count()
            total_suppliers = Supplier.objects.filter(is_active=True).count()
            
            print(f"📊 Productos activos: {total_products}")
            print(f"📊 Categorías activas: {total_categories}")
            print(f"📊 Proveedores activos: {total_suppliers}")
            
            # Calcular valor total con filtros - CORREGIDO CON CAST
            total_stock_value = InventoryItem.objects.filter(**inventory_filter).aggregate(
                total_value=Sum(
                    Case(
                        When(quantity__isnull=False,
                             then=F('quantity') * F('unit_cost')),
                        default=Value(0),
                        output_field=DecimalField(max_digits=15, decimal_places=2)
                    )
                )
            )['total_value'] or 0
            
            print(f"💰 Valor total de inventario: {total_stock_value}")
            
            # Stock crítico con filtros
            low_stock_items = InventoryItem.objects.filter(
                quantity__lt=30,
                **inventory_filter
            )
            low_stock_products = low_stock_items.count()
            
            print(f"⚠️ Items con stock crítico (<30): {low_stock_products}")
            
            # Productos sin stock con filtros
            out_of_stock_products = InventoryItem.objects.filter(
                quantity__lte=0,
                **inventory_filter
            ).count()
            
            print(f"❌ Items sin stock: {out_of_stock_products}")
            
            # Transacciones con filtros de fecha
            transaction_filter = {}
            if not date_filter:
                # Por defecto, últimos 7 días
                seven_days_ago = timezone.now() - timedelta(days=7)
                transaction_filter['transaction_date__gte'] = seven_days_ago
            else:
                transaction_filter.update(date_filter)
            
            try:
                recent_transactions = Transaction.objects.filter(**transaction_filter).count()
                # Transacciones de hoy específicamente
                today = timezone.now().date()
                today_transactions = Transaction.objects.filter(
                    transaction_date__date=today
                ).count()
            except Exception:
                recent_transactions = 0
                today_transactions = 0
            
            print(f"📈 Transacciones filtradas: {recent_transactions}")
            print(f"📈 Transacciones hoy: {today_transactions}")
            
            # Alertas activas
            try:
                from alerts.models import Alert
                active_alerts = Alert.objects.filter(status='active').count()
            except Exception:
                active_alerts = 0
            
            print(f"🚨 Alertas activas: {active_alerts}")
            
            # Top productos por valor con filtros - CORREGIDO CON CAST
            try:
                top_products = list(InventoryItem.objects.select_related('product').filter(
                    **inventory_filter
                ).annotate(
                    total_value=Case(
                        When(quantity__isnull=False,
                             then=F('quantity') * F('unit_cost')),
                        default=Value(0),
                        output_field=DecimalField(max_digits=15, decimal_places=2)
                    )
                ).order_by('-total_value')[:5].values(
                    'product__id', 'product__name', 'product__sku', 
                    'quantity', 'total_value', 'location__name'
                ))
            except Exception as e:
                print(f"❌ Error obteniendo top productos: {e}")
                top_products = []
            
            # DATOS PARA GRÁFICOS (CORREGIDOS)
            try:
                # Stock por categoría (para gráfico de distribución) - CORREGIDO CON CAST
                products_by_category = list(Category.objects.filter(
                    is_active=True,
                    products__is_active=True
                ).annotate(
                    count=Count('products', distinct=True),
                    total_stock=Sum('products__inventory_items__quantity'),
                    total_value=Sum(
                        Case(
                            When(products__inventory_items__quantity__isnull=False,
                                 then=F('products__inventory_items__quantity') * F('products__inventory_items__unit_cost')),
                            default=Value(0),
                            output_field=DecimalField(max_digits=15, decimal_places=2)
                        )
                    )
                ).values('name', 'count', 'total_stock', 'total_value'))
                
                # Formatear para frontend
                products_by_category = [
                    {
                        'category': cat['name'],
                        'value': cat['count'] or 0,
                        'stock': cat['total_stock'] or 0,
                        'total_value': float(cat['total_value'] or 0)
                    }
                    for cat in products_by_category
                ]
                
                # Stock por ubicación (para gráfico de almacenes) - CORREGIDO CON CAST
                stock_by_warehouse = list(Location.objects.annotate(
                    current_stock=Sum('inventory_items__quantity'),
                    total_items=Count('inventory_items'),
                    total_value=Sum(
                        Case(
                            When(inventory_items__quantity__isnull=False,
                                 then=F('inventory_items__quantity') * F('inventory_items__unit_cost')),
                            default=Value(0),
                            output_field=DecimalField(max_digits=15, decimal_places=2)
                        )
                    )
                ).values('name', 'current_stock', 'total_items', 'total_value'))
                
                # Formatear para frontend
                stock_by_warehouse = [
                    {
                        'warehouse': loc['name'],
                        'current_stock': loc['current_stock'] or 0,
                        'min_stock': 50,  # Valor por defecto
                        'max_stock': 500,  # Valor por defecto
                        'total_items': loc['total_items'] or 0,
                        'total_value': float(loc['total_value'] or 0)
                    }
                    for loc in stock_by_warehouse
                ]
                
                # Tendencia de transacciones (últimos 30 días)
                thirty_days_ago = timezone.now() - timedelta(days=30)
                transactions_trend = Transaction.objects.filter(
                    transaction_date__gte=thirty_days_ago
                ).extra(
                    select={'date': 'DATE(transaction_date)'}
                ).values('date').annotate(
                    sales=Sum('quantity', filter=Q(transaction_type='sale')),
                    purchases=Sum('quantity', filter=Q(transaction_type='purchase'))
                ).order_by('date')
                
                # Formatear para frontend
                # CORREGIDO: Usar abs() para ventas ya que están en negativo en la BD
                sales_trend = [
                    {
                        'date': str(item['date']),
                        'sales': abs(item['sales']) if item['sales'] else 0,
                        'forecast': float(abs(item['sales'])) * 1.05 if item['sales'] else 0 # Estimación simple
                    }
                    for item in transactions_trend
                ]
                
            except Exception as e:
                import traceback
                print(f"❌ Error generando datos para gráficos: {e}")
                print(f"🔍 TRACEBACK COMPLETO:")
                traceback.print_exc()
                products_by_category = []
                stock_by_warehouse = []
                sales_trend = []
            
            # NUEVO: Métricas temporales con comparación
            try:
                # Comparar con período anterior
                if date_filter:
                    # Si hay filtros de fecha, comparar con período anterior de igual duración
                    period_days = (datetime.strptime(end_date, '%Y-%m-%d') - datetime.strptime(start_date, '%Y-%m-%d')).days if start_date and end_date else 30
                else:
                    period_days = 30
                
                previous_period_start = timezone.now() - timedelta(days=period_days*2)
                previous_period_end = timezone.now() - timedelta(days=period_days)
                
                previous_transactions = Transaction.objects.filter(
                    transaction_date__gte=previous_period_start,
                    transaction_date__lte=previous_period_end
                ).count()
                
                # Calcular cambio porcentual
                if previous_transactions > 0:
                    transaction_change = ((recent_transactions - previous_transactions) / previous_transactions) * 100
                else:
                    transaction_change = 0
                
                # Calcular cambio en valor de inventario (estimado)
                inventory_change = 5.2  # Placeholder - se puede calcular con historical data
                
            except Exception as e:
                transaction_change = 0
                inventory_change = 0
                print(f"❌ Error calculando cambios: {e}")
            
            # Respuesta completa con todos los datos
            dashboard_data = {
                # Métricas principales
                'total_products': total_products,
                'total_categories': total_categories,
                'total_suppliers': total_suppliers,
                'total_stock_value': float(total_stock_value),
                'low_stock_products': low_stock_products,
                'out_of_stock_products': out_of_stock_products,
                'recent_transactions': recent_transactions,
                'active_alerts': active_alerts,
                
                # Aliases para compatibilidad con frontend
                'total_value': float(total_stock_value),
                'low_stock_alerts': low_stock_products,
                'total_transactions_today': today_transactions,
                'active_customers': 0,
                'pipeline_value': 0,
                
                # DATOS PARA GRÁFICOS (CORREGIDOS)
                'products_by_category': products_by_category,
                'stock_by_warehouse': stock_by_warehouse,
                'sales_trend': sales_trend,
                
                # NUEVO: Métricas temporales con contexto
                'period_info': {
                    'start_date': start_date,
                    'end_date': end_date,
                    'period_days': period_days if 'period_days' in locals() else 30,
                    'transaction_change': round(transaction_change, 1),
                    'inventory_change': round(inventory_change, 1),
                    'timeframe': f"últimos {period_days if 'period_days' in locals() else 30} días"
                },
                
                # Productos destacados
                'top_products': top_products,
                
                # Filtros aplicados
                'applied_filters': {
                    'start_date': start_date,
                    'end_date': end_date,
                    'category': category,
                    'warehouse': warehouse
                }
            }
            
            print(f"✅ Dashboard data calculado exitosamente:")
            print(f"   📦 Total productos: {total_products}")
            print(f"   ⚠️ Stock crítico: {low_stock_products}")
            print(f"   💰 Valor total: {total_stock_value}")
            print(f"   📊 Gráficos: {len(products_by_category)} categorías, {len(stock_by_warehouse)} almacenes")
            
            return Response(dashboard_data)
            
        except Exception as e:
            print(f"❌ Error en dashboard: {str(e)}")
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error en dashboard view: {str(e)}")
            # En caso de error completo, devolver datos mínimos
            return Response({
                'total_products': 0,
                'total_categories': 0,
                'total_suppliers': 0,
                'total_stock_value': 0,
                'low_stock_products': 0,
                'out_of_stock_products': 0,
                'recent_transactions': 0,
                'active_alerts': 0,
                'top_products': [],
                'products_by_category': [],
                'stock_by_warehouse': [],
                'sales_trend': [],
                # Campos adicionales que el frontend espera
                'low_stock_alerts': 0,
                'total_value': 0,
                'total_transactions_today': 0,
                'active_customers': 0,
                'pipeline_value': 0,
                'period_info': {
                    'start_date': None,
                    'end_date': None,
                    'period_days': 30,
                    'transaction_change': 0,
                    'inventory_change': 0,
                    'timeframe': 'últimos 30 días'
                },
                'applied_filters': {
                    'start_date': None,
                    'end_date': None,
                    'category': None,
                    'warehouse': None
                },
                'error': f'Dashboard temporarily unavailable: {str(e)}'
            })


class InventoryDashboardView(APIView):
    """Vista para dashboard de inventario con datos corregidos"""
    
    def get(self, request):
        print(f"🔍 InventoryDashboardView.get() - Iniciando cálculo de estadísticas...")
        
        # NUEVO: Procesar filtros del frontend
        filters = {}
        category_filter = request.GET.get('category')
        warehouse_filter = request.GET.get('warehouse')
        status_filter = request.GET.get('status')
        search_filter = request.GET.get('search')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        print(f"🔍 Filtros recibidos: category={category_filter}, warehouse={warehouse_filter}, status={status_filter}, search={search_filter}, start_date={start_date}, end_date={end_date}")
        
        try:
            # FIX: Recalcular stocks agregados desde InventoryItem hacia Product
            self._update_product_stocks_from_inventory_items()
            
            # NUEVO: Construir queryset base de productos con filtros (SIN FECHA)
            products_queryset = Product.objects.filter(is_active=True)
            
            # Aplicar filtro de categoría
            if category_filter and category_filter != 'all':
                products_queryset = products_queryset.filter(category_id=category_filter)
                print(f"🔍 Aplicando filtro de categoría: {category_filter}")
            
            # Aplicar filtro de almacén (a través de InventoryItem)
            if warehouse_filter and warehouse_filter != 'all':
                # CORREGIDO: El warehouse_filter es el índice en la lista de almacenes únicos
                try:
                    # Obtener lista de almacenes únicos igual que en FilterOptionsView
                    unique_warehouses = list(Location.objects.filter(
                        is_active=True
                    ).values_list('warehouse', flat=True).distinct())
                    
                    # Convertir el índice a nombre de almacén
                    warehouse_index = int(warehouse_filter) - 1  # Convertir de 1-based a 0-based
                    if 0 <= warehouse_index < len(unique_warehouses):
                        warehouse_name = unique_warehouses[warehouse_index]
                        products_queryset = products_queryset.filter(inventory_items__location__warehouse=warehouse_name)
                        print(f"🔍 Aplicando filtro de almacén: {warehouse_name} (índice: {warehouse_filter})")
                    else:
                        print(f"❌ Índice de almacén fuera de rango: {warehouse_filter}")
                except (ValueError, IndexError) as e:
                    print(f"❌ Error procesando filtro de almacén {warehouse_filter}: {e}")
                    pass
            
            # Aplicar filtro de búsqueda
            if search_filter:
                products_queryset = products_queryset.filter(
                    Q(name__icontains=search_filter) |
                    Q(sku__icontains=search_filter) |
                    Q(description__icontains=search_filter)
                )
                print(f"🔍 Aplicando filtro de búsqueda: {search_filter}")
                
            # CORREGIDO: Aplicar filtro de estado al final para tener queryset completo
            if status_filter and status_filter != 'all':
                if status_filter == 'low_stock':
                    products_queryset = products_queryset.filter(stock__lt=F('min_stock'), stock__gt=0)
                elif status_filter == 'out_of_stock':
                    products_queryset = products_queryset.filter(stock__lte=0)
                elif status_filter == 'in_stock':
                    products_queryset = products_queryset.filter(stock__gt=0)
                print(f"🔍 Aplicando filtro de estado: {status_filter}")
            
            # Estadísticas básicas con filtros aplicados
            total_products = products_queryset.count()
            total_categories = Category.objects.filter(is_active=True).count()
            total_suppliers = Supplier.objects.filter(is_active=True).count()
            
            print(f"📊 Productos activos (filtrados): {total_products}")
            
            # NUEVO: Construir queryset de InventoryItem con filtros (SIN FECHA)
            inventory_items_queryset = InventoryItem.objects.filter(product__in=products_queryset)
            
            # Aplicar filtro de almacén a inventory items
            if warehouse_filter and warehouse_filter != 'all':
                try:
                    # CORREGIDO: Usar la misma lógica de índice que arriba
                    unique_warehouses = list(Location.objects.filter(
                        is_active=True
                    ).values_list('warehouse', flat=True).distinct())
                    
                    warehouse_index = int(warehouse_filter) - 1
                    if 0 <= warehouse_index < len(unique_warehouses):
                        warehouse_name = unique_warehouses[warehouse_index]
                        inventory_items_queryset = inventory_items_queryset.filter(location__warehouse=warehouse_name)
                        print(f"🔍 Aplicando filtro de almacén a inventory items: {warehouse_name}")
                    else:
                        print(f"❌ Índice de almacén fuera de rango para inventory items: {warehouse_filter}")
                except (ValueError, IndexError) as e:
                    print(f"❌ Error procesando filtro de almacén para inventory items {warehouse_filter}: {e}")
                    pass
                    print(f"❌ Almacén con ID {warehouse_filter} no encontrado para inventory items")
                    pass
            
            # FIX: Calcular valor total usando InventoryItem filtrado - CORREGIDO CON CAST
            total_stock_value = inventory_items_queryset.aggregate(
                total_value=Sum(
                    Case(
                        When(quantity__isnull=False,
                             then=F('quantity') * F('unit_cost')),
                        default=Value(0),
                        output_field=DecimalField(max_digits=15, decimal_places=2)
                    )
                )
            )['total_value'] or 0
            
            print(f"💰 Valor total de inventario (filtrado): {total_stock_value}")
            
            # FIX: Calcular stock crítico usando los stocks agregados en Product filtrado
            # Productos con stock por debajo del mínimo - USANDO QUERYSET FILTRADO
            low_stock_products = products_queryset.filter(
                stock__lt=F('min_stock'),
                stock__gt=0  # Excluir productos sin stock
            ).count()
            
            print(f"⚠️ Productos con stock crítico (filtrados): {low_stock_products}")
            
            # Productos completamente sin stock - USANDO QUERYSET FILTRADO
            out_of_stock_products = products_queryset.filter(
                stock__lte=0
            ).count()
            
            print(f"❌ Productos sin stock (filtrados): {out_of_stock_products}")
            
            # CORREGIDO: Transacciones con filtros de fecha SOLAMENTE
            transactions_queryset = Transaction.objects.all()
            
            # Aplicar filtros de fecha SOLO a transacciones
            if start_date:
                transactions_queryset = transactions_queryset.filter(transaction_date__gte=start_date)
                print(f"🔍 Aplicando filtro de fecha inicio a transacciones: {start_date}")
            if end_date:
                transactions_queryset = transactions_queryset.filter(transaction_date__lte=end_date)
                print(f"🔍 Aplicando filtro de fecha fin a transacciones: {end_date}")
            
            # CORREGIDO: Solo aplicar filtro de 7 días si no hay ningún filtro de fecha explícito
            # Si el usuario selecciona "all", no aplicar ningún filtro de fecha
            if not start_date and not end_date:
                # No aplicar filtro de fecha por defecto - mostrar todas las transacciones
                print("🔍 No hay filtros de fecha - mostrando todas las transacciones")
            
            # Aplicar filtros de productos a transacciones
            if category_filter and category_filter != 'all':
                transactions_queryset = transactions_queryset.filter(product__category_id=category_filter)
            if warehouse_filter and warehouse_filter != 'all':
                # CORREGIDO: Filtrar transacciones usando índice de almacén
                try:
                    unique_warehouses = list(Location.objects.filter(
                        is_active=True
                    ).values_list('warehouse', flat=True).distinct())
                    
                    warehouse_index = int(warehouse_filter) - 1
                    if 0 <= warehouse_index < len(unique_warehouses):
                        warehouse_name = unique_warehouses[warehouse_index]
                        transactions_queryset = transactions_queryset.filter(product__inventory_items__location__warehouse=warehouse_name)
                        print(f"🔍 Aplicando filtro de almacén a transacciones: {warehouse_name} (índice: {warehouse_filter})")
                    else:
                        print(f"❌ Índice de almacén fuera de rango para transacciones: {warehouse_filter}")
                except (ValueError, IndexError) as e:
                    print(f"❌ Error procesando filtro de almacén para transacciones {warehouse_filter}: {e}")
                    pass
            if search_filter:
                transactions_queryset = transactions_queryset.filter(
                    Q(product__name__icontains=search_filter) |
                    Q(product__sku__icontains=search_filter)
                )
            
            # Transacciones con filtros aplicados
            recent_transactions = transactions_queryset.count()
            print(f"📊 Transacciones recientes (filtradas): {recent_transactions}")
            
            # OPTIMIZADO: Calcular métricas de ventas y compras con filtros de fecha usando agregaciones
            sales_queryset = transactions_queryset.filter(transaction_type='sale')
            purchases_queryset = transactions_queryset.filter(transaction_type='purchase')
            
            # OPTIMIZADO: Calcular ventas usando agregación
            sales_aggregation = sales_queryset.aggregate(
                total_sales=Sum(
                    Case(
                        When(product__sale_price__isnull=False,
                             then=F('quantity') * F('product__sale_price')),  # Ventas como valores positivos
                        default=Value(0),
                        output_field=DecimalField(max_digits=15, decimal_places=2)
                    )
                ),
                count=Count('id')
            )
            
            sales_value = float(sales_aggregation['total_sales'] or 0)
            sales_count = sales_aggregation['count'] or 0
            
            # OPTIMIZADO: Calcular compras usando agregación  
            purchases_aggregation = purchases_queryset.aggregate(
                total_purchases=Sum(
                    Case(
                        When(product__cost_price__isnull=False,
                             then=F('quantity') * F('product__cost_price')),
                        default=Value(0),
                        output_field=DecimalField(max_digits=15, decimal_places=2)
                    )
                ),
                count=Count('id')
            )
            
            purchases_value = float(purchases_aggregation['total_purchases'] or 0)
            purchases_count = purchases_aggregation['count'] or 0
            
            # Calcular ganancia neta
            net_profit = sales_value - purchases_value
            
            print(f"💰 Ventas en período filtrado: {sales_count} transacciones, S/ {sales_value:.2f}")
            print(f"📦 Compras en período filtrado: {purchases_count} transacciones, S/ {purchases_value:.2f}")
            print(f"📈 Ganancia neta en período filtrado: S/ {net_profit:.2f}")
            print(f"🔍 Filtros aplicados a transacciones: start_date={start_date}, end_date={end_date}, category={category_filter}, warehouse={warehouse_filter}")
            
            # Top 5 productos por valor total - CORREGIDO CON CAST y filtrado
            try:
                top_products = list(products_queryset.annotate(
                    total_value=Case(
                        When(stock__isnull=False,
                             then=F('stock') * F('sale_price')),
                        default=Value(0),
                        output_field=DecimalField(max_digits=15, decimal_places=2)
                    )
                ).order_by('-total_value')[:5].values(
                    'id', 'name', 'sku', 'stock', 'total_value'
                ))
            except Exception as e:
                print(f"❌ Error obteniendo top productos: {e}")
                top_products = []
            
            # Stock por categoría - CORREGIDO CON CAST y filtrado
            try:
                categories_queryset = Category.objects.filter(is_active=True)
                if category_filter and category_filter != 'all':
                    categories_queryset = categories_queryset.filter(id=category_filter)
                
                stock_by_category = list(categories_queryset.annotate(
                    total_products=Count('products', filter=Q(products__is_active=True) & Q(products__in=products_queryset)),
                    total_stock=Sum('products__stock', filter=Q(products__is_active=True) & Q(products__in=products_queryset)),
                    total_value=Sum(
                        Case(
                            When(products__stock__isnull=False,
                                 then=F('products__stock') * F('products__sale_price')),
                            default=Value(0),
                            output_field=DecimalField(max_digits=15, decimal_places=2)
                        ),
                        filter=Q(products__is_active=True) & Q(products__in=products_queryset)
                    )
                ).values('name', 'total_products', 'total_stock', 'total_value'))
                print(f"📊 Stock por categoría (filtrado): {len(stock_by_category)} categorías")
            except Exception as e:
                print(f"❌ Error obteniendo stock por categoría: {e}")
                stock_by_category = []
            
            # NUEVO: Calcular ventas por fecha para el gráfico
            try:
                # Obtener ventas agrupadas por fecha
                sales_by_date = sales_queryset.annotate(
                    date=TruncDate('transaction_date')
                ).values('date').annotate(
                    total_sales=Sum(
                        Case(
                            When(product__sale_price__isnull=False,
                                 then=F('quantity') * F('product__sale_price') * -1),  # Convertir a positivo
                            default=Value(0),
                            output_field=DecimalField(max_digits=15, decimal_places=2)
                        )
                    ),
                    count=Count('id')
                ).order_by('date')
                
                sales_trend_data = []
                for sale in sales_by_date:
                    sales_trend_data.append({
                        'date': sale['date'].strftime('%Y-%m-%d') if sale['date'] else '',
                        'sales': float(sale['total_sales'] or 0),
                        'count': sale['count'] or 0
                    })
                
                print(f"📊 Tendencia de ventas por fecha: {len(sales_trend_data)} días con datos")
                
            except Exception as e:
                print(f"❌ Error calculando tendencia de ventas: {e}")
                sales_trend_data = []

            # NUEVO: Stock por almacén para el gráfico
            try:
                # Obtener almacenes únicos filtrados
                warehouses_queryset = Location.objects.filter(is_active=True)
                if warehouse_filter and warehouse_filter != 'all':
                    try:
                        # CORREGIDO: Usar índice de almacén
                        unique_warehouses = list(Location.objects.filter(
                            is_active=True
                        ).values_list('warehouse', flat=True).distinct())
                        
                        warehouse_index = int(warehouse_filter) - 1
                        if 0 <= warehouse_index < len(unique_warehouses):
                            warehouse_name = unique_warehouses[warehouse_index]
                            warehouses_queryset = warehouses_queryset.filter(warehouse=warehouse_name)
                        else:
                            print(f"❌ Índice de almacén fuera de rango para stock por almacén: {warehouse_filter}")
                    except (ValueError, IndexError) as e:
                        print(f"❌ Error procesando filtro de almacén para stock por almacén {warehouse_filter}: {e}")
                        pass
                
                stock_by_warehouse = []
                seen_warehouses = set()
                
                for location in warehouses_queryset:
                    if location.warehouse not in seen_warehouses:
                        # Calcular stock total para este almacén
                        warehouse_stock = InventoryItem.objects.filter(
                            location__warehouse=location.warehouse,
                            location__is_active=True,
                            product__is_active=True
                        ).aggregate(
                            total_stock=Sum('quantity'),
                            min_stock=Sum('product__min_stock'),
                            max_stock=Sum('product__max_stock')
                        )
                        
                        stock_by_warehouse.append({
                            'warehouse': location.warehouse,
                            'current_stock': float(warehouse_stock['total_stock'] or 0),
                            'min_stock': float(warehouse_stock['min_stock'] or 0),
                            'max_stock': float(warehouse_stock['max_stock'] or 0)
                        })
                        seen_warehouses.add(location.warehouse)
                
                print(f"🏢 Stock por almacén (filtrado): {len(stock_by_warehouse)} almacenes")
            except Exception as e:
                print(f"❌ Error obteniendo stock por almacén: {e}")
                stock_by_warehouse = []
            
            dashboard_data = {
                'total_products': total_products,
                'total_categories': total_categories,
                'total_suppliers': total_suppliers,
                'total_stock_value': float(total_stock_value),
                'low_stock_products': low_stock_products,  # FIX: Este es el campo que el frontend necesita
                'out_of_stock_products': out_of_stock_products,
                'recent_transactions': recent_transactions,
                'active_alerts': 0,  # Placeholder
                'top_products': top_products,
                'stock_by_category': stock_by_category,
                'stock_by_warehouse': stock_by_warehouse,
                'products_by_category': stock_by_category,  # Alias para compatibilidad con frontend
                'recent_sales': [],
                
                # NUEVO: Métricas de ventas y compras que cambian con fecha
                'sales_value': float(sales_value),
                'sales_count': sales_count,
                'purchases_value': float(purchases_value),
                'purchases_count': purchases_count,
                'net_profit': float(net_profit),
                'sales_trend_data': sales_trend_data,
                
                # Campos adicionales que el frontend puede esperar
                'total_value': float(total_stock_value),
                'low_stock_alerts': low_stock_products,
                'total_transactions_today': recent_transactions,
                'active_customers': 0,
                'pipeline_value': 0,
                
                # Información de filtros aplicados
                'filters_applied': {
                    'category': category_filter,
                    'warehouse': warehouse_filter, 
                    'status': status_filter,
                    'search': search_filter,
                    'start_date': start_date,
                    'end_date': end_date
                }
            }
            
            print(f"✅ Dashboard data generado con {total_products} productos filtrados")
            print(f"📊 Resumen: {low_stock_products} productos con stock crítico, {out_of_stock_products} sin stock")
            
            return Response(dashboard_data)
            
        except Exception as e:
            print(f"❌ Error en InventoryDashboardView: {str(e)}")
            import traceback
            print(f"🔍 Traceback: {traceback.format_exc()}")
            return Response({
                'error': 'Internal server error',
                'message': str(e)
            }, status=500)
    
    def _update_product_stocks_from_inventory_items(self):
        """Actualizar stocks agregados en Product desde InventoryItem"""
        try:
            print("🔄 Actualizando stocks agregados desde InventoryItem...")
            
            # Agrupar por producto y sumar quantities
            stock_totals = InventoryItem.objects.values('product').annotate(
                total_stock=Sum('quantity')
            )
            
            updated_count = 0
            for item in stock_totals:
                product_id = item['product']
                total_stock = item['total_stock'] or 0
                
                # Actualizar el stock en Product
                Product.objects.filter(id=product_id).update(stock=total_stock)
                updated_count += 1
            
            print(f"✅ {updated_count} productos actualizados con stocks agregados")
            return updated_count
            
        except Exception as e:
            print(f"❌ Error actualizando stocks: {e}")
            return 0
    
    def _get_updated_products_count(self):
        """Obtener conteo de productos actualizados recientemente"""
        try:
            return Product.objects.filter(
                updated_at__gte=timezone.now() - timedelta(minutes=5)
            ).count()
        except:
            return 0


class FileUploadView(APIView):
    """Vista para subir archivos CSV de inventario"""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request):
        # Implementación básica para subida de archivos
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response(
                {'error': 'No file provided'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Aquí se implementaría la lógica de procesamiento del CSV
        # Por ahora, retornamos un mensaje de éxito
        return Response({
            'message': 'File uploaded successfully',
            'filename': file_obj.name,
            'size': file_obj.size
        })


class LowStockView(APIView):
    """Vista para obtener productos con stock bajo"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Obtener productos con stock bajo",
        description="Retorna productos que están por debajo del stock mínimo"
    )
    def get(self, request):
        low_stock_products = Product.objects.filter(
            is_active=True,
            stock__lte=F('min_stock')
        ).select_related('category', 'supplier')
        
        serializer = ProductSerializer(low_stock_products, many=True)
        return Response({
            'count': low_stock_products.count(),
            'results': serializer.data
        })


class StockMovementsView(APIView):
    """Vista para obtener movimientos de stock"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Obtener movimientos de stock",
        description="Retorna el historial de movimientos de stock con paginación"
    )
    def get(self, request):
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
        
        queryset = InventoryHistory.objects.select_related('product', 'user').order_by('-date_changed')
        
        start = (page - 1) * page_size
        end = start + page_size
        
        movements = queryset[start:end]
        total_count = queryset.count()
        
        movements_data = []
        for movement in movements:
            movements_data.append({
                'id': movement.id,
                'product_name': movement.product.name,
                'product_sku': movement.product.sku,
                'stock_before': movement.stock_before,
                'stock_after': movement.stock_after,
                'change_reason': movement.change_reason,
                'date_changed': movement.date_changed,
                'user': movement.user.username if movement.user else None
            })
        
        return Response({
            'count': total_count,
            'page': page,
            'page_size': page_size,
            'results': movements_data
        })


class LocationViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de ubicaciones"""
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        try:
            return Location.objects.filter(is_active=True).order_by('warehouse', 'zone', 'aisle')
        except Exception as e:
            print(f"Error in LocationViewSet.get_queryset: {e}")
            return Location.objects.none()
    
    def list(self, request, *args, **kwargs):
        """Override del método list para manejo robusto de errores"""
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return Response({
                'count': queryset.count(),
                'results': serializer.data
            })
        except Exception as e:
            return Response({
                'count': 0,
                'results': [],
                'error': f'Locations service temporarily unavailable: {str(e)}'
            })


class InventoryItemViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de items de inventario"""
    queryset = InventoryItem.objects.all()
    serializer_class = InventoryItemSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        try:
            return InventoryItem.objects.filter(is_active=True).select_related(
                'product', 'location'
            ).order_by('-created_at')
        except Exception as e:
            print(f"Error in InventoryItemViewSet.get_queryset: {e}")
            return InventoryItem.objects.none()
    
    def list(self, request, *args, **kwargs):
        """Override del método list para manejo robusto de errores"""
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return Response({
                'count': queryset.count(),
                'results': serializer.data
            })
        except Exception as e:
            return Response({
                'count': 0,
                'results': [],
                'error': f'Inventory items service temporarily unavailable: {str(e)}'
            })
    
    @action(detail=False, methods=['get'])
    def by_location(self, request):
        """Obtener items por ubicación"""
        location_id = request.query_params.get('location_id')
        if not location_id:
            return Response({'error': 'location_id parameter is required'}, status=400)
        
        items = self.get_queryset().filter(location_id=location_id)
        serializer = self.get_serializer(items, many=True)
        return Response({
            'count': items.count(),
            'results': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def by_product(self, request):
        """Obtener items por producto"""
        product_id = request.query_params.get('product_id')
        if not product_id:
            return Response({'error': 'product_id parameter is required'}, status=400)
        
        items = self.get_queryset().filter(product_id=product_id)
        serializer = self.get_serializer(items, many=True)
        return Response({
            'count': items.count(),
            'results': serializer.data
        })


class CustomerViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de clientes"""
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        try:
            return Customer.objects.filter(is_active=True).order_by('name')
        except Exception as e:
            print(f"Error in CustomerViewSet.get_queryset: {e}")
            return Customer.objects.none()
    
    def list(self, request, *args, **kwargs):
        """Override del método list para manejo robusto de errores"""
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return Response({
                'count': queryset.count(),
                'results': serializer.data
            })
        except Exception as e:
            return Response({
                'count': 0,
                'results': [],
                'error': f'Customers service temporarily unavailable: {str(e)}'
            })


class LeadViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de leads"""
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        try:
            return Lead.objects.select_related('assigned_to').prefetch_related('interested_products').order_by('-created_at')
        except Exception as e:
            print(f"Error in LeadViewSet.get_queryset: {e}")
            return Lead.objects.none()
    
    def list(self, request, *args, **kwargs):
        """Override del método list para manejo robusto de errores"""
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return Response({
                'count': queryset.count(),
                'results': serializer.data
            })
        except Exception as e:
            return Response({
                'count': 0,
                'results': [],
                'error': f'Leads service temporarily unavailable: {str(e)}'
            })
    
    def perform_create(self, serializer):
        # Asignar el usuario actual como responsable si no se especifica otro
        if not serializer.validated_data.get('assigned_to'):
            serializer.validated_data['assigned_to'] = self.request.user
        serializer.save()
    
    @action(detail=False, methods=['get'])
    def by_status(self, request):
        """Obtener leads por estado"""
        status_filter = request.query_params.get('status')
        if not status_filter:
            return Response({'error': 'status parameter is required'}, status=400)
        
        leads = self.get_queryset().filter(status=status_filter)
        serializer = self.get_serializer(leads, many=True)
        return Response({
            'count': leads.count(),
            'results': serializer.data
        })


class OpportunityViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de oportunidades (basado en Lead)"""
    queryset = Lead.objects.all()
    serializer_class = OpportunitySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        try:
            # Filtrar leads que son oportunidades (con valor estimado > 0)
            return Lead.objects.filter(
                estimated_value__gt=0
            ).select_related('assigned_to').order_by('-estimated_value')
        except Exception as e:
            print(f"Error in OpportunityViewSet.get_queryset: {e}")
            return Lead.objects.none()
    
    def list(self, request, *args, **kwargs):
        """Override del método list para manejo robusto de errores"""
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return Response({
                'count': queryset.count(),
                'results': serializer.data
            })
        except Exception as e:
            return Response({
                'count': 0,
                'results': [],
                'error': f'Opportunities service temporarily unavailable: {str(e)}'
            })
    
    @action(detail=False, methods=['get'])
    def by_stage(self, request):
        """Obtener oportunidades por etapa"""
        stage = request.query_params.get('stage')
        if not stage:
            return Response({'error': 'stage parameter is required'}, status=400)
        
        opportunities = self.get_queryset().filter(status=stage)
        serializer = self.get_serializer(opportunities, many=True)
        return Response({
            'count': opportunities.count(),
            'results': serializer.data
        })


class FilterOptionsView(APIView):
    """Vista para obtener opciones de filtros del dashboard"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Obtener opciones de filtros",
        description="Retorna las opciones disponibles para los filtros del dashboard (categorías, almacenes, estados)"
    )
    def get(self, request):
        try:
            # Obtener la empresa del usuario
            company = get_company_for_user(request.user)
            
            # Obtener almacenes únicos desde las ubicaciones
            unique_warehouses = Location.objects.filter(
                is_active=True
            ).values_list('warehouse', flat=True).distinct()
            
            warehouses_list = []
            for i, warehouse in enumerate(unique_warehouses):
                if warehouse:  # Solo incluir almacenes que no estén vacíos
                    warehouses_list.append({
                        'id': str(i + 1),  # ID numérico para el frontend
                        'name': warehouse
                    })
            
            # Construir las opciones de filtros
            options = {
                'categories': list(Category.objects.filter(is_active=True).values('id', 'name')),
                'suppliers': list(Supplier.objects.filter(is_active=True).values('id', 'name')),
                'locations': list(Location.objects.filter(is_active=True).values('id', 'name', 'warehouse')),
                'warehouses': warehouses_list,  # NUEVO: Lista de almacenes únicos
                'statuses': [  # CORREGIDO: Cambiar de stock_statuses a statuses
                    {'id': 'critical', 'name': 'Stock Crítico'},
                    {'id': 'low', 'name': 'Stock Bajo'},
                    {'id': 'normal', 'name': 'Stock Normal'},
                    {'id': 'high', 'name': 'Stock Alto'},
                    {'id': 'low_stock', 'name': 'Stock Bajo'},  # Alias para compatibilidad
                    {'id': 'out_of_stock', 'name': 'Sin Stock'},
                    {'id': 'in_stock', 'name': 'En Stock'},
                ],
                'transaction_types': [
                    {'id': 'sale', 'name': 'Venta'},
                    {'id': 'purchase', 'name': 'Compra'},
                    {'id': 'adjustment', 'name': 'Ajuste'},
                    {'id': 'transfer', 'name': 'Transferencia'},
                ],
            }
            
            print(f"📋 FilterOptions: Devolviendo {len(options['categories'])} categorías, {len(options['warehouses'])} almacenes")
            return Response(options)
            
        except Exception as e:
            return Response({
                'error': f'Error al obtener opciones de filtros: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProductIntelligenceView(APIView):
    """Vista para obtener datos de inteligencia artificial para productos"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Obtener datos de inteligencia artificial para productos",
        description="Retorna recomendaciones de IA, tendencias, y estadísticas avanzadas por producto"
    )
    def get(self, request):
        try:
            company = get_company_for_user(request.user)
            product_id = request.GET.get('product_id')
            
            # Si se especifica un producto específico
            if product_id:
                try:
                    product = Product.objects.get(id=product_id, company=company)
                    intelligence_data = self._get_product_intelligence_safe(product)
                    return Response(intelligence_data)
                except Product.DoesNotExist:
                    return Response({'error': 'Producto no encontrado'}, status=404)
            
            # Obtener datos de inteligencia para todos los productos
            products = Product.objects.filter(company=company, is_active=True)
            intelligence_data = {}
            
            for product in products:
                try:
                    intelligence_data[product.id] = self._get_product_intelligence_safe(product)
                except Exception as e:
                    # Si hay error con un producto específico, usar datos básicos
                    intelligence_data[product.id] = {
                        'product_id': product.id,
                        'product_name': product.name,
                        'current_stock': product.stock or 0,
                        'status': 'limited_data',
                        'error': str(e)
                    }
            
            return Response(intelligence_data)
            
        except Exception as e:
            return Response({
                'error': f'Error al obtener datos de inteligencia: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_product_intelligence_safe(self, product):
        """Versión segura del método de inteligencia con mejor manejo de errores"""
        try:
            now = timezone.now()
            last_30_days = now - timedelta(days=30)
            last_7_days = now - timedelta(days=7)
            
            # Obtener transacciones recientes de forma segura
            try:
                recent_transactions = Transaction.objects.filter(
                    product=product,
                    transaction_type='sale',
                    transaction_date__gte=last_30_days
                ).aggregate(
                    total_sold=Sum('quantity') or 0,
                    avg_daily_sales=Avg('quantity') or 0,
                    transaction_count=Count('id') or 0
                )
                
                last_week_transactions = Transaction.objects.filter(
                    product=product,
                    transaction_type='sale',
                    transaction_date__gte=last_7_days
                ).aggregate(
                    last_week_sales=Sum('quantity') or 0
                )
            except Exception:
                # Si falla la consulta de transacciones, usar valores por defecto
                recent_transactions = {'total_sold': 0, 'avg_daily_sales': 0, 'transaction_count': 0}
                last_week_transactions = {'last_week_sales': 0}
            
            # Calcular métricas básicas
            current_stock = product.stock or 0
            min_stock = product.min_stock or 0
            max_stock = product.max_stock or 100
            daily_sales = recent_transactions['avg_daily_sales'] or 0
            
            # Calcular días de stock
            days_of_stock = None
            if daily_sales > 0:
                days_of_stock = current_stock / daily_sales
            
            # Determinar estado del stock
            stock_status = 'normal'
            if current_stock <= 0:
                stock_status = 'out_of_stock'
            elif current_stock <= min_stock:
                stock_status = 'low_stock'
            elif current_stock >= max_stock:
                stock_status = 'overstocked'
            
            # Calcular tendencia básica
            trend = 'stable'
            weekly_avg = daily_sales * 7
            if last_week_transactions['last_week_sales'] > weekly_avg * 1.2:
                trend = 'increasing'
            elif last_week_transactions['last_week_sales'] < weekly_avg * 0.8:
                trend = 'decreasing'
            
            # Recomendación de reorden
            needs_reorder = current_stock <= min_stock and trend in ['stable', 'increasing']
            suggested_quantity = 0
            if needs_reorder:
                suggested_quantity = max(min_stock - current_stock + int(daily_sales * 7), 0)
            
            return {
                'product_id': product.id,
                'product_name': product.name,
                'current_stock': current_stock,
                'min_stock': min_stock,
                'max_stock': max_stock,
                'stock_status': stock_status,
                'days_of_stock': round(days_of_stock, 1) if days_of_stock else None,
                'sales_data': {
                    'last_30_days': recent_transactions['total_sold'],
                    'last_7_days': last_week_transactions['last_week_sales'],
                    'avg_daily_sales': round(daily_sales, 2),
                    'transaction_count': recent_transactions['transaction_count']
                },
                'recommendations': {
                    'needs_reorder': needs_reorder,
                    'suggested_order_quantity': suggested_quantity,
                    'trend': trend,
                    'priority': 'high' if stock_status == 'out_of_stock' else 'medium' if stock_status == 'low_stock' else 'low'
                },
                'intelligence_summary': self._get_stock_level_text_safe(current_stock, days_of_stock),
                'ai_insights': [
                    f"Producto con {current_stock} unidades en stock",
                    f"Tendencia de ventas: {trend}",
                    f"Estado: {stock_status.replace('_', ' ').title()}",
                    f"Días de stock estimados: {round(days_of_stock, 1) if days_of_stock else 'N/A'}"
                ]
            }
            
        except Exception as e:
            # Fallback a datos muy básicos si todo falla
            return {
                'product_id': product.id,
                'product_name': product.name,
                'current_stock': product.stock or 0,
                'status': 'error',
                'error': str(e),
                'ai_insights': [f"Error al procesar datos para {product.name}"]
            }
    
    def _get_stock_level_text_safe(self, current_stock, days_of_stock):
        """Versión segura del texto de nivel de stock"""
        try:
            if days_of_stock is None:
                return f"{current_stock} unidades"
            
            if days_of_stock < 1:
                return f"{current_stock} unidades (menos de 1 día)"
            elif days_of_stock < 7:
                return f"{current_stock} unidades (bueno para {int(days_of_stock)} días)"
            elif days_of_stock < 30:
                return f"{current_stock} unidades (bueno para {int(days_of_stock)} días)"
            else:
                return f"{current_stock} unidades (stock abundante)"
        except Exception:
            return f"{current_stock} unidades"


class ProductSmartFiltersView(APIView):
    """Vista para obtener productos con filtros inteligentes"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Obtener productos con filtros inteligentes",
        description="Retorna productos filtrados por criterios inteligentes como 'necesita reabastecimiento', 'próximos a vencer', etc."
    )
    def get(self, request):
        try:
            company = get_company_for_user(request.user)
            filter_type = request.GET.get('filter_type', 'all')
            
            # Base queryset
            queryset = Product.objects.filter(company=company, is_active=True)
            
            # Aplicar filtros inteligentes
            if filter_type == 'needs_restock':
                # Productos que necesitan reabastecimiento
                queryset = queryset.filter(
                    Q(stock__lte=F('min_stock')) |
                    Q(id__in=ReorderRecommendation.objects.filter(
                        status='pending',
                        priority__in=['high', 'urgent']
                    ).values_list('product_id', flat=True))
                )
            
            elif filter_type == 'expiring_soon':
                # Productos próximos a vencer (con fecha de vencimiento)
                expiring_date = timezone.now().date() + timedelta(days=30)
                queryset = queryset.filter(
                    has_expiration=True,
                    inventory_items__expiration_date__lte=expiring_date
                ).distinct()
            
            elif filter_type == 'top_sellers':
                # Productos más vendidos en las últimas 2 semanas
                two_weeks_ago = timezone.now() - timedelta(days=14)
                top_products = Sale.objects.filter(
                    date_sold__gte=two_weeks_ago
                ).values('product_id').annotate(
                    total_sold=Sum('quantity')
                ).order_by('-total_sold')[:20]
                
                product_ids = [item['product_id'] for item in top_products]
                queryset = queryset.filter(id__in=product_ids)
            
            elif filter_type == 'low_stock':
                # Stock bajo
                queryset = queryset.filter(stock__lte=F('min_stock'))
            
            elif filter_type == 'critical_stock':
                # Stock crítico (0 o negativo)
                queryset = queryset.filter(stock__lte=0)
            
            elif filter_type == 'trending_up':
                # Productos con tendencia al alza
                # Esto requiere cálculos más complejos, por simplicidad filtraremos por ventas recientes
                last_week = timezone.now() - timedelta(days=7)
                trending_products = Sale.objects.filter(
                    date_sold__gte=last_week
                ).values('product_id').annotate(
                    total_sold=Sum('quantity')
                ).filter(total_sold__gt=0)
                
                product_ids = [item['product_id'] for item in trending_products]
                queryset = queryset.filter(id__in=product_ids)
            
            # Obtener productos con información adicional
            products = queryset.select_related('category', 'supplier').prefetch_related('sales')
            
            # Serializar productos
            serializer = ProductSerializer(products, many=True)
            
            return Response({
                'filter_type': filter_type,
                'count': products.count(),
                'results': serializer.data
            })
            
        except Exception as e:
            return Response({
                'error': f'Error al filtrar productos: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProductActionView(APIView):
    """Vista para ejecutar acciones inteligentes en productos"""
    permission_classes = [IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        print("🔧 ProductActionView.__init__ - INICIANDO")
        super().__init__(*args, **kwargs)
        print("🔧 ProductActionView.__init__ - super() completado")
        
        # **DIAGNÓSTICO: Inicialización con logging detallado**
        try:
            print("🔧 Configurando OpenAI...")
            # Configurar OpenAI solo si está disponible
            if hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY:
                import openai
                openai.api_key = settings.OPENAI_API_KEY
                print("✅ OpenAI configurado exitosamente")
            else:
                print("⚠️ OpenAI API key no encontrada")
            
            print("🔧 Inicializando NotificationService...")
            # Inicializar NotificationService de forma segura
            try:
                self.notification_service = NotificationService()
                print("✅ NotificationService inicializado exitosamente")
            except Exception as e:
                print(f"⚠️ Warning: NotificationService no disponible: {e}")
                self.notification_service = None
                
        except Exception as e:
            print(f"❌ Error en inicialización de ProductActionView: {e}")
            import traceback
            traceback.print_exc()
            self.notification_service = None
            
        print("🔧 ProductActionView.__init__ - COMPLETADO")
    
    @extend_schema(
        summary="Ejecutar acciones inteligentes en productos",
        description="Ejecuta acciones como generar orden de compra, obtener pronóstico, etc."
    )
    def post(self, request):
        print("🚀 ProductActionView.post - MÉTODO LLAMADO!")
        print(f"📍 Request method: {request.method}")
        print(f"📍 Request path: {request.path}")
        print(f"📍 Request user: {request.user}")
        print(f"📍 Request authenticated: {request.user.is_authenticated}")
        
        try:
            print(f"📥 ProductActionView.post called with data: {request.data}")
            print(f"📥 Request headers: {dict(request.headers)}")
            
            product_id = request.data.get('product_id')
            action = request.data.get('action')
            additional_data = request.data.get('data', {})
            
            print(f"🔍 Processing: product_id={product_id}, action={action}, data={additional_data}")
            
            if not product_id or not action:
                print("❌ Missing required fields")
                return Response({
                    'error': 'Se requiere product_id y action'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            print("🔍 Getting company for user...")
            company = get_company_for_user(request.user)
            print(f"🏢 Company: {company}")
            
            print(f"🔍 Looking for product with ID: {product_id}")
            try:
                product = Product.objects.get(id=product_id, company=company)
                print(f"📦 Product found: {product.name}")
            except Product.DoesNotExist:
                print(f"❌ Product not found: {product_id}")
                return Response({'error': 'Producto no encontrado'}, status=404)
            
            print(f"🎯 Executing action: {action}")
            
            # Mantener funcionalidades completas originales
            if action == 'generate_purchase_order':
                print("🛒 Calling _generate_ai_purchase_order...")
                result = self._generate_ai_purchase_order(product, additional_data, request.user)
                print("✅ _generate_ai_purchase_order completed")
            elif action == 'get_forecast':
                print("📊 Calling _get_ml_forecast_with_ai_insights...")
                result = self._get_ml_forecast_with_ai_insights(product)
                print("✅ _get_ml_forecast_with_ai_insights completed")
            elif action == 'update_stock_alert':
                print("⚠️ Calling _update_stock_alert...")
                result = self._update_stock_alert(product, additional_data)
                print("✅ _update_stock_alert completed")
            elif action == 'send_purchase_email':
                print("📧 Calling _send_purchase_order_email...")
                result = self._send_purchase_order_email(product, additional_data, request.user)
                print("✅ _send_purchase_order_email completed")
            else:
                print(f"❌ Invalid action: {action}")
                return Response({'error': 'Acción no válida'}, status=400)
            
            print(f"✅ Action '{action}' completed successfully")
            print(f"📤 Returning result: {result}")
            return Response(result)
            
        except Exception as e:
            print(f"❌ EXCEPTION in ProductActionView.post: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response({
                'error': f'Error al ejecutar acción: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _generate_ai_purchase_order(self, product, data, user):
        """Generar orden de compra con IA y recomendaciones personalizables"""
        print(f"🛒 BACKEND: _generate_ai_purchase_order INICIADO")
        print(f"🛒 BACKEND: Product: {product.name} (ID: {product.id})")
        print(f"🛒 BACKEND: Data recibida: {data}")
        print(f"🛒 BACKEND: User: {user}")
        
        # Obtener datos base para la recomendación
        print("🛒 BACKEND: Buscando ReorderRecommendation...")
        reorder_rec = ReorderRecommendation.objects.filter(
            product=product,
            status='pending'
        ).first()
        print(f"🛒 BACKEND: ReorderRecommendation encontrada: {reorder_rec}")
        
        # Calcular cantidad recomendada base
        if reorder_rec:
            base_quantity = float(reorder_rec.recommended_quantity)
            estimated_cost = float(reorder_rec.estimated_cost)
            print(f"🛒 BACKEND: Usando ReorderRecommendation - quantity: {base_quantity}, cost: {estimated_cost}")
        else:
            print("🛒 BACKEND: No hay ReorderRecommendation, calculando automáticamente...")
            # Cálculo inteligente basado en histórico y stock
            base_quantity = max(
                float(product.min_stock * 2), 
                float(product.reorder_point),
                self._calculate_smart_quantity(product)
            )
            estimated_cost = base_quantity * float(product.cost_price)
            print(f"🛒 BACKEND: Cantidad calculada: {base_quantity}, costo estimado: {estimated_cost}")
        
        # Obtener insights con OpenAI si está disponible
        ai_recommendation = self._get_openai_purchase_recommendation(product, base_quantity)
        
        # Permitir override manual de cantidad
        final_quantity = data.get('custom_quantity', base_quantity)
        final_cost = final_quantity * float(product.cost_price)
        
        result = {
            'action': 'generate_purchase_order',
            'product_id': product.id,
            'product_name': product.name,
            'supplier': {
                'name': product.supplier.name if product.supplier else 'Sin proveedor asignado',
                'email': getattr(product.supplier, 'email', None) if product.supplier else None,
                'phone': getattr(product.supplier, 'phone', None) if product.supplier else None,
            },
            'recommendation': {
                'ai_suggested_quantity': base_quantity,
                'user_selected_quantity': final_quantity,
                'estimated_cost': final_cost,
                'unit_cost': float(product.cost_price),
                'ai_insights': ai_recommendation.get('insights', ''),
                'priority_level': ai_recommendation.get('priority', 'medium'),
                'justification': ai_recommendation.get('justification', '')
            },
            'current_stock': product.stock,
            'reorder_point': product.reorder_point,
            'min_stock': product.min_stock,
            'suggested_delivery_date': (timezone.now().date() + timedelta(days=7)).isoformat(),
            'can_send_email': bool(product.supplier and hasattr(product.supplier, 'email') and product.supplier.email),
            'email_options': {
                'whatsapp_available': False,  # En standby como solicitaste
                'email_available': True
            }
        }
        
        print(f"🛒 BACKEND: _generate_ai_purchase_order COMPLETADO")
        print(f"🛒 BACKEND: Result generado: {result}")
        return result
    
    def _get_ml_forecast_with_ai_insights(self, product):
        """Obtener pronósticos ML con insights de IA"""
        
        # Obtener pronósticos de los modelos ML
        forecasts = DemandForecast.objects.filter(
            product=product,
            forecast_date__gte=timezone.now().date()
        ).order_by('forecast_date')[:30]
        
        forecast_data = []
        total_demand = 0
        
        for forecast in forecasts:
            forecast_item = {
                'date': forecast.forecast_date.isoformat(),
                'predicted_demand': float(forecast.predicted_demand),
                'lower_bound': float(forecast.lower_bound),
                'upper_bound': float(forecast.upper_bound),
                'confidence_level': float(forecast.confidence_level),
                'model_type': forecast.model.model_type if forecast.model else 'unknown'
            }
            forecast_data.append(forecast_item)
            total_demand += forecast_item['predicted_demand']
        
        # Obtener insights de IA sobre los pronósticos
        ai_insights = self._get_openai_forecast_insights(product, forecast_data)
        
        # Obtener modelos ML disponibles y sus métricas
        available_models = self._get_available_ml_models(product)
        
        # Recomendaciones de nuevos modelos a implementar
        model_recommendations = self._get_model_recommendations()
        
        forecast_summary = {
            'total_forecasted_demand': total_demand,
            'avg_daily_demand': total_demand / len(forecast_data) if forecast_data else 0,
            'forecast_horizon_days': len(forecast_data),
            'confidence_avg': sum(f['confidence_level'] for f in forecast_data) / len(forecast_data) if forecast_data else 0
        }
        
        return {
            'action': 'get_forecast',
            'product_id': product.id,
            'product_name': product.name,
            'forecast_data': forecast_data,
            'forecast_summary': forecast_summary,
            'ai_insights': ai_insights,
            'ml_models': {
                'active_models': available_models,
                'model_recommendations': model_recommendations,
                'model_performance': self._get_model_performance_summary(product)
            }
        }
    
    def _send_purchase_order_email(self, product, data, user):
        """Enviar email de orden de compra usando el sistema de alertas"""
        
        try:
            quantity = data.get('quantity', 0)
            if not quantity:
                return {'error': 'Cantidad requerida para enviar email'}
            
            # Generar email con OpenAI
            email_content = self._generate_purchase_order_email_with_ai(product, quantity, user)
            
            # Crear una alerta temporal para usar el sistema de notificaciones
            alert = Alert.objects.create(
                title=f"Orden de Compra - {product.name}",
                message=email_content.get('message', ''),
                severity='medium',
                status='pending',
                product=product,
                company=product.company,
                current_value=quantity,
                threshold_value=product.min_stock
            )
            
            # **✅ CORREGIDO: Verificar email personalizado del frontend PRIMERO**
            custom_email = data.get('email_to')
            
            if custom_email:
                # **PRIORIDAD 1: Usar email personalizado del usuario**
                print(f"📧 Enviando a email personalizado: {custom_email}")
                result = self._send_email_to_custom(custom_email, email_content, product, quantity)
            elif product.supplier and hasattr(product.supplier, 'email') and product.supplier.email:
                # **PRIORIDAD 2: Enviar al proveedor**
                print(f"📧 Enviando a proveedor: {product.supplier.email}")
                result = self._send_email_to_supplier(product.supplier.email, email_content, product, quantity)
            else:
                # **PRIORIDAD 3: Enviar al usuario solicitante**
                print(f"📧 Enviando a usuario: {user.email}")
                result = self._send_email_to_user(user.email, email_content, product, quantity)
            
            # Limpiar alerta temporal
            alert.delete()
            
            return {
                'action': 'send_purchase_email',
                'success': result.get('status') == 'success',
                'message': result.get('message', ''),
                'email_sent_to': result.get('recipient', ''),
                'email_subject': email_content.get('subject', ''),
                'ai_generated': True
            }
            
        except Exception as e:
            return {'error': f'Error enviando email: {str(e)}'}
    
    def _calculate_smart_quantity(self, product):
        """Calcular cantidad inteligente basada en historial"""
        try:
            # Obtener transacciones recientes (últimos 30 días)
            recent_transactions = Transaction.objects.filter(
                product=product,
                transaction_date__gte=timezone.now().date() - timedelta(days=30),
                transaction_type='sale'
            )
            
            total_sold = sum(t.quantity for t in recent_transactions)
            daily_avg = total_sold / 30 if total_sold > 0 else 1
            
            # Calcular para 2 semanas de stock
            return max(daily_avg * 14, float(product.min_stock))
            
        except:
            return float(product.min_stock * 2)
    
    def _get_openai_purchase_recommendation(self, product, base_quantity):
        """Obtener recomendación de compra usando OpenAI"""
        
        if not hasattr(settings, 'OPENAI_API_KEY') or not settings.OPENAI_API_KEY:
            return {
                'insights': 'Recomendación automática basada en datos históricos',
                'priority': 'medium',
                'justification': f'Cantidad calculada automáticamente: {base_quantity} unidades'
            }
        
        try:
            # Obtener contexto del producto
            context = self._build_product_context(product)
            
            prompt = f"""
            Eres un experto en gestión de inventarios. Analiza la siguiente información del producto y da una recomendación de compra:
            
            Producto: {product.name}
            Stock actual: {product.stock}
            Stock mínimo: {product.min_stock}
            Punto de reorden: {product.reorder_point}
            Cantidad sugerida: {base_quantity}
            Contexto adicional: {context}
            
            Proporciona:
            1. Una justificación clara de por qué esta cantidad es recomendable
            2. El nivel de prioridad (low, medium, high, urgent)
            3. Insights adicionales para optimizar el inventario
            
            Responde en formato JSON con keys: insights, priority, justification
            """
            
            import openai
            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.7
            )
            
            ai_response = json.loads(response.choices[0].message.content)
            return ai_response
            
        except Exception as e:
            print(f"Error en OpenAI recommendation: {str(e)}")
            return {
                'insights': f'Recomendación automática: {base_quantity} unidades basada en histórico',
                'priority': 'medium',
                'justification': 'Cálculo automático por falta de conectividad con IA'
            }
    
    def _get_openai_forecast_insights(self, product, forecast_data):
        """Obtener insights de pronósticos usando OpenAI"""
        
        if not hasattr(settings, 'OPENAI_API_KEY') or not settings.OPENAI_API_KEY or not forecast_data:
            return {
                'summary': 'Análisis automático de pronósticos basado en modelos ML',
                'trends': 'Tendencia estable basada en datos históricos',
                'recommendations': 'Mantener niveles de stock actuales',
                'risk_factors': 'Riesgo bajo de desabastecimiento'
            }
        
        try:
            # Preparar datos de pronóstico para IA
            forecast_summary = {
                'total_demand': sum(f['predicted_demand'] for f in forecast_data),
                'avg_confidence': sum(f['confidence_level'] for f in forecast_data) / len(forecast_data),
                'demand_range': {
                    'min': min(f['predicted_demand'] for f in forecast_data),
                    'max': max(f['predicted_demand'] for f in forecast_data)
                }
            }
            
            prompt = f"""
            Analiza estos pronósticos de demanda para el producto "{product.name}":
            
            Datos del producto:
            - Stock actual: {product.stock}
            - Stock mínimo: {product.min_stock}
            
            Pronósticos:
            - Demanda total pronosticada: {forecast_summary['total_demand']}
            - Confianza promedio: {forecast_summary['avg_confidence']}%
            - Rango de demanda: {forecast_summary['demand_range']['min']} - {forecast_summary['demand_range']['max']}
            
            Proporciona análisis en formato JSON con:
            - summary: Resumen ejecutivo
            - trends: Análisis de tendencias
            - recommendations: Recomendaciones específicas
            - risk_factors: Factores de riesgo identificados
            """
            
            import openai
            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400,
                temperature=0.7
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            print(f"Error en OpenAI forecast insights: {str(e)}")
            return {
                'summary': 'Análisis automático disponible',
                'trends': 'Tendencia basada en modelos ML',
                'recommendations': 'Continuar monitoreo regular',
                'risk_factors': 'Evaluación automática de riesgos'
            }
    
    def _get_available_ml_models(self, product):
        """Obtener modelos ML disponibles para este producto"""
        try:
            from forecasting.models import ForecastModel
            
            models = ForecastModel.objects.filter(
                company=product.company,
                status='active'
            ).filter(
                models.Q(products=product) | 
                models.Q(categories=product.category) |
                models.Q(products__isnull=True, categories__isnull=True)  # Modelos generales
            )
            
            model_data = []
            for model in models:
                model_data.append({
                    'id': model.id,
                    'name': model.name,
                    'type': model.model_type,
                    'accuracy': model.accuracy_score,
                    'mape': float(model.mape) if model.mape else None,
                    'last_trained': model.training_completed_at.isoformat() if model.training_completed_at else None
                })
            
            return model_data
            
        except Exception as e:
            print(f"Error obteniendo modelos ML: {str(e)}")
            return []
    
    def _get_model_recommendations(self):
        """Recomendar modelos ML adicionales a implementar"""
        return {
            'recommended_models': [
                {
                    'name': 'XGBoost Forecaster',
                    'description': 'Modelo de gradient boosting para patrones complejos',
                    'benefits': 'Mejor rendimiento en datos no lineales',
                    'complexity': 'medium'
                },
                {
                    'name': 'Transformer Neural Network',
                    'description': 'Red neuronal basada en attention para series temporales',
                    'benefits': 'Excelente para patrones estacionales complejos',
                    'complexity': 'high'
                },
                {
                    'name': 'Seasonal ARIMA (SARIMA)',
                    'description': 'ARIMA con componentes estacionales',
                    'benefits': 'Manejo explícito de estacionalidad',
                    'complexity': 'medium'
                },
                {
                    'name': 'Facebook Prophet con regressors',
                    'description': 'Prophet mejorado con variables externas',
                    'benefits': 'Incorpora factores externos como promociones',
                    'complexity': 'low'
                }
            ],
            'current_models_status': 'Tienes modelos básicos implementados',
            'priority_suggestion': 'Implementar XGBoost para mejorar precisión general'
        }
    
    def _get_model_performance_summary(self, product):
        """Resumen del rendimiento de modelos para este producto"""
        try:
            from forecasting.models import ForecastModel
            
            models = ForecastModel.objects.filter(
                company=product.company,
                status='active'
            )
            
            performance = {
                'total_models': models.count(),
                'best_model': None,
                'avg_accuracy': 0,
                'model_comparison': []
            }
            
            if models.exists():
                best_model = models.filter(mape__isnull=False).order_by('mape').first()
                if best_model:
                    performance['best_model'] = {
                        'name': best_model.name,
                        'type': best_model.model_type,
                        'accuracy': best_model.accuracy_score
                    }
                
                accuracies = [m.accuracy_score for m in models if m.accuracy_score]
                if accuracies:
                    performance['avg_accuracy'] = sum(accuracies) / len(accuracies)
            
            return performance
            
        except Exception as e:
            print(f"Error en performance summary: {str(e)}")
            return {'total_models': 0, 'best_model': None, 'avg_accuracy': 0}
    
    def _generate_purchase_order_email_with_ai(self, product, quantity, user):
        """Generar contenido de email para orden de compra usando OpenAI"""
        
        if not hasattr(settings, 'OPENAI_API_KEY') or not settings.OPENAI_API_KEY:
            return self._generate_basic_purchase_email(product, quantity, user)
        
        try:
            supplier_info = ""
            if product.supplier:
                supplier_info = f"Proveedor: {product.supplier.name}"
                if hasattr(product.supplier, 'contact_name'):
                    supplier_info += f"\nContacto: {product.supplier.contact_name}"
            
            prompt = f"""
            Genera un email profesional para solicitar una orden de compra con estos detalles:
            
            Producto: {product.name}
            SKU: {product.sku}
            Cantidad solicitada: {quantity}
            Precio unitario: S/ {product.cost_price}
            Total estimado: S/ {quantity * float(product.cost_price)}
            {supplier_info}
            
            Solicitante: {user.get_full_name() or user.username}
            Empresa: {product.company.name if hasattr(product, 'company') else 'DataLens'}
            
            El email debe ser:
            - Profesional y cordial
            - Incluir todos los detalles necesarios
            - Solicitar confirmación de disponibilidad y tiempo de entrega
            - Incluir datos de contacto para coordinación de entrega
            
            Responde en formato JSON con keys: subject, message
            """
            
            import openai
            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.7
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            print(f"Error generando email con OpenAI: {str(e)}")
            return self._generate_basic_purchase_email(product, quantity, user)
    
    def _generate_basic_purchase_email(self, product, quantity, user):
        """Generar email básico sin IA"""
        subject = f"Solicitud de Compra - {product.name} (SKU: {product.sku})"
        
        message = f"""
        Estimado proveedor,
        
        Nos dirigimos a ustedes para solicitar la siguiente orden de compra:
        
        DETALLES DEL PEDIDO:
        • Producto: {product.name}
        • SKU: {product.sku}
        • Cantidad: {quantity} unidades
        • Precio unitario: S/ {product.cost_price}
        • Total estimado: S/ {quantity * float(product.cost_price)}
        
        Por favor, confirmen:
        1. Disponibilidad del producto
        2. Tiempo de entrega estimado
        3. Condiciones de pago
        4. Datos para coordinación de entrega
        
        Quedamos atentos a su respuesta.
        
        Saludos cordiales,
        {user.get_full_name() or user.username}
        {product.company.name if hasattr(product, 'company') else 'DataLens'}
        """
        
        return {'subject': subject, 'message': message}
    
    def _send_email_to_supplier(self, supplier_email, email_content, product, quantity):
        """Enviar email específicamente al proveedor"""
        try:
            from django.core.mail import send_mail
            
            send_mail(
                subject=email_content['subject'],
                message=email_content['message'],
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[supplier_email],
                fail_silently=False,
            )
            
            return {
                'status': 'success',
                'message': f'Email enviado exitosamente al proveedor',
                'recipient': supplier_email
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error enviando email: {str(e)}',
                'recipient': supplier_email
            }
    
    def _send_email_to_custom(self, custom_email, email_content, product, quantity):
        """Enviar email a dirección personalizada del usuario"""
        try:
            from django.core.mail import send_mail
            
            send_mail(
                subject=email_content['subject'],
                message=email_content['message'],
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[custom_email],
                fail_silently=False,
            )
            
            return {
                'status': 'success',
                'message': f'Email enviado exitosamente a dirección personalizada',
                'recipient': custom_email
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error enviando email: {str(e)}',
                'recipient': custom_email
            }
    
    def _send_email_to_user(self, user_email, email_content, product, quantity):
        """Enviar email al usuario solicitante"""
        try:
            from django.core.mail import send_mail
            
            # Modificar el email para que sea una copia para el usuario
            user_subject = f"[COPIA] {email_content['subject']}"
            user_message = f"Esta es una copia de la orden de compra generada:\n\n{email_content['message']}"
            
            send_mail(
                subject=user_subject,
                message=user_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user_email],
                fail_silently=False,
            )
            
            return {
                'status': 'success',
                'message': f'Copia de email enviada exitosamente',
                'recipient': user_email
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error enviando email: {str(e)}',
                'recipient': user_email
            }
    
    def _build_product_context(self, product):
        """Construir contexto adicional del producto para IA"""
        try:
            # Obtener transacciones recientes
            recent_sales = Transaction.objects.filter(
                product=product,
                transaction_type='sale',
                transaction_date__gte=timezone.now().date() - timedelta(days=30)
            ).count()
            
            context = f"Ventas recientes (30 días): {recent_sales}. "
            context += f"Categoría: {product.category.name if product.category else 'Sin categoría'}. "
            
            if product.supplier:
                context += f"Proveedor actual: {product.supplier.name}. "
            
            return context
            
        except Exception:
            return "Contexto limitado disponible."
    
    def _update_stock_alert(self, product, data):
        """Actualizar configuración de alerta de stock"""
        new_min_stock = data.get('min_stock')
        new_reorder_point = data.get('reorder_point')
        
        if new_min_stock is not None:
            product.min_stock = new_min_stock
        if new_reorder_point is not None:
            product.reorder_point = new_reorder_point
        
        product.save()
        
        return {
            'action': 'update_stock_alert',
            'product_id': product.id,
            'product_name': product.name,
            'min_stock': product.min_stock,
            'reorder_point': product.reorder_point,
            'message': 'Configuración de alertas actualizada'
        }