# api/chart_generator.py
import plotly.express as px
import plotly.graph_objects as go
import json
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

def generate_sales_chart(data: list) -> dict:
    """
    Genera un gráfico de líneas de la tendencia de ventas.
    Se espera que 'data' sea una lista de diccionarios con las claves 'date_of_entry' y 'sales'.
    """
    try:
        # Validar que existan datos
        if not data:
            return {"error": "No se proporcionaron datos para generar el gráfico."}
            
        df = pd.DataFrame(data)
        
        # Manejar diferentes nombres de columnas (date/fecha, sales/ventas)
        date_columns = ['date_of_entry', 'date', 'fecha']
        sales_columns = ['sales', 'ventas']
        
        # Identificar columnas de fecha y ventas
        date_col = next((col for col in date_columns if col in df.columns), None)
        sales_col = next((col for col in sales_columns if col in df.columns), None)
        
        if not date_col or not sales_col:
            return {"error": "Los datos deben contener columnas de fecha y ventas."}
        
        # Renombrar columnas para procesamiento estándar
        df = df.rename(columns={date_col: 'date', sales_col: 'sales'})
        
        # Convertir la columna de fecha a formato datetime
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df.dropna(subset=['date'])
        
        # Agrupar por fecha y sumar las ventas si hay registros duplicados en la misma fecha
        df_grouped = df.groupby('date', as_index=False).sum()
        
        # Ordenar por fecha
        df_grouped = df_grouped.sort_values('date')
        
        # Calcular crecimiento mes a mes
        if len(df_grouped) > 1:
            df_grouped['growth'] = df_grouped['sales'].pct_change() * 100
            df_grouped['growth'] = df_grouped['growth'].fillna(0).round(1)
        else:
            df_grouped['growth'] = 0
        
        # Formato de fecha para mejor visualización
        df_grouped['formatted_date'] = df_grouped['date'].dt.strftime('%d-%m-%Y')
        
        # Crear el gráfico interactivo
        fig = px.line(df_grouped, x='date', y='sales', 
                      title='Tendencia de Ventas',
                      labels={'sales': 'Ventas (S/)', 'date': 'Fecha', 'growth': 'Crecimiento (%)'},
                      custom_data=['formatted_date', 'growth'])
        
        # Mejorar el aspecto visual
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#0A192F",
            plot_bgcolor="#0A192F",
            font=dict(color="#E6E6E6"),
            xaxis=dict(showgrid=True, gridcolor="#1C3D5A"),
            yaxis=dict(showgrid=True, gridcolor="#1C3D5A"),
            hovermode="x unified"
        )
        
        # Personalizar el tooltip
        fig.update_traces(
            hovertemplate="<b>Fecha:</b> %{customdata[0]}<br><b>Ventas:</b> S/ %{y:,.2f}<br><b>Crecimiento:</b> %{customdata[1]}%"
        )
        
        # Agregar línea de tendencia
        if len(df_grouped) > 2:
            x = np.array(range(len(df_grouped)))
            y = df_grouped['sales'].values
            coeffs = np.polyfit(x, y, 1)
            trend = np.poly1d(coeffs)
            
            fig.add_trace(go.Scatter(
                x=df_grouped['date'],
                y=trend(x),
                mode='lines',
                line=dict(color='rgba(255, 255, 255, 0.5)', dash='dash'),
                name='Tendencia'
            ))
        
        # Análisis básico
        analysis = {
            "total_sales": float(df_grouped['sales'].sum()),
            "average_sale": float(df_grouped['sales'].mean()),
            "max_sale": float(df_grouped['sales'].max()),
            "min_sale": float(df_grouped['sales'].min()),
            "growth_rate": float(df_grouped['growth'].iloc[-1]) if len(df_grouped) > 1 else 0,
            "data_points": len(df_grouped)
        }
        
        # Convertir la figura a JSON para enviarla al front
        return {
            "chart": json.loads(fig.to_json()),
            "analysis": analysis,
            "raw_data": df_grouped[['formatted_date', 'sales', 'growth']].to_dict('records')
        }
    except Exception as e:
        return {"error": f"Error generando el gráfico: {str(e)}"}

