import pandas as pd
import folium
import random
import streamlit as st
from shapely import wkt
from shapely.geometry import Point
from folium.plugins import HeatMap
from folium.features import DivIcon

# Configurar el modo amplio de Streamlit
st.set_page_config(layout="wide")

st.image("PBI BP Azul.png", use_container_width=True, output_format="PNG")
st.markdown(
    """
    <style>
        .title {
            text-align: center;
            margin-top: -50px;
            font-size: 36px;
            font-weight: bold;
        }
        [data-testid="stSidebar"] {
            background-color: #1B2D54;
        }
        [data-testid="stSidebar"] * {
            color: #CDCDCD;
        }
        .metric-card {
            background-color: #1B2D54;
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            font-size: 20px;
            font-weight: bold;
            margin: 10px;
        }
        .dataframe-header {
            background-color: #0078D4 !important;
            color: white !important;
            text-align: center !important;
            font-weight: bold !important;
        }
        img {
            height: 75px !important;
            float: left;
            object-fit: contain;
            background-color: #1B2D54;
        }
    </style>
    
    """,
    unsafe_allow_html=True
)

# Configurar diseño con una barra lateral
with st.sidebar:
    st.subheader("Sube tus archivos")
    # Subir archivo CSV para geolocalización
    uploaded_file = st.file_uploader("Geolocalizaciones .csv", type=["csv"])

    # Subir archivo XLSX para polígonos
    polygon_file = st.file_uploader("Poligonos .xlsx", type=["xlsx"])

if uploaded_file:
    # Leer el archivo CSV
    df = pd.read_csv(uploaded_file)

    # Verificar si existe la columna 'geolocation'
    if 'geolocation' in df.columns:
        # Convertir la columna de geolocalización en dos columnas separadas (latitud y longitud)
        df[['latitude', 'longitude']] = df['geolocation'].str.split(',', expand=True).astype(float)

        # Convertir la columna 'fecha' a solo fecha
        df['fecha'] = pd.to_datetime(df['fecha']).dt.date

        # Ordenar los datos por identificación del cliente, fecha y hora
        df = df.sort_values(by=['identification', 'fecha', 'hora'])

        # Combobox para seleccionar la identificación
        identificaciones = df['identification'].unique()
        st.subheader("Selecciona una identificación para actualizar el mapa")
        seleccion_identificacion = st.selectbox("", identificaciones, key="identificacion_selector")

        # Filtrar los datos según la identificación seleccionada
        cliente_data = df[df['identification'] == seleccion_identificacion]

        # Crear el mapa centrado en los puntos de la identificación seleccionada
        mapa = folium.Map(location=[cliente_data['latitude'].mean(), cliente_data['longitude'].mean()], zoom_start=12)

        # Generar una lista de colores para los puntos
        colors = ["black"]

        # Seleccionar un color aleatorio para la identificación
        color = random.choice(colors)

        # Agregar puntos y línea al mapa
        puntos = list(zip(cliente_data['latitude'], cliente_data['longitude'], cliente_data['fecha'], cliente_data['hora'], cliente_data['monto']))

        # Crear tres columnas para métricas
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(
                f"""
                <div class="metric-card">
                    Cliente<br>
                    {seleccion_identificacion}
                </div>
                """,
                unsafe_allow_html=True
            )

        with col2:
            session_count = cliente_data['session'].nunique()
            st.markdown(
                f"""
                <div class="metric-card">
                    Inicios de Sesión Únicos<br>
                    {session_count}
                </div>
                """,
                unsafe_allow_html=True
            )

        with col3:
            total_monto = cliente_data['monto'].sum()
            st.markdown(
                f"""
                <div class="metric-card">
                    Total Monto Transaccionado<br>
                    ${total_monto:,.2f}
                </div>
                """,
                unsafe_allow_html=True
            )

        for idx, (lat, lon, fecha, hora, monto) in enumerate(puntos, start=1):
            popup_text = f"<b>Orden:</b> {idx}<br>Fecha: {fecha}<br>Hora: {hora}<br>Monto: ${monto}"
            folium.Marker(
                location=(lat, lon),
                popup=popup_text,
                icon=DivIcon(
                    icon_size=(40, 40),
                    icon_anchor=(20, 20),
                    html=f'<div style="width: 40px; height: 40px; background: #1B2D54; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 14pt; font-weight: bold;">{idx}</div>'
                )
            ).add_to(mapa)

        # Agregar línea entre los puntos
        if len(puntos) > 1:
            trayectoria = [(lat, lon) for lat, lon, fecha, hora, monto in puntos]
            folium.PolyLine(trayectoria, color=color, weight=2.5, opacity=0.7).add_to(mapa)

        # Agregar gráfico de calor al mapa
        heat_data = cliente_data[['latitude', 'longitude']].values.tolist()
        HeatMap(heat_data, radius=10).add_to(mapa)

        # Crear dos columnas: el mapa más grande
        col_mapa, col_tabla = st.columns([2, 1])

        with col_mapa:
            # Mostrar el mapa
            st.subheader("Mapa Geolocalizacion")
            st.components.v1.html(mapa._repr_html_(), height=600)

        with col_tabla:
            # Mostrar la tabla detallada con la información de la identificación seleccionada
            st.subheader("Detalles del Cliente")
            st.markdown(
                cliente_data[['fecha', 'hora', 'monto']]
                .style.set_table_styles([
                    {"selector": "thead th", "props": [
                        ("background-color", "#1B2D54"),
                        ("color", "white"),
                        ("text-align", "center")
                    ]},
                    {"selector": "tbody td", "props": [
                        ("text-align", "center")
                    ]}
                ]).to_html(),
                unsafe_allow_html=True
            )
    else:
        st.error("El archivo CSV debe tener una columna llamada 'geolocation'")
