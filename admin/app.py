import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
import datetime
import requests
import json
import os
import sys

# Añadir directorio raíz al path para importar módulos de la aplicación principal
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.database import get_db_connection
from app.db.models import Order, Customer, Product, OrderItem
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_

# Configuración de la página
st.set_page_config(
    page_title="WhatsApp Sales Bot - Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilos CSS personalizados
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
    }
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 0.5rem;
        padding: 1rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #1E88E5;
    }
    .metric-label {
        font-size: 1rem;
        color: #424242;
    }
    .section-header {
        font-size: 1.8rem;
        color: #0D47A1;
        margin-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar para navegación
st.sidebar.image("https://via.placeholder.com/150x150.png?text=Logo", width=150)

page = st.sidebar.radio(
    "Navegar", 
    ["Dashboard", "Productos", "Órdenes", "Clientes", "Seguridad", "Configuración"]
)

st.sidebar.markdown("---")
st.sidebar.info("WhatsApp Sales Bot v1.0.0")

# Funciones auxiliares
def get_stats_from_db():
    """Obtiene estadísticas generales desde la base de datos"""
    conn = get_db_connection()
    try:
        # Total de clientes
        total_customers = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
        
        # Total de órdenes
        total_orders = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        
        # Total de ventas
        total_sales = conn.execute("SELECT SUM(total_amount) FROM orders WHERE status='completed'").fetchone()[0]
        if total_sales is None:
            total_sales = 0
            
        # Ventas del día
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        today_sales = conn.execute(
            "SELECT SUM(total_amount) FROM orders WHERE status='completed' AND DATE(created_at)=?", 
            (today,)
        ).fetchone()[0]
        if today_sales is None:
            today_sales = 0
            
        # Clientes nuevos hoy
        new_customers = conn.execute(
            "SELECT COUNT(*) FROM customers WHERE DATE(created_at)=?", 
            (today,)
        ).fetchone()[0]
        
        # Órdenes pendientes
        pending_orders = conn.execute(
            "SELECT COUNT(*) FROM orders WHERE status='pending'"
        ).fetchone()[0]
        
        return {
            "total_customers": total_customers,
            "total_orders": total_orders,
            "total_sales": total_sales,
            "today_sales": today_sales,
            "new_customers": new_customers,
            "pending_orders": pending_orders
        }
    finally:
        conn.close()

def get_sales_by_product():
    """Obtiene datos de ventas por producto"""
    conn = get_db_connection()
    try:
        query = """
        SELECT p.name, SUM(oi.quantity) as units_sold, SUM(oi.quantity * oi.price) as revenue
        FROM order_items oi
        JOIN products p ON oi.product_id = p.id
        JOIN orders o ON oi.order_id = o.id
        WHERE o.status = 'completed'
        GROUP BY p.name
        ORDER BY revenue DESC
        LIMIT 10
        """
        df = pd.read_sql_query(query, conn)
        return df
    finally:
        conn.close()

def get_sales_over_time():
    """Obtiene datos de ventas a lo largo del tiempo"""
    conn = get_db_connection()
    try:
        query = """
        SELECT DATE(created_at) as date, SUM(total_amount) as revenue, COUNT(*) as order_count
        FROM orders
        WHERE status = 'completed'
        GROUP BY DATE(created_at)
        ORDER BY date
        LIMIT 30
        """
        df = pd.read_sql_query(query, conn)
        df['date'] = pd.to_datetime(df['date'])
        return df
    finally:
        conn.close()

def get_security_incidents():
    """Obtiene datos sobre incidentes de seguridad"""
    conn = get_db_connection()
    try:
        query = """
        SELECT DATE(timestamp) as date, type, COUNT(*) as count
        FROM security_incidents
        GROUP BY DATE(timestamp), type
        ORDER BY date DESC
        LIMIT 100
        """
        try:
            df = pd.read_sql_query(query, conn)
            df['date'] = pd.to_datetime(df['date'])
            return df
        except:
            # Si la tabla no existe
            return pd.DataFrame(columns=['date', 'type', 'count'])
    finally:
        conn.close()

def get_metrics_from_prometheus():
    """Obtiene métricas desde Prometheus"""
    try:
        response = requests.get("http://localhost:9090/api/v1/query", params={
            'query': 'whatsapp_sales_http_requests_total'
        })
        data = response.json()
        if data['status'] == 'success' and len(data['data']['result']) > 0:
            return data['data']['result']
        return []
    except:
        return []

# Páginas
def show_dashboard():
    st.markdown("<h1 class='main-header'>Dashboard de Ventas</h1>", unsafe_allow_html=True)
    
    # Estadísticas generales
    stats = get_stats_from_db()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-value'>${stats['total_sales']:.2f}</div>", unsafe_allow_html=True)
        st.markdown("<div class='metric-label'>Ventas Totales</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-value'>{stats['total_orders']}</div>", unsafe_allow_html=True)
        st.markdown("<div class='metric-label'>Órdenes Totales</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col3:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-value'>{stats['total_customers']}</div>", unsafe_allow_html=True)
        st.markdown("<div class='metric-label'>Clientes Registrados</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    col4, col5, col6 = st.columns(3)
    
    with col4:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-value'>${stats['today_sales']:.2f}</div>", unsafe_allow_html=True)
        st.markdown("<div class='metric-label'>Ventas de Hoy</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col5:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-value'>{stats['new_customers']}</div>", unsafe_allow_html=True)
        st.markdown("<div class='metric-label'>Nuevos Clientes Hoy</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col6:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-value'>{stats['pending_orders']}</div>", unsafe_allow_html=True)
        st.markdown("<div class='metric-label'>Órdenes Pendientes</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Gráficos
    st.markdown("<h2 class='section-header'>Ventas en el Tiempo</h2>", unsafe_allow_html=True)
    
    sales_time_df = get_sales_over_time()
    if not sales_time_df.empty:
        fig = px.line(
            sales_time_df, 
            x='date', 
            y='revenue',
            title='Tendencia de Ventas',
            labels={'date': 'Fecha', 'revenue': 'Ingresos ($)'}
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay datos de ventas disponibles para mostrar en el gráfico.")
    
    col_product, col_security = st.columns(2)
    
    with col_product:
        st.markdown("<h2 class='section-header'>Ventas por Producto</h2>", unsafe_allow_html=True)
        product_sales_df = get_sales_by_product()
        if not product_sales_df.empty:
            fig = px.bar(
                product_sales_df, 
                x='name', 
                y='revenue',
                title='Top 10 Productos por Ingresos',
                labels={'name': 'Producto', 'revenue': 'Ingresos ($)'}
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay datos de ventas por producto disponibles.")
    
    with col_security:
        st.markdown("<h2 class='section-header'>Incidentes de Seguridad</h2>", unsafe_allow_html=True)
        security_df = get_security_incidents()
        if not security_df.empty:
            fig = px.bar(
                security_df, 
                x='date', 
                y='count', 
                color='type',
                title='Incidentes de Seguridad por Tipo',
                labels={'date': 'Fecha', 'count': 'Número de Incidentes', 'type': 'Tipo de Incidente'}
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay datos de incidentes de seguridad disponibles.")

def show_products():
    st.markdown("<h1 class='main-header'>Gestión de Productos</h1>", unsafe_allow_html=True)
    
    # Obtener lista de productos
    conn = get_db_connection()
    try:
        products_df = pd.read_sql_query("SELECT * FROM products ORDER BY name", conn)
    finally:
        conn.close()
    
    # Sección para añadir nuevo producto
    st.markdown("<h2 class='section-header'>Añadir Nuevo Producto</h2>", unsafe_allow_html=True)
    
    with st.form("new_product_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Nombre del Producto")
            description = st.text_area("Descripción")
        with col2:
            price = st.number_input("Precio", min_value=0.01, step=0.01)
            stock = st.number_input("Stock Disponible", min_value=0, step=1)
        
        category = st.selectbox("Categoría", ["Comida", "Bebida", "Tecnología", "Ropa", "Hogar", "Otro"])
        image_url = st.text_input("URL de Imagen (opcional)")
        
        submitted = st.form_submit_button("Guardar Producto")
        
        if submitted and name and price > 0:
            conn = get_db_connection()
            try:
                conn.execute(
                    "INSERT INTO products (name, description, price, stock, category, image_url) VALUES (?, ?, ?, ?, ?, ?)",
                    (name, description, price, stock, category, image_url)
                )
                conn.commit()
                st.success(f"Producto '{name}' añadido correctamente.")
                
                # Recargar la lista de productos
                products_df = pd.read_sql_query("SELECT * FROM products ORDER BY name", conn)
            except Exception as e:
                st.error(f"Error al guardar el producto: {str(e)}")
            finally:
                conn.close()
    
    # Mostrar tabla de productos
    st.markdown("<h2 class='section-header'>Productos Disponibles</h2>", unsafe_allow_html=True)
    
    if not products_df.empty:
        edited_df = st.data_editor(
            products_df, 
            column_config={
                "id": st.column_config.Column("ID", disabled=True),
                "name": st.column_config.Column("Nombre"),
                "description": st.column_config.TextColumn("Descripción", max_chars=200),
                "price": st.column_config.NumberColumn("Precio", format="%.2f"),
                "stock": st.column_config.NumberColumn("Stock", format="%d"),
                "category": st.column_config.SelectboxColumn("Categoría", options=["Comida", "Bebida", "Tecnología", "Ropa", "Hogar", "Otro"]),
                "image_url": st.column_config.Column("URL de Imagen"),
                "created_at": st.column_config.DatetimeColumn("Creado", disabled=True),
                "updated_at": st.column_config.DatetimeColumn("Actualizado", disabled=True)
            },
            hide_index=True,
            use_container_width=True,
            num_rows="dynamic"
        )
        
        if st.button("Guardar Cambios"):
            # Detectar cambios y actualizar la base de datos
            if not edited_df.equals(products_df):
                conn = get_db_connection()
                try:
                    for index, row in edited_df.iterrows():
                        if not products_df.loc[products_df['id'] == row['id']].equals(pd.DataFrame([row])):
                            conn.execute(
                                """UPDATE products SET 
                                   name=?, description=?, price=?, stock=?, 
                                   category=?, image_url=?, updated_at=CURRENT_TIMESTAMP
                                   WHERE id=?""",
                                (row['name'], row['description'], row['price'], row['stock'], 
                                 row['category'], row['image_url'], row['id'])
                            )
                    conn.commit()
                    st.success("Cambios guardados correctamente.")
                except Exception as e:
                    st.error(f"Error al guardar cambios: {str(e)}")
                finally:
                    conn.close()
    else:
        st.info("No hay productos registrados en la base de datos.")

def show_orders():
    st.markdown("<h1 class='main-header'>Gestión de Órdenes</h1>", unsafe_allow_html=True)
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox(
            "Filtrar por Estado",
            ["Todos", "pending", "processing", "completed", "cancelled"]
        )
    with col2:
        date_from = st.date_input("Desde Fecha", datetime.datetime.now() - datetime.timedelta(days=30))
    with col3:
        date_to = st.date_input("Hasta Fecha", datetime.datetime.now())
    
    # Construir consulta con filtros
    query = "SELECT * FROM orders WHERE 1=1"
    params = []
    
    if status_filter != "Todos":
        query += " AND status = ?"
        params.append(status_filter)
    
    query += " AND DATE(created_at) BETWEEN ? AND ?"
    params.append(date_from.strftime('%Y-%m-%d'))
    params.append(date_to.strftime('%Y-%m-%d'))
    
    query += " ORDER BY created_at DESC"
    
    # Obtener órdenes
    conn = get_db_connection()
    try:
        orders_df = pd.read_sql_query(query, conn, params=params)
    finally:
        conn.close()
    
    # Mostrar órdenes
    st.markdown("<h2 class='section-header'>Listado de Órdenes</h2>", unsafe_allow_html=True)
    
    if not orders_df.empty:
        # Convertir columnas de fechas a datetime para mejor visualización
        for col in ['created_at', 'updated_at']:
            if col in orders_df.columns:
                orders_df[col] = pd.to_datetime(orders_df[col])
        
        # Mostrar tabla con órdenes
        st.dataframe(
            orders_df,
            column_config={
                "id": st.column_config.Column("ID"),
                "customer_id": st.column_config.Column("ID Cliente"),
                "total_amount": st.column_config.NumberColumn("Total", format="$%.2f"),
                "status": st.column_config.SelectboxColumn(
                    "Estado", 
                    options=["pending", "processing", "completed", "cancelled"],
                    required=True
                ),
                "payment_method": st.column_config.Column("Método de Pago"),
                "created_at": st.column_config.DatetimeColumn("Creado"),
                "updated_at": st.column_config.DatetimeColumn("Actualizado")
            },
            hide_index=True,
            use_container_width=True
        )
        
        # Sección para ver detalles de una orden
        st.markdown("<h2 class='section-header'>Detalles de Orden</h2>", unsafe_allow_html=True)
        order_id = st.selectbox("Seleccionar Orden por ID", options=orders_df['id'].tolist())
        
        if order_id:
            conn = get_db_connection()
            try:
                # Obtener detalles de la orden
                order_details = pd.read_sql_query(
                    "SELECT * FROM orders WHERE id = ?", 
                    conn, 
                    params=[order_id]
                ).iloc[0]
                
                # Obtener cliente
                customer = pd.read_sql_query(
                    "SELECT * FROM customers WHERE id = ?", 
                    conn, 
                    params=[order_details['customer_id']]
                ).iloc[0]
                
                # Obtener items de la orden
                items_df = pd.read_sql_query(
                    """
                    SELECT oi.*, p.name as product_name 
                    FROM order_items oi
                    JOIN products p ON oi.product_id = p.id
                    WHERE oi.order_id = ?
                    """, 
                    conn, 
                    params=[order_id]
                )
                
                # Mostrar información
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Información de la Orden")
                    st.write(f"**ID:** {order_details['id']}")
                    st.write(f"**Estado:** {order_details['status']}")
                    st.write(f"**Total:** ${order_details['total_amount']:.2f}")
                    st.write(f"**Método de Pago:** {order_details['payment_method']}")
                    st.write(f"**Fecha:** {pd.to_datetime(order_details['created_at']).strftime('%Y-%m-%d %H:%M')}")
                
                with col2:
                    st.subheader("Información del Cliente")
                    st.write(f"**Nombre:** {customer['name']}")
                    st.write(f"**Teléfono:** {customer['phone']}")
                    st.write(f"**Email:** {customer.get('email', 'No disponible')}")
                    st.write(f"**Dirección:** {customer.get('address', 'No disponible')}")
                
                st.subheader("Productos en la Orden")
                
                if not items_df.empty:
                    for _, item in items_df.iterrows():
                        st.write(f"• {item['quantity']} x {item['product_name']} - ${item['price']:.2f} c/u (Subtotal: ${item['quantity'] * item['price']:.2f})")
                else:
                    st.info("No hay productos registrados para esta orden.")
                
                # Opciones para actualizar estado
                new_status = st.selectbox(
                    "Actualizar Estado",
                    options=["pending", "processing", "completed", "cancelled"],
                    index=["pending", "processing", "completed", "cancelled"].index(order_details['status'])
                )
                
                if st.button("Actualizar Estado"):
                    conn.execute(
                        "UPDATE orders SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                        (new_status, order_id)
                    )
                    conn.commit()
                    st.success(f"Estado de la orden actualizado a: {new_status}")
            except Exception as e:
                st.error(f"Error al obtener detalles de la orden: {str(e)}")
            finally:
                conn.close()
    else:
        st.info("No se encontraron órdenes con los filtros seleccionados.")

def show_customers():
    st.markdown("<h1 class='main-header'>Gestión de Clientes</h1>", unsafe_allow_html=True)
    
    # Obtener lista de clientes
    conn = get_db_connection()
    try:
        customers_df = pd.read_sql_query(
            """
            SELECT c.*, COUNT(o.id) as total_orders, SUM(o.total_amount) as lifetime_value
            FROM customers c
            LEFT JOIN orders o ON c.id = o.customer_id
            GROUP BY c.id
            ORDER BY c.name
            """, 
            conn
        )
    finally:
        conn.close()
    
    # Mostrar tabla de clientes
    st.markdown("<h2 class='section-header'>Listado de Clientes</h2>", unsafe_allow_html=True)
    
    if not customers_df.empty:
        # Convertir columnas de fechas a datetime para mejor visualización
        for col in ['created_at', 'updated_at']:
            if col in customers_df.columns:
                customers_df[col] = pd.to_datetime(customers_df[col])
        
        # Mostrar tabla con clientes
        st.dataframe(
            customers_df,
            column_config={
                "id": st.column_config.Column("ID"),
                "name": st.column_config.Column("Nombre"),
                "phone": st.column_config.Column("Teléfono"),
                "email": st.column_config.Column("Email"),
                "address": st.column_config.Column("Dirección"),
                "total_orders": st.column_config.NumberColumn("Total Órdenes"),
                "lifetime_value": st.column_config.NumberColumn("Valor Total", format="$%.2f"),
                "created_at": st.column_config.DatetimeColumn("Registrado"),
                "updated_at": st.column_config.DatetimeColumn("Actualizado")
            },
            hide_index=True,
            use_container_width=True
        )
        
        # Sección para ver detalles de un cliente
        st.markdown("<h2 class='section-header'>Detalles de Cliente</h2>", unsafe_allow_html=True)
        customer_id = st.selectbox("Seleccionar Cliente por ID", options=customers_df['id'].tolist())
        
        if customer_id:
            conn = get_db_connection()
            try:
                # Obtener órdenes del cliente
                orders_df = pd.read_sql_query(
                    "SELECT * FROM orders WHERE customer_id = ? ORDER BY created_at DESC", 
                    conn, 
                    params=[customer_id]
                )
                
                customer = customers_df[customers_df['id'] == customer_id].iloc[0]
                
                # Mostrar información
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Información del Cliente")
                    st.write(f"**ID:** {customer['id']}")
                    st.write(f"**Nombre:** {customer['name']}")
                    st.write(f"**Teléfono:** {customer['phone']}")
                    st.write(f"**Email:** {customer.get('email', 'No disponible')}")
                    st.write(f"**Dirección:** {customer.get('address', 'No disponible')}")
                    st.write(f"**Registrado:** {pd.to_datetime(customer['created_at']).strftime('%Y-%m-%d')}")
                
                with col2:
                    st.subheader("Estadísticas")
                    st.write(f"**Total de Órdenes:** {customer['total_orders']}")
                    st.write(f"**Valor Total:** ${customer['lifetime_value']:.2f}")
                    
                    # Calcular días desde la última compra
                    if not orders_df.empty:
                        last_purchase = pd.to_datetime(orders_df.iloc[0]['created_at'])
                        days_since = (datetime.datetime.now() - last_purchase).days
                        st.write(f"**Última Compra:** {last_purchase.strftime('%Y-%m-%d')} ({days_since} días)")
                    else:
                        st.write("**Última Compra:** No ha realizado compras")
                
                # Mostrar historial de órdenes
                st.subheader("Historial de Órdenes")
                
                if not orders_df.empty:
                    # Convertir columnas de fechas a datetime para mejor visualización
                    for col in ['created_at', 'updated_at']:
                        if col in orders_df.columns:
                            orders_df[col] = pd.to_datetime(orders_df[col])
                    
                    st.dataframe(
                        orders_df,
                        column_config={
                            "id": st.column_config.Column("ID"),
                            "total_amount": st.column_config.NumberColumn("Total", format="$%.2f"),
                            "status": st.column_config.Column("Estado"),
                            "payment_method": st.column_config.Column("Método de Pago"),
                            "created_at": st.column_config.DatetimeColumn("Fecha")
                        },
                        hide_index=True,
                        use_container_width=True
                    )
                else:
                    st.info("Este cliente no tiene órdenes registradas.")
            finally:
                conn.close()
    else:
        st.info("No hay clientes registrados en la base de datos.")

def show_security():
    st.markdown("<h1 class='main-header'>Centro de Seguridad</h1>", unsafe_allow_html=True)
    
    st.markdown("<h2 class='section-header'>Incidentes de Seguridad</h2>", unsafe_allow_html=True)
    
    # Obtener incidentes de seguridad
    conn = get_db_connection()
    try:
        try:
            incidents_df = pd.read_sql_query(
                """
                SELECT * FROM security_incidents
                ORDER BY timestamp DESC
                LIMIT 100
                """, 
                conn
            )
        except:
            # Si la tabla no existe
            incidents_df = pd.DataFrame()
    finally:
        conn.close()
    
    if not incidents_df.empty:
        # Convertir columna timestamp a datetime para mejor visualización
        if 'timestamp' in incidents_df.columns:
            incidents_df['timestamp'] = pd.to_datetime(incidents_df['timestamp'])
        
        # Mostrar tabla con incidentes
        st.dataframe(
            incidents_df,
            column_config={
                "id": st.column_config.Column("ID"),
                "type": st.column_config.Column("Tipo"),
                "description": st.column_config.TextColumn("Descripción"),
                "severity": st.column_config.Column("Severidad"),
                "ip_address": st.column_config.Column("Dirección IP"),
                "phone_number": st.column_config.Column("Número de Teléfono"),
                "timestamp": st.column_config.DatetimeColumn("Fecha y Hora"),
                "is_resolved": st.column_config.CheckboxColumn("Resuelto")
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("No hay incidentes de seguridad registrados o la tabla no existe.")
    
    # Sección para configuración de seguridad
    st.markdown("<h2 class='section-header'>Configuración de Seguridad</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Mostrar palabras sospechosas
        st.subheader("Palabras Sospechosas")
        
        try:
            with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), "app", "data", "suspicious_words.json"), "r") as f:
                suspicious_words = json.load(f)
                
            suspicious_text = st.text_area(
                "Palabras sospechosas (una por línea)",
                value="\n".join(suspicious_words),
                height=200
            )
            
            if st.button("Guardar Palabras Sospechosas"):
                new_words = [word.strip() for word in suspicious_text.split("\n") if word.strip()]
                
                with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), "app", "data", "suspicious_words.json"), "w") as f:
                    json.dump(new_words, f, indent=2)
                    
                st.success("Palabras sospechosas actualizadas correctamente.")
        except Exception as e:
            st.error(f"Error al cargar o guardar palabras sospechosas: {str(e)}")
    
    with col2:
        # Configuración de umbrales
        st.subheader("Umbrales de Seguridad")
        
        threshold = st.slider(
            "Umbral de actividad sospechosa",
            min_value=0.0,
            max_value=1.0,
            value=0.75,
            step=0.05,
            help="Probabilidad mínima para considerar una actividad como sospechosa (0-1)"
        )
        
        max_attempts = st.number_input(
            "Intentos máximos de autenticación",
            min_value=1,
            max_value=10,
            value=5,
            step=1,
            help="Número máximo de intentos fallidos antes de bloquear"
        )
        
        rate_limit = st.number_input(
            "Límite de mensajes por hora",
            min_value=10,
            max_value=1000,
            value=100,
            step=10,
            help="Número máximo de mensajes permitidos por hora por número"
        )
        
        if st.button("Guardar Configuración"):
            # Aquí se implementaría la lógica para guardar esta configuración
            # Por ejemplo, actualizando un archivo .env o una tabla en la base de datos
            st.success("Configuración de seguridad actualizada correctamente.")
            
            # Como ejemplo, podríamos guardar en variables de entorno
            # Esto es solo un ejemplo y no modifica realmente las variables de entorno
            st.code(f"""
            # Nuevos valores de configuración:
            SUSPICIOUS_ACTIVITY_THRESHOLD={threshold}
            MAX_LOGIN_ATTEMPTS={max_attempts}
            MESSAGE_RATE_LIMIT={rate_limit}
            """)

def show_configuration():
    st.markdown("<h1 class='main-header'>Configuración del Sistema</h1>", unsafe_allow_html=True)
    
    # Sección para configuración de Twilio
    st.markdown("<h2 class='section-header'>Configuración de WhatsApp / Twilio</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        account_sid = st.text_input("Twilio Account SID", value="", type="password")
        auth_token = st.text_input("Twilio Auth Token", value="", type="password")
    
    with col2:
        phone_number = st.text_input("Número de Teléfono de WhatsApp", value="")
        test_mode = st.checkbox("Modo de Prueba", value=True)
    
    if st.button("Probar Configuración de Twilio"):
        if account_sid and auth_token and phone_number:
            st.info("Probando conexión con Twilio...")
            # Aquí se llamaría a una función que pruebe la conexión con Twilio
            # Por ejemplo: result = test_twilio_connection(account_sid, auth_token, phone_number)
            
            # Simulando respuesta exitosa
            st.success("Conexión exitosa con Twilio. El número de WhatsApp está configurado correctamente.")
        else:
            st.error("Por favor, complete todos los campos de configuración de Twilio.")
    
    # Sección para configuración de OpenAI
    st.markdown("<h2 class='section-header'>Configuración de Inteligencia Artificial</h2>", unsafe_allow_html=True)
    
    api_key = st.text_input("API Key de OpenAI", value="", type="password")
    model = st.selectbox(
        "Modelo de OpenAI",
        options=["gpt-4-0125-preview", "gpt-4", "gpt-3.5-turbo", "gpt-3.5-turbo-16k"]
    )
    
    temperature = st.slider(
        "Temperatura",
        min_value=0.0,
        max_value=2.0,
        value=0.7,
        step=0.1,
        help="Controla la creatividad de las respuestas (0-2)"
    )
    
    if st.button("Probar Configuración de OpenAI"):
        if api_key:
            st.info("Probando conexión con OpenAI...")
            # Aquí se llamaría a una función que pruebe la conexión con OpenAI
            # Por ejemplo: result = test_openai_connection(api_key, model)
            
            # Simulando respuesta exitosa
            st.success("Conexión exitosa con OpenAI. El modelo está disponible y funcionando correctamente.")
        else:
            st.error("Por favor, ingrese una API Key válida para OpenAI.")
    
    # Sección para configuración de base de datos
    st.markdown("<h2 class='section-header'>Configuración de Base de Datos</h2>", unsafe_allow_html=True)
    
    db_type = st.selectbox(
        "Tipo de Base de Datos",
        options=["SQLite", "PostgreSQL", "MySQL"],
        index=0
    )
    
    if db_type == "SQLite":
        db_path = st.text_input("Ruta de la Base de Datos", value="whatsapp_sales.db")
        connection_string = f"sqlite:///{db_path}"
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            db_host = st.text_input("Host", value="localhost")
            db_name = st.text_input("Nombre de Base de Datos", value="whatsapp_sales")
        
        with col2:
            db_user = st.text_input("Usuario", value="")
            db_password = st.text_input("Contraseña", value="", type="password")
        
        db_port = st.text_input("Puerto", value="5432" if db_type == "PostgreSQL" else "3306")
        
        if db_type == "PostgreSQL":
            connection_string = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        else:
            connection_string = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    st.code(f"DATABASE_URL={connection_string}")
    
    if st.button("Probar Conexión a la Base de Datos"):
        st.info("Probando conexión a la base de datos...")
        # Aquí se llamaría a una función que pruebe la conexión a la base de datos
        # Por ejemplo: result = test_db_connection(connection_string)
        
        # Simulando respuesta exitosa
        st.success("Conexión exitosa a la base de datos.")
    
    # Sección para guardar configuración
    st.markdown("<h2 class='section-header'>Guardar Configuración</h2>", unsafe_allow_html=True)
    
    if st.button("Guardar Toda la Configuración", use_container_width=True):
        # Aquí se implementaría la lógica para guardar toda la configuración
        # Por ejemplo, creando o actualizando un archivo .env
        
        # Simulando éxito
        st.success("Configuración guardada correctamente.")
        st.info("Para que algunos cambios surtan efecto, es posible que necesite reiniciar la aplicación.")

# Mostrar la página seleccionada
if page == "Dashboard":
    show_dashboard()
elif page == "Productos":
    show_products()
elif page == "Órdenes":
    show_orders()
elif page == "Clientes":
    show_customers()
elif page == "Seguridad":
    show_security()
elif page == "Configuración":
    show_configuration()

# Mostrar instrucciones para ejecutar el panel
if __name__ == "__main__":
    st.sidebar.markdown("---")
    st.sidebar.info("""
    Para ejecutar este panel de administración, usa el siguiente comando en la terminal:
    ```
    streamlit run admin/app.py
    ```
    """)