def generate_category_chart(data: list, category_field: str = 'category', value_field: str = 'value') -> dict:
    """
    Genera un gráfico de barras para comparar categorías.
    """
    try:
        if not data:
            return {"error": "No se proporcionaron datos para generar el gráfico."}
            
        df = pd.DataFrame(data)
        
        # Manejar diferentes nombres de columnas
        if category_field not in df.columns:
            category_candidates = ['category', 'categoria', 'campaña', 'region', 'categoría']
            category_field = next((col for col in category_candidates if col in df.columns), None)
            
        if value_field not in df.columns:
            value_candidates = ['value', 'valor', 'ventas', 'sales']
            value_field = next((col for col in value_candidates if col in df.columns), None)
        
        if not category_field or not value_field:
            return {"error": "Los datos deben contener columnas para categoría y valor."}
        
        # Agrupar por categoría y ordenar por valor
        df_grouped = df.groupby(category_field, as_index=False)[value_field].sum()
        df_grouped = df_grouped.sort_values(value_field, ascending=False)
        
        # Calcular porcentajes
        total = df_grouped[value_field].sum()
        df_grouped['percentage'] = (df_grouped[value_field] / total * 100).round(1)
        
        # Crear el gráfico
        fig = px.bar(df_grouped, x=category_field, y=value_field, 
                     title='Análisis por Categoría',
                     labels={value_field: 'Ventas (S/)', category_field: 'Categoría'},
                     custom_data=['percentage'])
        
        # Mejorar el aspecto visual
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#0A192F",
            plot_bgcolor="#0A192F",
            font=dict(color="#E6E6E6"),
            xaxis=dict(showgrid=True, gridcolor="#1C3D5A"),
            yaxis=dict(showgrid=True, gridcolor="#1C3D5A")
        )
        
        # Personalizar el tooltip
        fig.update_traces(
            hovertemplate="<b>%{x}</b><br>Ventas: S/ %{y:,.2f}<br>Porcentaje: %{customdata[0]}%",
            marker_color="#00E6E6"
        )
        
        # Análisis básico
        analysis = {
            "total": float(total),
            "categories_count": len(df_grouped),
            "top_category": df_grouped.iloc[0][category_field],
            "top_category_value": float(df_grouped.iloc[0][value_field]),
            "top_category_percentage": float(df_grouped.iloc[0]['percentage'])
        }
        
        # Si hay más de una categoría, añadir análisis de la segunda
        if len(df_grouped) > 1:
            analysis["second_category"] = df_grouped.iloc[1][category_field]
            analysis["second_category_value"] = float(df_grouped.iloc[1][value_field])
            analysis["second_category_percentage"] = float(df_grouped.iloc[1]['percentage'])
        
        return {
            "chart": json.loads(fig.to_json()),
            "analysis": analysis,
            "raw_data": df_grouped.to_dict('records')
        }
    except Exception as e:
        return {"error": f"Error generando el gráfico: {str(e)}"}

def generate_regional_chart(data: list, region_field: str = 'region', value_field: str = 'sales') -> dict:
    """
    Genera un gráfico para análisis regional.
    """
    try:
        if not data:
            return {"error": "No se proporcionaron datos para generar el gráfico."}
            
        df = pd.DataFrame(data)
        
        # Manejar diferentes nombres de columnas
        if region_field not in df.columns:
            region_candidates = ['region', 'región', 'zona', 'departamento', 'provincia']
            region_field = next((col for col in region_candidates if col in df.columns), None)
            
        if value_field not in df.columns:
            value_candidates = ['sales', 'ventas', 'value', 'valor']
            value_field = next((col for col in value_candidates if col in df.columns), None)
        
        if not region_field or not value_field:
            return {"error": f"Los datos deben contener columnas para región y ventas."}
        
        # Agrupar por región y ordenar
        df_grouped = df.groupby(region_field, as_index=False)[value_field].sum()
        df_grouped = df_grouped.sort_values(value_field, ascending=False)
        
        # Calcular porcentajes
        total = df_grouped[value_field].sum()
        df_grouped['percentage'] = (df_grouped[value_field] / total * 100).round(1)
        
        # Crear gráfico circular
        fig = px.pie(df_grouped, names=region_field, values=value_field, 
                     title='Distribución Regional',
                     custom_data=['percentage'])
        
        # Mejorar el aspecto visual
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#0A192F",
            plot_bgcolor="#0A192F",
            font=dict(color="#E6E6E6")
        )
        
        # Personalizar el tooltip
        fig.update_traces(
            hovertemplate="<b>%{label}</b><br>Ventas: S/ %{value:,.2f}<br>Porcentaje: %{percent:.1%}"
        )
        
        # Análisis básico
        analysis = {
            "total": float(total),
            "regions_count": len(df_grouped),
            "top_region": df_grouped.iloc[0][region_field],
            "top_region_value": float(df_grouped.iloc[0][value_field]),
            "top_region_percentage": float(df_grouped.iloc[0]['percentage'])
        }
        
        # Si hay más de una región, añadir análisis de la segunda
        if len(df_grouped) > 1:
            analysis["second_region"] = df_grouped.iloc[1][region_field]
            analysis["second_region_value"] = float(df_grouped.iloc[1][value_field])
            analysis["second_region_percentage"] = float(df_grouped.iloc[1]['percentage'])
        
        return {
            "chart": json.loads(fig.to_json()),
            "analysis": analysis,
            "raw_data": df_grouped.to_dict('records')
        }
    except Exception as e:
        return {"error": f"Error generando el gráfico: {str(e)}"}

