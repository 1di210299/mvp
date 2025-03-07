# api/chart_generator.py
import plotly.express as px
import json
import pandas as pd

def generate_sales_chart(data: list) -> dict:
    """
    Genera un gráfico de líneas de la tendencia de ventas.
    Se espera que 'data' sea una lista de diccionarios con las claves 'date_of_entry' y 'sales'.
    """
    df = pd.DataFrame(data)
    if 'date_of_entry' not in df.columns or 'sales' not in df.columns:
        return {"error": "Los datos deben contener las columnas 'date_of_entry' y 'sales'."}
    
    # Convertir la columna de fecha a formato datetime
    df['date_of_entry'] = pd.to_datetime(df['date_of_entry'], errors='coerce')
    df = df.dropna(subset=['date_of_entry'])
    
    # Agrupar por fecha y sumar las ventas si hay registros duplicados en la misma fecha
    df_grouped = df.groupby('date_of_entry', as_index=False).sum()
    
    # Crear el gráfico interactivo
    fig = px.line(df_grouped, x='date_of_entry', y='sales', title='Tendencia de Ventas')
    
    # Convertir la figura a JSON para enviarla al front
    return json.loads(fig.to_json())
