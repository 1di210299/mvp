# api/prediction.py
import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np

def predict_sales(data: list, future_periods: int = 5) -> dict:
    """
    Realiza una predicción simple de ventas futuras utilizando regresión lineal.
    Se espera que 'data' sea una lista de diccionarios con las claves 'date_of_entry' y 'sales'.
    """
    df = pd.DataFrame(data)
    if 'date_of_entry' not in df.columns or 'sales' not in df.columns:
        return {"error": "Los datos deben contener las columnas 'date_of_entry' y 'sales'."}
    
    # Convertir la columna de fecha y ordenar
    df['date_of_entry'] = pd.to_datetime(df['date_of_entry'], errors='coerce')
    df = df.dropna(subset=['date_of_entry']).sort_values('date_of_entry')
    
    # Crear una columna de 'días' desde la fecha mínima
    df['days'] = (df['date_of_entry'] - df['date_of_entry'].min()).dt.days
    X = df[['days']]
    y = df['sales']
    
    # Entrenar el modelo de regresión lineal
    model = LinearRegression()
    model.fit(X, y)
    
    # Predecir para 'future_periods' días adicionales
    last_day = df['days'].max()
    future_days = np.array(range(last_day + 1, last_day + future_periods + 1)).reshape(-1, 1)
    predictions = model.predict(future_days)
    
    # Crear una lista con las predicciones y las fechas correspondientes
    future_dates = [df['date_of_entry'].min() + pd.Timedelta(days=int(d)) for d in future_days.flatten()]
    prediction_data = [
        {"date": str(date.date()), "predicted_sales": float(pred)}
        for date, pred in zip(future_dates, predictions)
    ]
    
    return {"predictions": prediction_data}