def generate_time_comparison_chart(data: list, date_field: str = 'date', value_field: str = 'value', 
                                 compare_field: str = 'category') -> dict:
    """
    Genera un gráfico de líneas para comparar diferentes categorías a lo largo del tiempo.
    """
    try:
        if not data:
            return {"error": "No se proporcionaron datos para generar el gráfico."}
            
        df = pd.DataFrame(data)
        
        # Validar columnas
        if date_field not in df.columns or value_field not in df.columns or compare_field not in df.columns:
            date_candidates = ['date', 'fecha', 'date_of_entry']
            value_candidates = ['value', 'valor', 'ventas', 'sales']
            compare_candidates = ['category', 'categoria', 'categoría', 'product', 'producto']
            
            date_field = next((col for col in date_candidates if col in df.columns), None)
            value_field = next((col for col in value_candidates if col in df.columns), None)
            compare_field = next((col for col in compare_candidates if col in df.columns), None)
            
            if not date_field or not value_field or not compare_field:
                return {"error": f"Los datos deben contener columnas para fecha, valor y categoría."}
        
        # Convertir fechas
        df[date_field] = pd.to_datetime(df[date_field], errors='coerce')
        df = df.dropna(subset=[date_field])
        
        # Agrupar datos
        df_grouped = df.groupby([date_field, compare_field], as_index=False)[value_field].sum()
        
        # Ordenar por fecha
        df_grouped = df_grouped.sort_values(date_field)
        
        # Añadir columna de fecha formateada para tooltip
        df_grouped['formatted_date'] = df_grouped[date_field].dt.strftime('%d-%m-%Y')
        
        # Crear gráfico
        fig = px.line(df_grouped, x=date_field, y=value_field, color=compare_field, 
                       title='Comparativa Temporal',
                       labels={value_field: 'Ventas (S/)', date_field: 'Fecha', compare_field: 'Categoría'},
                       custom_data=['formatted_date'])
        
        # Mejorar el aspecto visual
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#0A192F",
            plot_bgcolor="#0A192F",
            font=dict(color="#E6E6E6"),
            xaxis=dict(showgrid=True, gridcolor="#1C3D5A"),
            yaxis=dict(showgrid=True, gridcolor="#1C3D5A")
        )
        
        # Personalizar el tooltip
        fig.update_traces(
            hovertemplate="<b>%{customdata[0]}</b><br>%{y:,.2f} S/"
        )
        
        # Análisis básico
        categories = df_grouped[compare_field].unique()
        category_totals = df_grouped.groupby(compare_field)[value_field].sum().to_dict()
        
        analysis = {
            "total": float(df_grouped[value_field].sum()),
            "categories_count": len(categories),
            "categories": list(categories),
            "category_totals": {k: float(v) for k, v in category_totals.items()},
            "date_range": {
                "min": df_grouped[date_field].min().strftime('%Y-%m-%d'),
                "max": df_grouped[date_field].max().strftime('%Y-%m-%d')
            }
        }
        
        return {
            "chart": json.loads(fig.to_json()),
            "analysis": analysis,
            "raw_data": df_grouped[[date_field, compare_field, value_field]].to_dict('records')
        }
    except Exception as e:
        return {"error": f"Error generando el gráfico: {str(e)}"}

def generate_heatmap_chart(data: list, x_field: str, y_field: str, value_field: str) -> dict:
    """
    Genera un mapa de calor para visualizar correlaciones.
    """
    try:
        if not data:
            return {"error": "No se proporcionaron datos para generar el gráfico."}
            
        df = pd.DataFrame(data)
        
        # Validar columnas
        if x_field not in df.columns or y_field not in df.columns or value_field not in df.columns:
            return {"error": f"Los datos deben contener las columnas '{x_field}', '{y_field}' y '{value_field}'."}
        
        # Pivotar los datos para el heatmap
        pivot_table = df.pivot_table(values=value_field, index=y_field, columns=x_field, aggfunc='mean')
        
        # Crear heatmap con Plotly
        fig = px.imshow(pivot_table, 
                         labels=dict(x=x_field, y=y_field, color=value_field),
                         x=pivot_table.columns,
                         y=pivot_table.index,
                         color_continuous_scale='Viridis')
        
        # Mejorar el aspecto visual
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#0A192F",
            plot_bgcolor="#0A192F",
            font=dict(color="#E6E6E6")
        )
        
        # Añadir valores en las celdas
        fig.update_traces(text=pivot_table.values, texttemplate="%{z:.1f}")
        
        # Análisis básico
        analysis = {
            "x_values_count": len(pivot_table.columns),
            "y_values_count": len(pivot_table.index),
            "max_value": float(pivot_table.max().max()),
            "min_value": float(pivot_table.min().min()),
            "mean_value": float(pivot_table.mean().mean())
        }
        
        return {
            "chart": json.loads(fig.to_json()),
            "analysis": analysis,
            "raw_data": df.to_dict('records')
        }
    except Exception as e:
        return {"error": f"Error generando el heatmap: {str(e)}"}

