import streamlit as st
import geopandas as gpd
import requests
import folium
from streamlit_folium import st_folium
from shapely.geometry import Point, MultiPoint
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from io import BytesIO
import json
import pandas as pd
import time

# --- Configuración de la Página ---
st.set_page_config(page_title="Análisis Territorial Bogotá", page_icon="🗺️", layout="wide")
st.title("🗺️ Análisis Territorial de Bogotá - Sistema de Diagnóstico")

# --- Función cacheada para la carga de datos ---
@st.cache_data
def cargar_datasets():
    """Carga todos los datasets geográficos desde GitHub"""
    datasets = {
        "localidades": "https://github.com/andres-fuentex/tfm-avm-bogota/raw/main/datos_visualizacion/datos_geograficos_geo/dim_localidad.geojson",
        "areas": "https://github.com/andres-fuentex/tfm-avm-bogota/raw/main/datos_visualizacion/datos_geograficos_geo/dim_area.geojson",
        "manzanas": "https://github.com/andres-fuentex/tfm-avm-bogota/raw/main/datos_visualizacion/datos_geograficos_geo/tabla_hechos.geojson",
        "transporte": "https://github.com/andres-fuentex/tfm-avm-bogota/raw/main/datos_visualizacion/datos_geograficos_geo/dim_transporte.geojson",
        "colegios": "https://github.com/andres-fuentex/tfm-avm-bogota/raw/main/datos_visualizacion/datos_geograficos_geo/dim_colegios.geojson"
    }
    
    dataframes = {}
    total = len(datasets)
    progress_bar = st.progress(0, text="Iniciando carga de datos...")
    
    for idx, (nombre, url) in enumerate(datasets.items(), start=1):
        progress_text = f"Cargando {nombre} ({idx}/{total})..."
        progress_bar.progress(idx / total, text=progress_text)
        
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                geojson_data = json.loads(response.text)
                dataframes[nombre] = gpd.GeoDataFrame.from_features(
                    geojson_data["features"], crs="EPSG:4326"
                )
                break
            except requests.exceptions.RequestException as e:
                st.warning(f"Intento {attempt + 1}/{max_retries} fallido al cargar {nombre}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    st.error(f"Error al cargar {nombre} después de {max_retries} intentos")
                    return None
            except json.JSONDecodeError as e:
                st.error(f"Error al decodificar JSON para {nombre}: {e}")
                return None
            except Exception as e:
                st.error(f"Error al procesar {nombre}: {e}")
                return None
    
    progress_bar.empty()
    return dataframes

# --- Inicialización del estado ---
if "step" not in st.session_state:
    st.session_state.step = 1

# ========================================
# PASO 1: CARGA DE DATOS
# ========================================
if st.session_state.step == 1:
    st.markdown("""
    ### Bienvenido al Sistema de Análisis Territorial
    
    Este sistema permite realizar diagnósticos territoriales de las localidades de Bogotá,
    analizando la disponibilidad de servicios y equipamientos urbanos en áreas específicas.
    """)
    
    with st.spinner('Cargando datasets geográficos...'):
        dataframes = cargar_datasets()
        
    if dataframes:
        st.success('✅ Todos los datos han sido cargados correctamente.')
        if st.button("▶️ Iniciar Análisis"):
            for nombre, df in dataframes.items():
                st.session_state[nombre] = df
            st.session_state.step = 2
            st.rerun()
    else:
        st.error("❌ Error al cargar los datasets. Por favor, revise las URLs o la conexión.")

# ========================================
# PASO 2: SELECCIÓN DE LOCALIDAD
# ========================================
elif st.session_state.step == 2:
    st.header("🌆 Paso 1: Seleccione su Localidad")
    st.markdown("Haz clic sobre la localidad que deseas analizar:")
    
    localidades = st.session_state.localidades
    
    # Crear mapa interactivo con Folium
    bounds = localidades.total_bounds
    center = [(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2]
    
    mapa = folium.Map(location=center, zoom_start=11, tiles="CartoDB positron")
    
    folium.GeoJson(
        localidades,
        style_function=lambda feature: {
            "fillColor": "#3388ff",
            "color": "black",
            "weight": 2,
            "fillOpacity": 0.3
        },
        highlight_function=lambda feature: {
            "weight": 3,
            "color": "#FF6B6B",
            "fillOpacity": 0.6
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["nombre_localidad"],
            labels=False,
            sticky=True
        )
    ).add_to(mapa)
    
    result = st_folium(mapa, width=900, height=600, returned_objects=["last_clicked"])
    
    # Detectar clic en localidad
    clicked = result.get("last_clicked")
    if clicked and "lat" in clicked and "lng" in clicked:
        punto = Point(clicked["lng"], clicked["lat"])
        for _, row in localidades.iterrows():
            if row["geometry"].contains(punto):
                st.session_state.localidad_clic = row["nombre_localidad"]
                break
        else:
            st.session_state.localidad_clic = None
    
    # Mostrar localidad seleccionada
    if "localidad_clic" in st.session_state and st.session_state.localidad_clic:
        st.success(f"✅ Localidad seleccionada: **{st.session_state.localidad_clic}**")
        
        if st.button("✅ Confirmar y Continuar"):
            st.session_state.localidad_sel = st.session_state.localidad_clic
            st.session_state.step = 3
            st.rerun()
    
    if st.button("🔄 Volver al Inicio"):
        st.session_state.step = 1
        st.rerun()

# ========================================
# PASO 3: SELECCIÓN DE TAMAÑO DE BUFFER
# ========================================
elif st.session_state.step == 3:
    st.header("📏 Paso 2: Seleccione el Tamaño del Buffer")
    
    st.markdown(f"""
    Localidad seleccionada: **{st.session_state.localidad_sel}**
    
    El buffer es el área de influencia que se analizará alrededor del punto de interés.
    Seleccione el radio en metros:
    """)
    
    buffer_size = st.slider(
        "Radio del buffer (metros)",
        min_value=300,
        max_value=2000,
        value=500,
        step=100,
        help="Distancia de análisis desde el punto seleccionado"
    )
    
    st.session_state.buffer_size = buffer_size
    
    st.info(f"📍 Se analizará un área de **{buffer_size} metros** alrededor del punto seleccionado")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔙 Volver a Selección de Localidad"):
            st.session_state.step = 2
            st.rerun()
    with col2:
        if st.button("✅ Confirmar y Continuar"):
            st.session_state.step = 4
            st.rerun()


# ========================================
# PASO 4: CLIC SOBRE PUNTO DE INTERÉS
# ========================================
elif st.session_state.step == 4:
    st.header("📍 Paso 3: Seleccione el Punto de Interés")
    
    st.markdown(f"""
    **Localidad:** {st.session_state.localidad_sel}  
    **Buffer:** {st.session_state.buffer_size} metros
    
    Haz clic sobre el mapa para seleccionar el punto de interés a analizar:
    """)
    
    localidades = st.session_state.localidades
    manzanas = st.session_state.manzanas
    
    # Filtrar por localidad
    cod_localidad = localidades[
        localidades["nombre_localidad"] == st.session_state.localidad_sel
    ]["num_localidad"].values[0]
    
    # Obtener geometría de la localidad seleccionada
    localidad_geo = localidades[localidades["num_localidad"] == cod_localidad]
    
    # Crear mapa de la localidad
    bounds = localidad_geo.total_bounds
    center = [(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2]
    
    # Crear mapa
    mapa = folium.Map(
        location=center, 
        zoom_start=12, 
        tiles="CartoDB positron",
        prefer_canvas=True
    )
    
    # Agregar polígono de la localidad con los colores que te gustaron
    folium.GeoJson(
        localidad_geo,
        style_function=lambda feature: {
            "fillColor": "#E4EB83",  # Naranja claro (que te gustó)
            "color": "#FF0000",  # Borde rojo
            "weight": 3,
            "fillOpacity": 0.35,
            "interactive": True
        },
        highlight_function=lambda feature: {
            "fillColor": "#F7C28E",  # Verde-amarillo al hover (que te gustó)
            "color": "#FF0000",
            "weight": 4,
            "fillOpacity": 0.45
        }
    ).add_to(mapa)
    
    # Agregar CSS para cursor de cruz
    cursor_css = """
    <style>
        .folium-map {
            cursor: crosshair !important;
        }
        .leaflet-container {
            cursor: crosshair !important;
        }
        .leaflet-interactive {
            cursor: crosshair !important;
        }
        .leaflet-grab {
            cursor: crosshair !important;
        }
        .leaflet-dragging .leaflet-grab {
            cursor: move !important;
        }
    </style>
    """
    
    # Agregar CSS al mapa
    mapa.get_root().html.add_child(folium.Element(cursor_css))
    
    # Renderizar mapa (ESTO FALTABA)
    result = st_folium(mapa, width=900, height=600, returned_objects=["last_clicked"], key="mapa_punto_interes")
    
    # Detectar clic
    clicked = result.get("last_clicked")
    if clicked and "lat" in clicked and "lng" in clicked:
        st.session_state.punto_lat = clicked["lat"]
        st.session_state.punto_lon = clicked["lng"]
        
        # Mostrar información del punto seleccionado con estilo mejorado
        st.success(f"✅ **Punto seleccionado exitosamente**")
        
        col_info1, col_info2, col_info3 = st.columns(3)
        with col_info1:
            st.metric("📍 Latitud", f"{clicked['lat']:.6f}")
        with col_info2:
            st.metric("📍 Longitud", f"{clicked['lng']:.6f}")
        with col_info3:
            st.metric("🎯 Buffer", f"{st.session_state.buffer_size}m")
        
        if st.button("✅ Confirmar y Generar Análisis", type="primary", use_container_width=True):
            st.session_state.step = 5
            st.rerun()
    else:
        st.info("👆 Haz clic sobre el mapa para seleccionar el punto de análisis")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔙 Volver a Selección de Buffer", use_container_width=True):
            st.session_state.step = 3
            st.rerun()
    with col2:
        if st.button("🔄 Reiniciar", use_container_width=True):
            st.session_state.step = 1
            st.rerun()


# ========================================
# PASO 5: GENERACIÓN DE MAPAS Y ANÁLISIS
# ========================================
elif st.session_state.step == 5:
    st.header("📊 Análisis Territorial Completo")
    
    st.markdown(f"""
    **Localidad:** {st.session_state.localidad_sel}  
    **Buffer:** {st.session_state.buffer_size} metros  
    **Punto:** Lat {st.session_state.punto_lat:.6f}, Lon {st.session_state.punto_lon:.6f}
    """)
    
    # Cargar datos
    localidades = st.session_state.localidades
    manzanas = st.session_state.manzanas
    transporte = st.session_state.transporte
    colegios = st.session_state.colegios
    areas = st.session_state.areas
    
    # Obtener código de localidad
    cod_localidad = localidades[
        localidades["nombre_localidad"] == st.session_state.localidad_sel
    ]["num_localidad"].values[0]
    
    # Crear punto y buffer
    punto = Point(st.session_state.punto_lon, st.session_state.punto_lat)
    punto_gdf = gpd.GeoDataFrame([{"geometry": punto}], crs="EPSG:4326")
    punto_proj = punto_gdf.to_crs(epsg=3116)
    
    buffer_proj = punto_proj.buffer(st.session_state.buffer_size)
    buffer_wgs = buffer_proj.to_crs(epsg=4326).iloc[0]
    
    # Filtrar datos dentro del buffer
    manzanas_buffer = manzanas[manzanas.geometry.intersects(buffer_wgs)]
    
    # Contar estaciones de transporte dentro del buffer
    estaciones_buffer = []
    for _, row in transporte.iterrows():
        if hasattr(row["geometry"], "geoms"):
            for pt in row["geometry"].geoms:
                if buffer_wgs.contains(pt):
                    estaciones_buffer.append(pt)
        elif isinstance(row["geometry"], Point):
            if buffer_wgs.contains(row["geometry"]):
                estaciones_buffer.append(row["geometry"])
    
    # Contar colegios dentro del buffer
    colegios_buffer = []
    for _, row in colegios.iterrows():
        if hasattr(row["geometry"], "geoms"):
            for pt in row["geometry"].geoms:
                if buffer_wgs.contains(pt):
                    colegios_buffer.append(pt)
        elif isinstance(row["geometry"], Point):
            if buffer_wgs.contains(row["geometry"]):
                colegios_buffer.append(row["geometry"])
    
    # ========================================
    # IMAGEN 1: Mapa buffer con cantidad de manzanas
    # ========================================
    st.markdown("### 📍 Imagen 1: Buffer con Manzanas")
    
    fig1 = go.Figure()
    
    # Agregar buffer
    fig1.add_trace(go.Scattermapbox(
        lat=list(buffer_wgs.exterior.xy[1]),
        lon=list(buffer_wgs.exterior.xy[0]),
        mode='lines',
        fill='toself',
        name=f'Buffer {st.session_state.buffer_size}m',
        fillcolor='rgba(255, 0, 0, 0.1)',
        line=dict(color='red', width=2)
    ))
    
    # Agregar manzanas
    for _, manzana in manzanas_buffer.iterrows():
        coords = manzana.geometry.exterior.coords
        fig1.add_trace(go.Scattermapbox(
            lat=[c[1] for c in coords],
            lon=[c[0] for c in coords],
            mode='lines',
            fill='toself',
            fillcolor='rgba(76, 175, 80, 0.4)',
            line=dict(color='#2E7D32', width=1),
            showlegend=False
        ))
    
    # Agregar punto central
    fig1.add_trace(go.Scattermapbox(
        lat=[st.session_state.punto_lat],
        lon=[st.session_state.punto_lon],
        mode='markers',
        name='Punto de Interés',
        marker=dict(size=12, color='blue')
    ))
    
    fig1.update_layout(
        mapbox_style="carto-positron",
        mapbox_center={"lat": st.session_state.punto_lat, "lon": st.session_state.punto_lon},
        mapbox_zoom=14,
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
        title=f"Buffer con {len(manzanas_buffer)} Manzanas",
        showlegend=True
    )
    
    st.plotly_chart(fig1, use_container_width=True)
    st.metric("Total de Manzanas", len(manzanas_buffer))
    
    # ========================================
    # IMAGEN 2: Mapa buffer con estaciones de transporte
    # ========================================
    # ========================================
    # IMAGEN 2: Mapa buffer con estaciones de transporte
    # ========================================
    st.markdown("### 🚇 Imagen 2: Buffer con Estaciones de Transporte")

    # Filtrar estaciones dentro del buffer (CORREGIDO)
    estaciones_buffer = []
    estaciones_coords = []  # Para evitar duplicados

    for _, row in transporte.iterrows():
        geom = row["geometry"]
        
        # Manejar MultiPoint
        if hasattr(geom, "geoms"):
            for pt in geom.geoms:
                if buffer_wgs.contains(pt):
                    coord_tuple = (pt.x, pt.y)
                    if coord_tuple not in estaciones_coords:
                        estaciones_buffer.append(pt)
                        estaciones_coords.append(coord_tuple)
        # Manejar Point simple
        elif isinstance(geom, Point):
            if buffer_wgs.contains(geom):
                coord_tuple = (geom.x, geom.y)
                if coord_tuple not in estaciones_coords:
                    estaciones_buffer.append(geom)
                    estaciones_coords.append(coord_tuple)

    fig2 = go.Figure()

    # Agregar buffer
    fig2.add_trace(go.Scattermapbox(
        lat=list(buffer_wgs.exterior.xy[1]),
        lon=list(buffer_wgs.exterior.xy[0]),
        mode='lines',
        fill='toself',
        name=f'Buffer {st.session_state.buffer_size}m',
        fillcolor='rgba(255, 165, 0, 0.1)',
        line=dict(color='orange', width=2)
    ))

    # Agregar estaciones (MEJORADO para visualización)
    if estaciones_buffer:
        lats = [pt.y for pt in estaciones_buffer]
        lons = [pt.x for pt in estaciones_buffer]
        
        fig2.add_trace(go.Scattermapbox(
            lat=lats,
            lon=lons,
            mode='markers',
            name='Estaciones de Transporte',
            marker=dict(
                size=12,
                color='red',
                opacity=1.0,
                symbol='circle'  # Cambio de 'rail' a 'circle' para mejor visualización
            ),
            text=[f'Estación {i+1}' for i in range(len(estaciones_buffer))],
            hoverinfo='text'
        ))

    # Agregar punto central
    fig2.add_trace(go.Scattermapbox(
        lat=[st.session_state.punto_lat],
        lon=[st.session_state.punto_lon],
        mode='markers',
        name='Punto de Interés',
        marker=dict(
            size=15,
            color='blue'
        )
    ))

    fig2.update_layout(
        mapbox_style="carto-positron",
        mapbox_center={"lat": st.session_state.punto_lat, "lon": st.session_state.punto_lon},
        mapbox_zoom=14,
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
        title=f"Buffer con {len(estaciones_buffer)} Estaciones de Transporte",
        showlegend=True,
        height=600
    )

    st.plotly_chart(fig2, use_container_width=True)

    # Métricas adicionales
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total de Estaciones en Buffer", len(estaciones_buffer))
    with col2:
        if estaciones_buffer:
            densidad = len(estaciones_buffer) / (3.14159 * (st.session_state.buffer_size/1000)**2)
            st.metric("Densidad (estaciones/km²)", f"{densidad:.2f}")
    
    # ========================================
    # IMAGEN 3: Mapa buffer con colegios
    # ========================================
    st.markdown("### 🏫 Imagen 3: Buffer con Colegios")

    # Filtrar colegios dentro del buffer (CORREGIDO)
    colegios_buffer = []
    colegios_coords = []  # Para evitar duplicados

    for _, row in colegios.iterrows():
        geom = row["geometry"]
        
        # Manejar MultiPoint
        if hasattr(geom, "geoms"):
            for pt in geom.geoms:
                if buffer_wgs.contains(pt):
                    coord_tuple = (pt.x, pt.y)
                    if coord_tuple not in colegios_coords:
                        colegios_buffer.append(pt)
                        colegios_coords.append(coord_tuple)
        # Manejar Point simple
        elif isinstance(geom, Point):
            if buffer_wgs.contains(geom):
                coord_tuple = (geom.x, geom.y)
                if coord_tuple not in colegios_coords:
                    colegios_buffer.append(geom)
                    colegios_coords.append(coord_tuple)

    fig3 = go.Figure()

    # Agregar buffer
    fig3.add_trace(go.Scattermapbox(
        lat=list(buffer_wgs.exterior.xy[1]),
        lon=list(buffer_wgs.exterior.xy[0]),
        mode='lines',
        fill='toself',
        name=f'Buffer {st.session_state.buffer_size}m',
        fillcolor='rgba(0, 0, 255, 0.1)',
        line=dict(color='blue', width=2)
    ))

    # Agregar colegios (MEJORADO para visualización)
    if colegios_buffer:
        lats = [pt.y for pt in colegios_buffer]
        lons = [pt.x for pt in colegios_buffer]
        
        fig3.add_trace(go.Scattermapbox(
            lat=lats,
            lon=lons,
            mode='markers',
            name='Colegios',
            marker=dict(
                size=12,
                color='purple',
                opacity=1.0,
                symbol='circle'  # Cambio de 'school' a 'circle' para mejor visualización
            ),
            text=[f'Colegio {i+1}' for i in range(len(colegios_buffer))],
            hoverinfo='text'
        ))

    # Agregar punto central
    fig3.add_trace(go.Scattermapbox(
        lat=[st.session_state.punto_lat],
        lon=[st.session_state.punto_lon],
        mode='markers',
        name='Punto de Interés',
        marker=dict(
            size=15,
            color='blue'
        )
    ))

    fig3.update_layout(
        mapbox_style="carto-positron",
        mapbox_center={"lat": st.session_state.punto_lat, "lon": st.session_state.punto_lon},
        mapbox_zoom=14,
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
        title=f"Buffer con {len(colegios_buffer)} Colegios",
        showlegend=True,
        height=600
    )

    st.plotly_chart(fig3, use_container_width=True)

    # Métricas adicionales
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total de Colegios en Buffer", len(colegios_buffer))
    with col2:
        if colegios_buffer:
            densidad = len(colegios_buffer) / (3.14159 * (st.session_state.buffer_size/1000)**2)
            st.metric("Densidad (colegios/km²)", f"{densidad:.2f}")
    
    # ========================================
    # IMAGEN 4: Mapa buffer con manzanas por estrato
    # ========================================
    st.markdown("### 🏘️ Imagen 4: Buffer con Manzanas por Estrato")

    # Preparar colores por estrato
    estratos_unicos = sorted(manzanas_buffer["estrato"].unique())
    color_estrato = {
        1: '#8B0000',  # Rojo oscuro
        2: '#FF4500',  # Rojo naranja
        3: '#FFD700',  # Dorado
        4: '#90EE90',  # Verde claro
        5: '#4169E1',  # Azul real
        6: '#9370DB'   # Púrpura medio
    }

    fig4 = go.Figure()

    # Buffer
    fig4.add_trace(go.Scattermapbox(
        lat=list(buffer_wgs.exterior.xy[1]),
        lon=list(buffer_wgs.exterior.xy[0]),
        mode='lines',
        name=f'Buffer {st.session_state.buffer_size}m',
        line=dict(color='black', width=2),
        showlegend=False
    ))

    # Agrupar manzanas por estrato para optimizar el renderizado
    trazas_agregadas = set()  # Para controlar que cada estrato aparezca solo una vez en la leyenda

    for estrato in estratos_unicos:
        manzanas_estrato = manzanas_buffer[manzanas_buffer["estrato"] == estrato]
        
        # Agregar cada manzana del estrato
        for idx, (_, manzana) in enumerate(manzanas_estrato.iterrows()):
            if manzana.geometry.geom_type == 'Polygon':
                coords = list(manzana.geometry.exterior.coords)
                
                # Solo mostrar en leyenda la primera manzana de cada estrato
                mostrar_leyenda = estrato not in trazas_agregadas
                if mostrar_leyenda:
                    trazas_agregadas.add(estrato)
                
                fig4.add_trace(go.Scattermapbox(
                    lat=[c[1] for c in coords],
                    lon=[c[0] for c in coords],
                    mode='lines',
                    fill='toself',
                    fillcolor=color_estrato.get(estrato, '#808080'),
                    line=dict(color='black', width=0.5),
                    name=f'Estrato {estrato}',
                    showlegend=mostrar_leyenda,
                    legendgroup=f'estrato_{estrato}',
                    hovertext=f'Estrato {estrato}',
                    hoverinfo='text'
                ))

    # Punto central (CORREGIDO)
    fig4.add_trace(go.Scattermapbox(
        lat=[st.session_state.punto_lat],
        lon=[st.session_state.punto_lon],
        mode='markers',
        name='Punto de Interés',
        marker=dict(
            size=15,
            color='white',
            opacity=1.0
        ),
        showlegend=True
    ))

    # Agregar un segundo marcador para el borde negro del punto
    fig4.add_trace(go.Scattermapbox(
        lat=[st.session_state.punto_lat],
        lon=[st.session_state.punto_lon],
        mode='markers',
        marker=dict(
            size=18,
            color='black',
            opacity=1.0
        ),
        showlegend=False
    ))

    fig4.update_layout(
        mapbox_style="carto-positron",
        mapbox_center={"lat": st.session_state.punto_lat, "lon": st.session_state.punto_lon},
        mapbox_zoom=14,
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
        title="Manzanas Clasificadas por Estrato",
        showlegend=True,
        height=600,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor="rgba(255, 255, 255, 0.8)"
        )
    )

    st.plotly_chart(fig4, use_container_width=True)

    # Distribución de estratos con gráfico visual
    st.markdown("**Distribución de Estratos:**")

    dist_estratos = manzanas_buffer["estrato"].value_counts().sort_index()

    # Crear dos columnas: texto y gráfico
    col1, col2 = st.columns([1, 1])

    with col1:
        for estrato, cantidad in dist_estratos.items():
            porcentaje = cantidad/len(manzanas_buffer)*100
            st.write(f"- Estrato {estrato}: {cantidad} manzanas ({porcentaje:.1f}%)")

    with col2:
        # Gráfico de barras de estratos
        fig_estratos = go.Figure(data=[
            go.Bar(
                x=[f"E{e}" for e in dist_estratos.index],
                y=dist_estratos.values,
                marker_color=[color_estrato.get(e, '#808080') for e in dist_estratos.index],
                text=dist_estratos.values,
                textposition='auto',
            )
        ])
        
        fig_estratos.update_layout(
            title="Cantidad de Manzanas por Estrato",
            xaxis_title="Estrato",
            yaxis_title="Cantidad",
            height=300,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        
        st.plotly_chart(fig_estratos, use_container_width=True)
        
    # ========================================
    # IMAGEN 5: Mapa buffer con áreas POT
    # ========================================
    st.markdown("### 🗺️ Imagen 5: Buffer con Áreas del POT")

    # Unir con áreas POT
    if "id_area" in manzanas_buffer.columns and not areas.empty:
        manzanas_pot = manzanas_buffer.merge(
            areas[["id_area", "uso_pot_simplificado"]],
            on="id_area",
            how="left"
        )
        manzanas_pot["uso_pot_simplificado"] = manzanas_pot["uso_pot_simplificado"].fillna("Sin clasificación")
    else:
        manzanas_pot = manzanas_buffer.copy()
        manzanas_pot["uso_pot_simplificado"] = "Sin clasificación"

    # Colores para POT
    usos_pot = sorted(manzanas_pot["uso_pot_simplificado"].unique())
    palette_pot = px.colors.qualitative.Plotly
    color_pot_map = {uso: palette_pot[i % len(palette_pot)] for i, uso in enumerate(usos_pot)}

    fig5 = go.Figure()

    # Buffer
    fig5.add_trace(go.Scattermapbox(
        lat=list(buffer_wgs.exterior.xy[1]),
        lon=list(buffer_wgs.exterior.xy[0]),
        mode='lines',
        name=f'Buffer {st.session_state.buffer_size}m',
        line=dict(color='black', width=2),
        showlegend=False
    ))

    # Agrupar manzanas por uso POT para optimizar el renderizado
    trazas_agregadas_pot = set()  # Para controlar que cada uso aparezca solo una vez en la leyenda

    for uso in usos_pot:
        manzanas_uso = manzanas_pot[manzanas_pot["uso_pot_simplificado"] == uso]
        
        # Agregar cada manzana del uso POT
        for idx, (_, manzana) in enumerate(manzanas_uso.iterrows()):
            if manzana.geometry.geom_type == 'Polygon':
                coords = list(manzana.geometry.exterior.coords)
                
                # Solo mostrar en leyenda la primera manzana de cada uso
                mostrar_leyenda = uso not in trazas_agregadas_pot
                if mostrar_leyenda:
                    trazas_agregadas_pot.add(uso)
                
                fig5.add_trace(go.Scattermapbox(
                    lat=[c[1] for c in coords],
                    lon=[c[0] for c in coords],
                    mode='lines',
                    fill='toself',
                    fillcolor=color_pot_map.get(uso, '#808080'),
                    line=dict(color='black', width=0.5),
                    name=uso,
                    showlegend=mostrar_leyenda,
                    legendgroup=f'pot_{uso}',
                    hovertext=f'{uso}',
                    hoverinfo='text'
                ))

    # Punto central (CORREGIDO - mismo método que en Imagen 4)
    fig5.add_trace(go.Scattermapbox(
        lat=[st.session_state.punto_lat],
        lon=[st.session_state.punto_lon],
        mode='markers',
        name='Punto de Interés',
        marker=dict(
            size=15,
            color='white',
            opacity=1.0
        ),
        showlegend=True
    ))

    # Agregar un segundo marcador para el borde negro del punto
    fig5.add_trace(go.Scattermapbox(
        lat=[st.session_state.punto_lat],
        lon=[st.session_state.punto_lon],
        mode='markers',
        marker=dict(
            size=18,
            color='black',
            opacity=1.0
        ),
        showlegend=False
    ))

    fig5.update_layout(
        mapbox_style="carto-positron",
        mapbox_center={"lat": st.session_state.punto_lat, "lon": st.session_state.punto_lon},
        mapbox_zoom=14,
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
        title="Manzanas Clasificadas por Uso del Suelo (POT)",
        showlegend=True,
        height=600,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor="rgba(255, 255, 255, 0.8)"
        )
    )

    st.plotly_chart(fig5, use_container_width=True)

    # Distribución de usos POT con visualización mejorada
    st.markdown("**Distribución de Usos del Suelo:**")

    dist_pot = manzanas_pot["uso_pot_simplificado"].value_counts()

    # Crear dos columnas: texto y gráfico
    col1, col2 = st.columns([1, 1])

    with col1:
        for uso, cantidad in dist_pot.items():
            porcentaje = cantidad/len(manzanas_pot)*100
            st.write(f"- {uso}: {cantidad} manzanas ({porcentaje:.1f}%)")

    with col2:
        # Gráfico de barras de usos POT
        fig_pot = go.Figure(data=[
            go.Bar(
                x=list(range(len(dist_pot))),
                y=dist_pot.values,
                marker_color=[color_pot_map.get(uso, '#808080') for uso in dist_pot.index],
                text=dist_pot.values,
                textposition='auto',
                hovertext=dist_pot.index,
                hoverinfo='text+y'
            )
        ])
        
        fig_pot.update_layout(
            title="Cantidad de Manzanas por Uso POT",
            xaxis_title="Uso del Suelo",
            yaxis_title="Cantidad",
            height=300,
            margin=dict(l=20, r=20, t=40, b=20),
            showlegend=False,
            xaxis=dict(
                tickmode='array',
                tickvals=list(range(len(dist_pot))),
                ticktext=[uso[:20] + '...' if len(uso) > 20 else uso for uso in dist_pot.index],
                tickangle=-45
            )
        )
        
        st.plotly_chart(fig_pot, use_container_width=True)
        
    # ========================================
    # INFORME AUTOMATIZADO
    # ========================================
    st.markdown("---")
    st.markdown("### 📋 Informe Automatizado de Diagnóstico Territorial")
    
    # Calcular datos de la localidad completa
    manzanas_localidad = manzanas[manzanas["num_localidad"] == cod_localidad]
    
    # Contar estaciones totales en la localidad
    estaciones_localidad = []
    for _, row in transporte.iterrows():
        if hasattr(row["geometry"], "geoms"):
            for pt in row["geometry"].geoms:
                # Verificar si el punto está en alguna manzana de la localidad
                for _, manzana in manzanas_localidad.iterrows():
                    if manzana.geometry.contains(pt):
                        estaciones_localidad.append(pt)
                        break
    
    # Contar colegios totales en la localidad
    colegios_localidad = []
    for _, row in colegios.iterrows():
        if hasattr(row["geometry"], "geoms"):
            for pt in row["geometry"].geoms:
                for _, manzana in manzanas_localidad.iterrows():
                    if manzana.geometry.contains(pt):
                        colegios_localidad.append(pt)
                        break
    
    total_estaciones_loc = len(set([(pt.x, pt.y) for pt in estaciones_localidad]))
    total_colegios_loc = len(set([(pt.x, pt.y) for pt in colegios_localidad]))
    
    # Calcular porcentajes
    porcentaje_estaciones = (len(estaciones_buffer) / total_estaciones_loc * 100) if total_estaciones_loc > 0 else 0
    porcentaje_colegios = (len(colegios_buffer) / total_colegios_loc * 100) if total_colegios_loc > 0 else 0
    
    # Generar informe
    st.markdown(f"""
    #### Resumen Ejecutivo
    
    **Localidad Analizada:** {st.session_state.localidad_sel}  
    **Radio de Análisis:** {st.session_state.buffer_size} metros  
    **Coordenadas del Punto:** {st.session_state.punto_lat:.6f}, {st.session_state.punto_lon:.6f}
    
    ---
    
    #### 🏘️ Análisis de Manzanas
    - **Total de manzanas en el buffer:** {len(manzanas_buffer)}
    - **Estrato predominante:** {manzanas_buffer['estrato'].mode()[0] if not manzanas_buffer.empty else 'N/A'}
    - **Uso del suelo predominante:** {dist_pot.index[0] if not dist_pot.empty else 'N/A'}
    
    #### 🚇 Análisis de Transporte
    - **Estaciones en el buffer:** {len(estaciones_buffer)}
    - **Total de estaciones en la localidad:** {total_estaciones_loc}
    - **Representación:** {porcentaje_estaciones:.1f}% del total de la localidad
    
    **Diagnóstico:** {"✅ El sector cuenta con buena cobertura de transporte" if len(estaciones_buffer) >= 2 else "⚠️ El sector tiene cobertura limitada de transporte"}
    
    #### 🏫 Análisis Educativo
    - **Colegios en el buffer:** {len(colegios_buffer)}
    - **Total de colegios en la localidad:** {total_colegios_loc}
    - **Representación:** {porcentaje_colegios:.1f}% del total de la localidad
    
    **Diagnóstico:** {"✅ El sector cuenta con buena oferta educativa" if len(colegios_buffer) >= 2 else "⚠️ El sector tiene oferta educativa limitada"}
    
    #### 📊 Evaluación General
    """)
    
    # Evaluación general
    score = 0
    if len(estaciones_buffer) >= 2:
        score += 1
    if len(colegios_buffer) >= 2:
        score += 1
    if len(manzanas_buffer) >= 10:
        score += 1
    
    if score == 3:
        st.success("✅ **SECTOR BIEN DOTADO** - El área analizada cuenta con buena disponibilidad de servicios y equipamientos urbanos.")
    elif score == 2:
        st.warning("⚠️ **SECTOR ACEPTABLE** - El área cuenta con algunos servicios, pero hay oportunidades de mejora.")
    else:
        st.error("❌ **SECTOR CON DÉFICIT** - El área presenta déficit en la disponibilidad de servicios y equipamientos.")
    
    # Guardar datos para descarga
    st.session_state.informe_data = {
        "localidad": st.session_state.localidad_sel,
        "buffer_size": st.session_state.buffer_size,
        "manzanas": len(manzanas_buffer),
        "estaciones": len(estaciones_buffer),
        "colegios": len(colegios_buffer),
        "total_estaciones_loc": total_estaciones_loc,
        "total_colegios_loc": total_colegios_loc,
        "score": score
    }
    
    # Botones de navegación
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔙 Volver a Selección de Punto"):
            st.session_state.step = 4
            st.rerun()
    
    with col2:
        if st.button("📥 Descargar Informe"):
            # Crear CSV con los datos
            import csv
            from io import StringIO
            
            csv_buffer = StringIO()
            writer = csv.writer(csv_buffer)
            writer.writerow(["Indicador", "Valor"])
            writer.writerow(["Localidad", st.session_state.localidad_sel])
            writer.writerow(["Buffer (m)", st.session_state.buffer_size])
            writer.writerow(["Manzanas", len(manzanas_buffer)])
            writer.writerow(["Estaciones", len(estaciones_buffer)])
            writer.writerow(["Colegios", len(colegios_buffer)])
            writer.writerow(["% Estaciones", f"{porcentaje_estaciones:.1f}"])
            writer.writerow(["% Colegios", f"{porcentaje_colegios:.1f}"])
            
            st.download_button(
                label="Descargar datos en CSV",
                data=csv_buffer.getvalue(),
                file_name=f"informe_{st.session_state.localidad_sel}_{st.session_state.buffer_size}m.csv",
                mime="text/csv"
            )
    
    with col3:
        if st.button("🔄 Nuevo Análisis"):
            # Limpiar datos pero mantener datasets
            keys_to_keep = ["localidades", "areas", "manzanas", "transporte", "colegios"]
            keys_to_delete = [k for k in st.session_state.keys() if k not in keys_to_keep]
            for key in keys_to_delete:
                del st.session_state[key]
            st.session_state.step = 2
            st.rerun()
