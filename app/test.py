import os
import streamlit as st
from breadcrumbs import generate_folder_tree
from streamlit_tree_select import tree_select
from utils import Utils
from dotenv import load_dotenv
from PIL import Image   
from streamlit_paste_button import paste_image_button as pbutton
from embeddings import Embedder
from langchain_community.chat_models import ChatOpenAI
from langchain_community.embeddings import OpenAIEmbeddings
import traceback
from datetime import datetime
from openai import OpenAI
import base64
import io
from pathlib import Path
import time
import json
import plotly.express as px
import streamlit.components.v1 as components
 
st.set_page_config(page_title="Ingenium", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    /* DataBrain Brand Colors */
    [data-theme="light"] {
        --db-primary: #1A1B4B;      /* Deep Space */
        --db-accent1: #00F0FF;      /* Electric Blue */
        --db-accent2: #B94FFF;      /* Neon Purple */
        --db-surface: #FFFFFF;      /* Pure White */
        --db-text: #0D0D2B;         /* Rich Black */
        --db-gradient-main: linear-gradient(135deg, #1A1B4B, #0D0D2B);
        --db-gradient-accent: linear-gradient(45deg, #00F0FF, #B94FFF);
        --db-gradient-surface: linear-gradient(135deg, rgba(255,255,255,0.9), rgba(255,255,255,0.95));
    }

    [data-theme="dark"] {
        --db-primary: #2A2B6B;      /* Lighter Deep Space */
        --db-accent1: #33F2FF;      /* Brighter Electric Blue */
        --db-accent2: #C67FFF;      /* Lighter Neon Purple */
        --db-surface: #0D0D2B;      /* Rich Black */
        --db-text: #FFFFFF;         /* Pure White */
        --db-gradient-main: linear-gradient(135deg, #2A2B6B, #1A1B4B);
        --db-gradient-accent: linear-gradient(45deg, #33F2FF, #C67FFF);
        --db-gradient-surface: linear-gradient(135deg, rgba(13,13,43,0.9), rgba(13,13,43,0.95));
    }

    /* Futuristic Interface Elements */
    .stApp {
        background: var(--db-gradient-main) !important;
    }

    /* Modern Cards with Glassmorphism */
    .db-card {
        background: var(--db-gradient-surface);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 15px;
        padding: 1.5rem;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }

    /* Tech-inspired Metrics */
    .metric-container {
        background: var(--db-gradient-surface);
        border-left: 4px solid var(--db-accent1);
        padding: 1.5rem;
        border-radius: 12px;
        transition: transform 0.3s ease;
        color: var(--db-text);
    }
    
    .metric-container:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 30px rgba(0,240,255,0.15);
    }

    /* Futuristic Buttons */
    .stButton>button {
        background: var(--db-gradient-accent) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        box-shadow: 0 4px 15px rgba(0,240,255,0.2);
        transition: all 0.3s ease !important;
        padding: 0.5rem 1rem !important;
    }

    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(185,79,255,0.3);
    }

    /* Modern Navigation */
    .stTabs [data-baseweb="tab-list"] {
        background: var(--db-gradient-surface);
        padding: 0.5rem;
        border-radius: 10px;
        backdrop-filter: blur(5px);
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        color: var(--db-text);
        transition: all 0.3s ease;
    }

    /* Sidebar Styling */
    .css-1d391kg {
        background: var(--db-gradient-main) !important;
    }

    .sidebar .sidebar-content {
        background: var(--db-gradient-main);
    }

    /* Input Fields */
    .stTextInput>div>div>input,
    .stSelectbox>div>div {
        background-color: var(--db-surface) !important;
        color: var(--db-text) !important;
        border-radius: 8px !important;
    }

    /* Headers and Text */
    h1, h2, h3 {
        color: var(--db-accent1) !important;
    }

    p {
        color: var(--db-text);
    }

    /* Chat Interface */
    .element-container .stChatMessage {
        background: var(--db-gradient-surface);
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
    }

    /* Custom Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }

    ::-webkit-scrollbar-track {
        background: var(--db-surface);
    }

    ::-webkit-scrollbar-thumb {
        background: var(--db-gradient-accent);
        border-radius: 4px;
    }

    /* Charts and Plots */
    .stPlot {
        background: var(--db-gradient-surface);
        border-radius: 12px;
        padding: 1rem;
    }

    /* Additional UI Enhancements */
    .uploadedFile {
        background-color: var(--db-surface);
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        border: 1px solid var(--db-accent1);
    }

    .custom-sidebar {
        background: var(--db-gradient-main);
        padding: 1rem;
    }

    .import-window {
        background: var(--db-gradient-surface);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 2rem;
        margin: 1rem 0;
        border: 1px solid rgba(255,255,255,0.1);
    }

    /* Status Messages */
    .stSuccess {
        background: linear-gradient(135deg, rgba(0,240,255,0.1), rgba(185,79,255,0.1));
        border: 1px solid var(--db-accent1);
        color: var(--db-text);
    }

    .stError {
        background: linear-gradient(135deg, rgba(255,79,79,0.1), rgba(255,79,79,0.05));
        border: 1px solid #ff4f4f;
        color: var(--db-text);
    }
</style>
""", unsafe_allow_html=True)



def verify_credentials():
    credentials_status = {
        
        'OPENAI_API_KEY': bool(os.getenv('OPENAI_API_KEY'))
    }
    return all(credentials_status.values()), credentials_status

    
utils = Utils(st)

#SAVING CREDENTIALS

try:
    load_dotenv()
    print("Environment variables loaded from .env file")
except Exception as e:
    print(f"Could not load .env file: {str(e)}")

if 'OPENAI_API_KEY' not in st.session_state:
    st.session_state.OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
if 'sidebar_expanded' not in st.session_state:
    st.session_state.sidebar_expanded = True
if "messages" not in st.session_state:
    st.session_state.messages = []
if 'show_import_window' not in st.session_state:
    st.session_state.show_import_window = False
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Dashboard"

menu_items = {
    "Dashboard": "📊",
    "Análisis Exploratorio": "📈",
    "Predicciones": "🔮",
    "Machine Learning": "🤖",
    "Reportes": "📑",
    "Configuración": "⚙️"
}

if 'import_window_state' not in st.session_state:
    st.session_state.import_window_state = False

if "embedder" not in st.session_state:
    print("Initializing embedder...")
    try:
        st.session_state.embedder = Embedder(st)
        st.session_state.embedder.model = ChatOpenAI(
            model_name="gpt-4o",
            temperature=0.7,
            max_tokens=2000
        )
        st.session_state.embedder.hf = OpenAIEmbeddings()
        print("Embedder initialized correctly")
    except Exception as e:
        print(f"Error initializing embedder: {str(e)}")



def check_openai_credentials():
    return bool(os.getenv('OPENAI_API_KEY') or st.session_state.get('OPENAI_API_KEY'))

def show_credentials_modal():
    with st.sidebar.expander("🔑 API Credentials Setup", expanded=True):
        st.markdown("""
        ### Get your API Keys
        
        1. [Get Atlassian API Token](https://id.atlassian.com/manage-profile/security/api-tokens)
        2. [Get OpenAI API Key](https://platform.openai.com/api-keys)
        """)
        
        openai_key = st.text_input("OpenAI API Key", 
                                  type="password", 
                                  value=st.session_state.get('OPENAI_API_KEY', ''),
                                  key="openai_key_input")
        #SAVING CREDENTIALS
        if st.button("Save Credentials", key="save_credentials_button"):
            st.session_state.OPENAI_API_KEY = openai_key
            
            try:
                with open('.env', 'w') as f:
                    st.success("Credentials saved successfully!")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Error saving credentials: {str(e)}")


# Check required environment variables
required_env_vars = {
    'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY')
}

missing_vars = [var for var, value in required_env_vars.items() if not value]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")


# Main layout
container = st.container()

# Dynamic column structure
if st.session_state.sidebar_expanded:
    main_col, right_sidebar_col = st.columns([3, 2])  # Cambiado de [4, 1] a [3, 2]
else:
    main_col, right_sidebar_col = st.columns([19, 1])


# Estilos CSS personalizados
st.markdown("""
<style>
    .css-18e3th9 {
        padding: 1rem 5rem 10rem;
    }
    .css-1d391kg {
        padding: 1rem 1rem;
    }
    .stButton>button {
        width: 100%;
    }
    .uploadedFile {
        background-color: #f0f2f6;
        border-radius: 5px;
        padding: 10px;
        margin: 5px 0;
    }
    .custom-sidebar {
        padding: 1rem;
    }
    .sidebar-header {
        margin-bottom: 2rem;
    }
    .sidebar-section {
        margin-bottom: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Layout principal
st.markdown("""
<style>
    .main-container {
        padding: 2rem;
    }
    .import-window {
        background-color: #262730;
        padding: 2rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar izquierdo
def toggle_import_window():
    st.session_state.import_window_state = not st.session_state.import_window_state

def render_page(page_name):
    if page_name == "Dashboard":
        # Código existente del Dashboard
        col1, col2, col3 = st.columns(3)
        with col1:
            st.date_input("Rango de Fechas", value=[])
        with col2:
            st.multiselect("Categorías", ["Categoría 1", "Categoría 2", "Categoría 3"])
        with col3:
            st.selectbox("Segmento", ["Todos", "Segmento A", "Segmento B", "Segmento C"])

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown("""
                <div class='metric-container'>
                    <h3>Ventas Totales</h3>
                    <h2>$1.2M</h2>
                    <p style='color: var(--db-accent1);'>↑ 12%</p>
                </div>
            """, unsafe_allow_html=True)

    elif page_name == "Análisis Exploratorio":
        st.markdown("""
            <div class='db-card'>
                <h2>📊 Análisis de Variables</h2>
            </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.selectbox("Variable X", ["Ventas", "Costos", "Tiempo", "Región"])
        with col2:
            st.selectbox("Variable Y", ["Beneficios", "Unidades", "Crecimiento", "Categoría"])

    elif page_name == "Predicciones":
        st.markdown("""
            <div class='db-card'>
                <h2>🔮 Pronósticos y Proyecciones</h2>
            </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.selectbox("Modelo de Predicción", ["Regresión Lineal", "ARIMA", "Prophet"])
        with col2:
            st.number_input("Horizonte de Predicción", min_value=1, value=30)

    elif page_name == "Machine Learning":
        st.markdown("""
            <div class='db-card'>
                <h2>🤖 Modelos de Machine Learning</h2>
            </div>
        """, unsafe_allow_html=True)
        
        st.selectbox("Tipo de Modelo", ["Clasificación", "Regresión", "Clustering"])

    elif page_name == "Reportes":
        st.markdown("""
            <div class='db-card'>
                <h2>📑 Generación de Informes</h2>
            </div>
        """, unsafe_allow_html=True)
        
        st.selectbox("Tipo de Reporte", ["Ejecutivo", "Detallado", "Personalizado"])

    elif page_name == "Configuración":
        st.markdown("""
            <div class='db-card'>
                <h2>⚙️ Configuración del Sistema</h2>
            </div>
        """, unsafe_allow_html=True)
        
        st.toggle("Modo Oscuro")
        st.selectbox("Idioma", ["Español", "English", "Português"])

with st.sidebar:
    st.markdown("""
        <div class='db-card'>
            <h1>DataBrain</h1>
            <p>Su Agente de AI les da la bienvenida</p>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    # Generar botones de navegación
    for page, icon in menu_items.items():
        is_active = st.session_state.current_page == page
        if st.sidebar.button(
            f"{icon} {page}",
            key=f"nav_{page}",
            use_container_width=True,
            type="primary" if is_active else "secondary"
        ):
            st.session_state.current_page = page
            st.rerun()

    st.markdown("---")
    st.markdown("### 📊 Datos")
    if st.button(
        "📁 Cargar Bases de Datos",
        key="load_data_btn",
        use_container_width=True
    ):
        st.session_state.import_window_state = not st.session_state.import_window_state

with main_col:
    if st.session_state.import_window_state:
        # Ventana de importación
        st.header("🔄 Importar Datos")
        
        # Botón de cierre
        if st.button("✖️", key="close_btn"):
            st.session_state.import_window_state = False
        
        # Pestañas de importación
        tabs = st.tabs(["📂 Archivos", "☁️ AWS", "🗄️ SQL", "📝 Manual"])
        
        # Pestaña de Archivos
        with tabs[0]:
            st.markdown("### Cargar Archivos Locales")
            uploaded_files = st.file_uploader(
                "Arrastra tus archivos aquí",
                accept_multiple_files=True,
                type=['csv', 'xlsx', 'xls', 'json', 'sql', 'txt'],
                key="file_uploader_main"
            )
            if uploaded_files:
                for file in uploaded_files:
                    st.success(f"✅ {file.name} cargado")

        # Pestaña AWS
        with tabs[1]:
            st.markdown("### Configuración AWS")
            col1, col2 = st.columns(2)
            with col1:
                st.text_input("Access Key ID", key="aws_key")
            with col2:
                st.text_input("Secret Access Key", type="password", key="aws_secret")
            st.text_input("Bucket", key="aws_bucket")

        # Pestaña SQL
        with tabs[2]:
            st.markdown("### Conectar Base de Datos SQL")
            st.selectbox("Tipo de Base de Datos", 
                ["PostgreSQL", "MySQL", "SQL Server", "Oracle"],
                key="db_type_select")
            col1, col2 = st.columns(2)
            with col1:
                st.text_input("Servidor", key="server_input")
                st.text_input("Usuario", key="user_input")
            with col2:
                st.text_input("Puerto", key="port_input")
                st.text_input("Contraseña", type="password", key="password_input")

        # Pestaña Manual
        with tabs[3]:
            st.markdown("### Ingresar Datos Manualmente")
            col1, col2 = st.columns(2)
            with col1:
                rows = st.number_input("Filas", min_value=1, value=5, key="rows_input")
            with col2:
                cols = st.number_input("Columnas", min_value=1, value=3, key="cols_input")

            if st.button("Crear Tabla", key="create_table_btn"):
                for i in range(int(rows)):
                    cols_data = st.columns(int(cols))
                    for j in range(int(cols)):
                        with cols_data[j]:
                            st.text_input(f"Dato [{i+1},{j+1}]", key=f"cell_{i}_{j}")

        # Botones de acción
        st.markdown("---")
        col1, col2, col3 = st.columns([6,2,2])
        with col2:
            if st.button("Cancelar", key="cancel_import"):
                st.session_state.import_window_state = False
        with col3:
            if st.button("Importar", type="primary", key="confirm_import"):
                st.success("✅ Datos importados exitosamente")
                st.session_state.import_window_state = False

    if st.session_state.current_page == "Dashboard":
        st.markdown("""
            <div class='db-card'>
                <h2>📊 Dashboard Principal</h2>
            </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.date_input("Rango de Fechas", value=[], key="dashboard_date")
        with col2:
            st.multiselect("Categorías", ["Categoría 1", "Categoría 2", "Categoría 3"], key="dashboard_categories")
        with col3:
            st.selectbox("Segmento", ["Todos", "Segmento A", "Segmento B", "Segmento C"], key="dashboard_segment")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown("""
                <div class='metric-container'>
                    <h3>Ventas Totales</h3>
                    <h2>$1.2M</h2>
                    <p style='color: var(--db-accent1);'>↑ 12%</p>
                </div>
            """, unsafe_allow_html=True)

    elif st.session_state.current_page == "Análisis Exploratorio":
        st.markdown("""
            <div class='db-card'>
                <h2>📈 Análisis Exploratorio de Datos</h2>
            </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.selectbox("Variable X", ["Ventas", "Costos", "Tiempo", "Región"], key="analysis_var_x")
        with col2:
            st.selectbox("Variable Y", ["Beneficios", "Unidades", "Crecimiento", "Categoría"], key="analysis_var_y")

    elif st.session_state.current_page == "Predicciones":
        st.markdown("""
            <div class='db-card'>
                <h2>🔮 Sistema de Predicciones</h2>
            </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.selectbox("Modelo de Predicción", ["Regresión Lineal", "ARIMA", "Prophet"], key="pred_model")
        with col2:
            st.number_input("Horizonte de Predicción", min_value=1, value=30, key="pred_horizon")

    elif st.session_state.current_page == "Machine Learning":
        st.markdown("""
            <div class='db-card'>
                <h2>🤖 Laboratorio de Machine Learning</h2>
            </div>
        """, unsafe_allow_html=True)
        
        st.selectbox("Tipo de Modelo", ["Clasificación", "Regresión", "Clustering"], key="ml_model_type")

    elif st.session_state.current_page == "Reportes":
        st.markdown("""
            <div class='db-card'>
                <h2>📑 Sistema de Reportes</h2>
            </div>
        """, unsafe_allow_html=True)
        
        st.selectbox("Tipo de Reporte", ["Ejecutivo", "Detallado", "Personalizado"], key="report_type")

    elif st.session_state.current_page == "Configuración":
        st.markdown("""
            <div class='db-card'>
                <h2>⚙️ Panel de Configuración</h2>
            </div>
        """, unsafe_allow_html=True)
        
        st.toggle("Modo Oscuro", key="dark_mode")
        st.selectbox("Idioma", ["Español", "English", "Português"], key="language")


with right_sidebar_col:
    # Toggle button
    toggle_button = st.button(
        "❯" if st.session_state.sidebar_expanded else "❮",
        help="Toggle sidebar",
        key="toggle_sidebar",
        use_container_width=True
    )
 
    if toggle_button:
        st.session_state.sidebar_expanded = not st.session_state.sidebar_expanded
        st.rerun()

    # Contents when expanded
    if st.session_state.sidebar_expanded:
        st.markdown("### Chat Interface")
        
        # Mostrar historial de mensajes
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Chat input
        if prompt := st.chat_input("Type your message here..."):
            if check_openai_credentials():
                # Mostrar mensaje del usuario
                with st.chat_message("user"):
                    st.markdown(prompt)
                
                try:
                    # Procesar la respuesta
                    response = utils.process_query(prompt, mode="chat")
                    
                    # Mostrar respuesta del asistente
                    with st.chat_message("assistant"):
                        st.markdown(response)
                    
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error: {str(e)}")
            else:
                st.error("Please configure OpenAI credentials")

    else:
        st.markdown("↔")