def generate_sales_prediction(data: list, periods: int = 3) -> dict:
    """
    Genera una predicción simple de ventas futuras basada en tendencias históricas.
    """
    try:
        if not data:
            return {"error": "No se proporcionaron datos para generar la predicción."}
            
        df = pd.DataFrame(data)
        
        # Identificar columnas de fecha y ventas
        date_columns = ['date_of_entry', 'date', 'fecha']
        sales_columns = ['sales', 'ventas']
        
        date_col = next((col for col in date_columns if col in df.columns), None)
        sales_col = next((col for col in sales_columns if col in df.columns), None)
        
        if not date_col or not sales_col:
            return {"error": "Los datos deben contener columnas de fecha y ventas."}
        
        # Preparar datos
        df = df.rename(columns={date_col: 'date', sales_col: 'sales'})
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df.dropna(subset=['date'])
        
        # Agrupar por fecha
        df_grouped = df.groupby('date', as_index=False)['sales'].sum()
        df_grouped = df_grouped.sort_values('date')
        
        # Necesitamos al menos 3 puntos para una predicción decente
        if len(df_grouped) < 3:
            return {"error": "Se necesitan al menos 3 puntos de datos para generar una predicción."}
        
        # Calcular tendencia lineal
        x = np.array(range(len(df_grouped)))
        y = df_grouped['sales'].values
        coeffs = np.polyfit(x, y, 1)
        trend = np.poly1d(coeffs)
        
        # Generar fechas futuras
        last_date = df_grouped['date'].iloc[-1]
        future_dates = [last_date + timedelta(days=(i+1)*30) for i in range(periods)]
        
        # Predecir valores
        future_x = np.array(range(len(df_grouped), len(df_grouped) + periods))
        future_y = trend(future_x)
        
        # Crear DataFrame con predicciones
        predictions_df = pd.DataFrame({
            'date': future_dates,
            'sales': future_y,
            'is_prediction': True
        })
        
        # Combinar datos históricos y predicciones
        df_grouped['is_prediction'] = False
        combined_df = pd.concat([df_grouped, predictions_df])
        
        # Añadir fecha formateada
        combined_df['formatted_date'] = combined_df['date'].dt.strftime('%d-%m-%Y')
        
        # Crear gráfico
        fig = px.line(combined_df, x='date', y='sales', 
                      color='is_prediction',
                      color_discrete_map={False: '#00E6E6', True: '#FF5722'},
                      title='Predicción de Ventas',
                      labels={'sales': 'Ventas (S/)', 'date': 'Fecha', 'is_prediction': 'Tipo'},
                      custom_data=['formatted_date'])
        
        # Mejorar el aspecto visual
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#0A192F",
            plot_bgcolor="#0A192F",
            font=dict(color="#E6E6E6"),
            xaxis=dict(showgrid=True, gridcolor="#1C3D5A"),
            yaxis=dict(showgrid=True, gridcolor="#1C3D5A"),
            legend=dict(
                title="Datos",
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        # Personalizar el tooltip
        fig.update_traces(
            hovertemplate="<b>Fecha:</b> %{customdata[0]}<br><b>Ventas:</b> S/ %{y:,.2f}"
        )
        
        # Actualizar nombres en la leyenda
        fig.for_each_trace(lambda t: t.update(name = "Histórico" if t.name == "False" else "Predicción"))
        
        # Análisis de la predicción
        prediction_data = predictions_df[['formatted_date', 'sales']].to_dict('records')
        last_historical = float(df_grouped['sales'].iloc[-1])
        last_prediction = float(predictions_df['sales'].iloc[-1])
        growth_rate = ((last_prediction / last_historical) - 1) * 100
        
        analysis = {
            "historical_average": float(df_grouped['sales'].mean()),
            "predicted_average": float(predictions_df['sales'].mean()),
            "growth_rate": float(growth_rate),
            "confidence": 85.0,  # Valor fijo ya que es un modelo simple
            "last_historical_date": df_grouped['formatted_date'].iloc[-1],
            "last_historical_value": last_historical,
            "prediction_periods": periods
        }
        
        return {
            "chart": json.loads(fig.to_json()),
            "analysis": analysis,
            "predictions": prediction_data
        }
    except Exception as e:
        return {"error": f"Error generando la predicción: {str(e)}"}