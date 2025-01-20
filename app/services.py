import pandas as pd
from typing import Dict, List
from datetime import datetime
from sklearn.ensemble import RandomForestRegressor
import numpy as np
#
class PredictiveService:
    def __init__(self):
        self.model = None
        self.df = None
        print("Iniciando PredictiveService...")
        self.load_data()

    def load_data(self):
        """
        Cargar datos desde CSV o base de datos
        """
        try:
            print("Intentando cargar datos...")
            self.df = pd.read_csv('data/data_final_creada.csv')
            print(f"Columnas cargadas: {self.df.columns.tolist()}")
            self.df['fecha'] = pd.to_datetime(self.df['fecha'])
            print("Datos cargados exitosamente")
        except Exception as e:
            print(f"Error cargando datos: {e}")
            self.df = pd.DataFrame()

    def analyze_customer_behavior(self, customer_id: str) -> Dict:
        """
        Analiza el comportamiento de un cliente específico
        """
        print(f"\nAnalizando comportamiento para customer_id: {customer_id}")
        
        if self.df is None:
            print("Error: DataFrame es None")
            return {"error": "No hay datos disponibles"}

        print(f"Shape del DataFrame: {self.df.shape}")
        customer_data = self.df[self.df['Customer_ID'] == customer_id]
        print(f"Datos encontrados para el cliente: {len(customer_data)} registros")
        
        if customer_data.empty:
            print("No se encontraron datos para este cliente")
            return {"error": "No se encontraron datos para este cliente"}

        try:
            print("Calculando métricas...")
            
            # Calcular total_transactions
            total_trans = len(customer_data)
            print(f"Total transacciones: {total_trans}")
            
            # Calcular average_purchase
            avg_purchase = customer_data['precio_final'].mean()
            print(f"Compra promedio: {avg_purchase}")
            
            # Obtener preferred_category
            pref_category = customer_data['categoria'].mode().iloc[0] if not customer_data.empty else None
            print(f"Categoría preferida: {pref_category}")
            
            # Obtener preferred_payment
            pref_payment = customer_data['payment_method'].mode().iloc[0] if not customer_data.empty else None
            print(f"Método de pago preferido: {pref_payment}")
            
            # Obtener favorite_mall
            fav_mall = customer_data['shopping_mall'].mode().iloc[0] if not customer_data.empty else None
            print(f"Centro comercial favorito: {fav_mall}")
            
            result = {
                "total_transactions": total_trans,
                "average_purchase": float(avg_purchase),  # Convertir explícitamente a float
                "preferred_category": pref_category,
                "preferred_payment": pref_payment,
                "favorite_mall": fav_mall
            }
            
            print("Resultado final:", result)
            return result
            
        except Exception as e:
            print(f"Error durante el análisis: {e}")
            print(f"Tipos de datos en customer_data:\n{customer_data.dtypes}")
            raise

    def predict_sales(self, filters: Dict) -> Dict:
        """
        Predice ventas basadas en filtros específicos
        """
        print(f"\nPrediciendo ventas con filtros: {filters}")
        
        if self.df is None:
            print("Error: DataFrame es None")
            return {"error": "No hay datos disponibles"}

        try:
            # Filtrar datos según los criterios recibidos
            filtered_data = self.df.copy()
            
            if 'categoria' in filters:
                filtered_data = filtered_data[filtered_data['categoria'] == filters['categoria']]
                
            if 'shopping_mall' in filters:
                filtered_data = filtered_data[filtered_data['shopping_mall'] == filters['shopping_mall']]
                
            if 'Store_Type' in filters:
                filtered_data = filtered_data[filtered_data['Store_Type'] == filters['Store_Type']]
                
            if 'Season' in filters:
                filtered_data = filtered_data[filtered_data['Season'] == filters['Season']]
                
            # Filtrar por fecha si se proporcionan fechas
            if 'fecha_inicio' in filters and 'fecha_fin' in filters:
                fecha_inicio = pd.to_datetime(filters['fecha_inicio'])
                fecha_fin = pd.to_datetime(filters['fecha_fin'])
                filtered_data = filtered_data[
                    (filtered_data['fecha'] >= fecha_inicio) & 
                    (filtered_data['fecha'] <= fecha_fin)
                ]

            if filtered_data.empty:
                return {
                    "predicted_sales": 0,
                    "confidence_score": 0,
                    "contributing_factors": [],
                    "message": "No hay datos suficientes para los filtros proporcionados"
                }

            # Calcular métricas básicas
            historical_sales = filtered_data['precio_final'].sum()
            avg_daily_sales = filtered_data.groupby('fecha')['precio_final'].sum().mean()
            
            # Calcular tendencia
            daily_sales = filtered_data.groupby('fecha')['precio_final'].sum()
            trend = np.polyfit(range(len(daily_sales)), daily_sales.values, 1)[0]
            
            # Calcular factores contribuyentes
            contributing_factors = []
            
            if 'Discount_Applied' in filters:
                discount_impact = filters['Discount_Applied'] * historical_sales
                contributing_factors.append({
                    "factor": "discount",
                    "impact": float(discount_impact)
                })

            # Predicción simple basada en tendencia histórica
            predicted_sales = float(avg_daily_sales * 30)  # Predicción para 30 días
            if trend > 0:
                predicted_sales *= 1.1  # Aumentar predicción si hay tendencia positiva
            elif trend < 0:
                predicted_sales *= 0.9  # Disminuir predicción si hay tendencia negativa

            # Calcular score de confianza basado en cantidad de datos
            total_records = len(filtered_data)
            confidence_score = min(0.95, total_records / 1000) if total_records > 0 else 0

            return {
                "predicted_sales": round(predicted_sales, 2),
                "confidence_score": round(confidence_score, 2),
                "contributing_factors": contributing_factors,
                "metrics": {
                    "historical_sales": float(historical_sales),
                    "avg_daily_sales": float(avg_daily_sales),
                    "trend": float(trend),
                    "total_records_analyzed": total_records
                }
            }

        except Exception as e:
            print(f"Error en predicción de ventas: {e}")
            return {
                "error": f"Error en predicción: {str(e)}",
                "predicted_sales": 0,
                "confidence_score": 0,
                "contributing_factors": []
            }

    def get_mall_analytics(self, mall_name: str) -> Dict:
        """
        Análisis específico por centro comercial
        """
        print(f"\nAnalizando centro comercial: {mall_name}")
        
        if self.df is None:
            print("Error: DataFrame es None")
            return {"error": "No hay datos disponibles"}
                
        try:
            mall_data = self.df[self.df['shopping_mall'] == mall_name]
            print(f"Registros encontrados para el centro comercial: {len(mall_data)}")
            
            if mall_data.empty:
                return {
                    "message": "No se encontraron datos para este centro comercial",
                    "daily_sales": {},
                    "popular_products": {},
                    "customer_demographics": {
                        "gender_distribution": {},
                        "age_groups": {}
                    }
                }

            # Procesar ventas diarias
            daily_sales = mall_data.groupby('fecha')['precio_final'].sum()
            daily_sales_dict = {
                str(date.date()): round(float(value), 2)
                for date, value in daily_sales.items()
                if pd.notna(value) and not np.isinf(value)
            }

            # Procesar productos populares
            products = mall_data.groupby('Product')['cantidad'].sum().nlargest(5)
            popular_products_dict = {
                str(product): round(float(value), 2)
                for product, value in products.items()
                if pd.notna(value) and not np.isinf(value)
            }

            # Procesar demografía de clientes
            gender_dist = mall_data['gender'].value_counts()
            gender_dict = {
                str(gender): int(value)
                for gender, value in gender_dist.items()
                if pd.notna(value)
            }

            # Estadísticas de edad
            age_stats = mall_data['edad'].describe()
            age_dict = {
                str(stat): round(float(value), 2)
                for stat, value in age_stats.items()
                if pd.notna(value) and not np.isinf(value)
            }

            # Métodos de pago más usados
            payment_methods = mall_data['payment_method'].value_counts()
            payment_dict = {
                str(method): int(value)
                for method, value in payment_methods.items()
                if pd.notna(value)
            }

            return {
                "mall_name": mall_name,
                "daily_sales": daily_sales_dict,
                "popular_products": popular_products_dict,
                "demographics": {
                    "gender_distribution": gender_dict,
                    "age_groups": age_dict
                },
                "payment_methods": payment_dict,
                "summary": {
                    "total_sales": round(float(mall_data['precio_final'].sum()), 2),
                    "total_transactions": len(mall_data),
                    "average_transaction": round(float(mall_data['precio_final'].mean()), 2),
                    "total_products_sold": int(mall_data['cantidad'].sum())
                }
            }
            
        except Exception as e:
            print(f"Error en análisis del centro comercial: {e}")
            return {
                "error": f"Error procesando datos del centro comercial: {str(e)}",
                "mall_name": mall_name,
                "daily_sales": {},
                "popular_products": {},
                "demographics": {
                    "gender_distribution": {},
                    "age_groups": {}
                },
                "payment_methods": {},
                "summary": {}
            }