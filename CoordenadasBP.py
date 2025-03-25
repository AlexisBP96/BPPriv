import pandas as pd
import folium
import random
import streamlit as st
from PIL import Image
from shapely import wkt
from shapely.geometry import Point
from folium.features import DivIcon
from folium.plugins import HeatMap
import matplotlib.pyplot as plt
import io 
import base64
from io import BytesIO

st.set_page_config(layout="wide")

# Mostrar el logo con clase específica
# st.image("assets/PBI BP Azul.png", output_format="PNG", use_container_width=True)
image = Image.open("assets/PBI BP Azul.png")

# Convierte la imagen a base64
buffered = BytesIO()
image.save(buffered, format="PNG")
img_base64 = base64.b64encode(buffered.getvalue()).decode()

# HTML + CSS para mostrar la imagen con estilo
st.markdown(
    f"""
    <style>
        .custom-img {{
            width: 100%;
            max-height: 75px !important;
            height: auto;
            border-radius: 15px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.3);
            margin: 20px auto;
            display: block;
            background-color: #1B2D54
        }}
    </style>
    <img src="data:image/png;base64,{img_base64}" class="custom-img" />
    """,
    unsafe_allow_html=True
)
# Estilos
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
        img {
            height: 560px !important;
            object-fit: contain;
        }
        .scrollable-table {
            height: 560px;
            overflow-y: scroll;
            display: block;
            border: 1px solid #ccc;
        }
        .scrollable-table table {
            border-collapse: collapse;
            width: 100%;
        }
        .scrollable-table table th {
            background-color: #1B2D54;
            color: white;
            text-align: center;
            position: sticky;
            top: 0;
            z-index: 2;
        }
        .scrollable-table table td {
            text-align: center;
        }
    </style>
    """,
    unsafe_allow_html=True
)

with st.sidebar:
    st.subheader("Sube tus archivos")
    uploaded_file = st.file_uploader("Geolocalizaciones .csv", type=["csv"])
    polygon_file = st.file_uploader("Poligonos .xlsx", type=["xlsx"])

polygons = None

if polygon_file:
    polygon_data = pd.read_excel(polygon_file)
    if 'POLIGONO' in polygon_data.columns and 'Segmentacion' in polygon_data.columns and 'NOMBRE' in polygon_data.columns:
        polygon_data['geometry'] = polygon_data['POLIGONO'].apply(wkt.loads)
        polygons = {
            row['NOMBRE']: (row['geometry'], row['Segmentacion']) for _, row in polygon_data.iterrows()
        }

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    if 'geolocation' in df.columns:
        df[['latitude', 'longitude']] = df['geolocation'].str.split(',', expand=True).astype(float)
        df['fecha'] = pd.to_datetime(df['fecha']).dt.date
        df = df.sort_values(by=['identification', 'fecha', 'hora'])

        if polygons:
            def get_polygon_name(lat, lon):
                point = Point(lon, lat)
                for name, (poly, segmentacion) in polygons.items():
                    if poly.contains(point):
                        return name
                return 'Fuera de Polígonos'

            df['Sitio'] = df.apply(lambda row: get_polygon_name(row['latitude'], row['longitude']), axis=1)

        identificaciones = df['cliente'].unique()

        col_cliente, col_fecha = st.columns([1, 1])

        with col_cliente:
            st.markdown("#### Cliente")
            seleccion_identificacion = st.selectbox("", identificaciones, key="identificacion_selector")

        with col_fecha:
            cliente_data_temp = df[df['cliente'] == seleccion_identificacion]
            min_fecha = cliente_data_temp['fecha'].min()
            max_fecha = cliente_data_temp['fecha'].max()
            st.markdown("#### Fechas")
            fecha_inicio, fecha_fin = st.date_input(
                "",
                value=(min_fecha, max_fecha),
                min_value=min_fecha,
                max_value=max_fecha,
                key="fecha_selector"
            )

        cliente_data = df[
            (df['cliente'] == seleccion_identificacion) &
            (df['fecha'] >= fecha_inicio) & (df['fecha'] <= fecha_fin)
        ]

        mapa = folium.Map(location=[cliente_data['latitude'].mean(), cliente_data['longitude'].mean()], zoom_start=12)
        color = "black"
        puntos = list(zip(cliente_data['latitude'], cliente_data['longitude'], cliente_data['fecha'], cliente_data['hora'], cliente_data['monto']))

        col1, col2, col3, col4 = st.columns(4)

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

        with col4:
            ultimo = cliente_data[['fecha', 'hora']].sort_values(by=['fecha', 'hora'], ascending=False).head(1)
            texto = f"{ultimo['fecha'].values[0]} - {int(ultimo['hora'].values[0])}h" if not ultimo.empty else "Sin datos"
            st.markdown(
                f"""
                <div class="metric-card">
                    Último Inicio de Sesión<br>
                    {texto}
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

        if len(puntos) > 1:
            trayectoria = [(lat, lon) for lat, lon, fecha, hora, monto in puntos]
            folium.PolyLine(trayectoria, color=color, weight=2.5, opacity=0.7).add_to(mapa)

        if polygons:
            for name, (poly, segmentacion) in polygons.items():
                color = "red" if segmentacion == "Riesgo" else "blue"
                folium.Polygon(
                    locations=[(point[1], point[0]) for point in poly.exterior.coords],
                    color=color,
                    weight=2,
                    opacity=0.7,
                    fill=True,
                    fill_color=color,
                    fill_opacity=0.3,
                    popup=f"{name} ({segmentacion})"
                ).add_to(mapa)

        col_geo, col_bar = st.columns([2, 1])

        with col_geo:
            st.subheader("Mapa Geolocalizacion")
            st.components.v1.html(mapa._repr_html_(), height=560)

        with col_bar:
            st.subheader("Accesos por Hora del Día")

            hora_count = cliente_data['hora'].value_counts().sort_index()
            fig, ax = plt.subplots(figsize=(6, 4))
            ax.bar(hora_count.index, hora_count.values, color='#1B2D54')
            ax.set_xlabel('Hora del Día')
            ax.set_ylabel('Cantidad de Accesos')
            ax.set_title('Distribución de Accesos por Hora')

            # Convertir la figura a base64
            buf = io.BytesIO()
            fig.savefig(buf, format="png", bbox_inches="tight")
            buf.seek(0)
            image_base64 = base64.b64encode(buf.read()).decode("utf-8")

            # Insertar imagen con clase personalizada
            st.markdown(
                f"""
                <div>
                    <img src="data:image/png;base64,{image_base64}" class="bar-plot-img">
                </div>
                """,
                unsafe_allow_html=True
            )

        col_mapa_calor, col_tabla = st.columns([2, 1])

        with col_mapa_calor:
            st.subheader("Mapa de Calor de Accesos del Cliente")
            mapa_calor = folium.Map(location=[cliente_data['latitude'].mean(), cliente_data['longitude'].mean()], zoom_start=12)
            heat_data = cliente_data[['latitude', 'longitude']].values.tolist()
            HeatMap(heat_data).add_to(mapa_calor)
            st.components.v1.html(mapa_calor._repr_html_(), height=560)

        with col_tabla:
            st.subheader("Detalles del Cliente")
            cliente_data['monto'] = cliente_data['monto'].round(2)
            if 'Sitio' in cliente_data.columns:
                cliente_data_display = cliente_data[['fecha', 'hora', 'monto', 'Sitio']]
            else:
                cliente_data_display = cliente_data[['fecha', 'hora', 'monto']]

            st.markdown(
                f"""
                <div class="scrollable-table">
                    {cliente_data_display.to_html(index=False, classes='table table-bordered')}
                </div>
                """,
                unsafe_allow_html=True
            )

    else:
        st.error("El archivo CSV debe tener una columna llamada 'geolocation'")
