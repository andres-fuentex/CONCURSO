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
st.set_page_config(
    page_title="Bogotá Inteligente: Diagnóstico Territorial",
    page_icon="🗺️",
    layout="wide"
)

st.title("🚀 Bogotá Inteligente: Explora el Potencial de tu Ciudad con Datos")

st.markdown("""
**Bienvenido al futuro del análisis urbano en Bogotá.**

Imagina poder mapear, entender y transformar tu entorno utilizando la ciencia de datos, ¡todo en un solo clic!

Esta plataforma pone en tus manos el poder de la información geoespacial pública para revelar oportunidades de desarrollo, detectar brechas de servicios y optimizar decisiones en planificación territorial.

A través de una experiencia interactiva, recorrerás paso a paso el proceso de diagnóstico: selecciona tu localidad, explora el área de influencia y descubre —de manera visual, automática y comparativa— los servicios, la educación, el transporte y mucho más, con el respaldo de datos abiertos.

_Convierte los datos en visión. Descubre el potencial oculto de cada rincón de Bogotá. El análisis comienza aquí._
""")

# --- Función cacheada para la carga de datos ---
@st.cache_data
def cargar_datasets():
    """Carga los datasets geográficos urbanos desde fuentes abiertas"""
    datasets = {
        "localidades": "https://github.com/andres-fuentex/tfm-avm-bogota/raw/main/datos_visualizacion/datos_geograficos_geo/dim_localidad.geojson",
        "areas": "https://github.com/andres-fuentex/tfm-avm-bogota/raw/main/datos_visualizacion/datos_geograficos_geo/dim_area.geojson",
        "manzanas": "https://github.com/andres-fuentex/tfm-avm-bogota/raw/main/datos_visualizacion/datos_geograficos_geo/tabla_hechos.geojson",
        "transporte": "https://github.com/andres-fuentex/tfm-avm-bogota/raw/main/datos_visualizacion/datos_geograficos_geo/dim_transporte.geojson",
        "colegios": "https://github.com/andres-fuentex/tfm-avm-bogota/raw/main/datos_visualizacion/datos_geograficos_geo/dim_colegios.geojson"
    }
    dataframes = {}
    for nombre, url in datasets.items():
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        geojson_data = json.loads(response.text)
        dataframes[nombre] = gpd.GeoDataFrame.from_features(
            geojson_data["features"], crs="EPSG:4326"
        )
    return dataframes

# --- Inicialización del estado ---
if "step" not in st.session_state:
    st.session_state.step = 1

# ========================================
# PASO 1: CARGA DE DATOS
# ========================================
if st.session_state.step == 1:
    st.markdown("""
    ### 🚦 Punto de partida: Activando el diagnóstico urbano

    Antes de comenzar, el sistema recopila y verifica los datos esenciales de la ciudad para tu análisis.
    Este proceso conectará fuentes oficiales y consolidará información geoespacial clave para que tu exploración territorial sea sólida y confiable.
    """)
    
    st.info(
        "🔄 **Preparando el escenario digital:**\n\n"
        "En segundos tendrás acceso a la radiografía inteligente de Bogotá, utilizando fuentes oficiales de datos abiertos urbanísticos."
    )

    # Usar spinner para indicar proceso de carga
    with st.spinner('⏳ Conectando y descargando los datasets urbanos...'):
        try:
            dataframes = cargar_datasets()
        except Exception as e:
            st.error(f"❌ Error al cargar los datos: {e}")
            st.stop()

    if dataframes:
        st.success('✅ Datos cargados exitosamente. ¡Listo para iniciar tu análisis!')
        if st.button("🔍 Empezar diagnóstico"):
            for nombre, df in dataframes.items():
                st.session_state[nombre] = df
            st.session_state.step = 2
            st.rerun()
    else:
        st.error("❌ Ocurrió un problema al cargar los datos. Verifica tu conexión o inténtalo nuevamente en unos minutos.")


# ========================================
# PASO 2: SELECCIÓN DE LOCALIDAD
# ========================================
elif st.session_state.step == 2:
    st.header("🌆 Paso 1: Selecciona tu Localidad de Interés")

    st.markdown("""
    **¿Dónde comienza tu análisis?**
    Haz clic sobre la localidad de Bogotá que deseas explorar. El sistema te mostrará un mapa interactivo con límites administrativos oficiales.
    El color azul suave resalta el área elegida; al pasar el mouse, el borde rojo reforzará tu selección. Toda la plataforma mantiene un estilo gráfico uniforme para garantizar claridad y profesionalismo.
    """)

    # Estilos generales unificados para todas las visualizaciones
    COLOR_FRAME = "#131313"        # Marco general, negro-gris
    COLOR_FILL = "#3D8EDB"         # Relleno principal, azul corporativo
    COLOR_HI_FILL = "#E7F5FF"      # Relleno al hover, azul muy claro
    COLOR_BORDER = "#C22323"       # Borde destacado en hover, rojo intenso

    localidades = st.session_state.localidades

    # Crear mapa interactivo con Folium
    bounds = localidades.total_bounds
    center = [(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2]

    mapa = folium.Map(location=center, zoom_start=11, tiles="CartoDB positron")
    
    # Marco y estilos de localidad
    folium.GeoJson(
        localidades,
        style_function=lambda feature: {
            "fillColor": COLOR_FILL,
            "color": COLOR_FRAME,
            "weight": 2,
            "fillOpacity": 0.35,       # Un poco más visible
        },
        highlight_function=lambda feature: {
            "weight": 3,
            "color": COLOR_BORDER,
            "fillColor": COLOR_HI_FILL,
            "fillOpacity": 0.55,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["nombre_localidad"],
            aliases=["Localidad:"],
            labels=False,
            sticky=True
        )
    ).add_to(mapa)

    # Uniformidad en tamaño del lienzo para todas las visualizaciones
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

    st.markdown("---")
    if st.button("🔄 Volver al Inicio"):
        st.session_state.step = 1
        st.rerun()


# ========================================
# PASO 3: DEFINIR ÁREA DE INFLUENCIA
# ========================================
elif st.session_state.step == 3:
    st.header("📏 Paso 2: Define el radio de tu análisis urbano")

    st.markdown(f"""
    **Localidad seleccionada:** `{st.session_state.localidad_sel}`  
    
    El radio de análisis determina el área de influencia que se estudiará alrededor del punto que escojas en el mapa.
    Decide qué tan amplio quieres que sea tu contexto urbano y ajusta el valor en metros para comparar sectores de forma homogénea.
    """)

    # Saltos de 300 en 300 para mejor usabilidad mobile/desktop
    radio_analisis = st.slider(
        "Selecciona el radio de análisis (metros)",
        min_value=300,
        max_value=2100,
        value=600,
        step=300,
        help="Entre más grande el radio, más contexto y servicios urbanos tendrás en el análisis."
    )
    st.session_state.radio_analisis = radio_analisis

    st.info(f"🟠 El análisis incluirá una zona de **{radio_analisis} metros** alrededor del punto que selecciones en el siguiente paso.")

    # Botones de navegación
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔙 Volver a selección de localidad"):
            st.session_state.step = 2
            st.rerun()
    with col2:
        if st.button("➡️ Continuar"):
            st.session_state.step = 4
            st.rerun()


# ========================================
# PASO 4: SELECCIÓN DE PUNTO DE INTERÉS
# ========================================
elif st.session_state.step == 4:
    st.header("📍 Paso 3: Selecciona el punto sobre el cual analizarás el entorno")

    st.markdown(f"""
    **Localidad elegida:** `{st.session_state.localidad_sel}`  
    **Radio de análisis:** `{st.session_state.radio_analisis} metros`

    Haz clic directamente sobre la zona que deseas estudiar en detalle. 
    El sistema aplicará el radio seleccionado para analizar el entorno urbano alrededor del punto que escojas.
    """)

    localidades = st.session_state.localidades

    # Filtrar por localidad seleccionada
    cod_localidad = localidades[
        localidades["nombre_localidad"] == st.session_state.localidad_sel
    ]["num_localidad"].values[0]

    localidad_geo = localidades[localidades["num_localidad"] == cod_localidad]

    # Colores uniformes
    COLOR_FILL = "#E4EB83"  # Relleno claro
    COLOR_BORDER = "#FF0000"  # Borde rojo

    # Crear mapa con cursor cruz
    bounds = localidad_geo.total_bounds
    center = [(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2]

    mapa = folium.Map(
        location=center,
        zoom_start=12,
        tiles="CartoDB positron",
        prefer_canvas=True
    )

    # Polígono de localidad visual uniforme
    folium.GeoJson(
        localidad_geo,
        style_function=lambda feature: {
            "fillColor": COLOR_FILL,
            "color": COLOR_BORDER,
            "weight": 3,
            "fillOpacity": 0.35,
            "interactive": True
        },
        highlight_function=lambda feature: {
            "fillColor": "#F7C28E",
            "color": COLOR_BORDER,
            "weight": 4,
            "fillOpacity": 0.45
        }
    ).add_to(mapa)

    # CSS para cursor de cruz
    cursor_css = """
    <style>
        .folium-map, .leaflet-container, .leaflet-interactive, .leaflet-grab {
            cursor: crosshair !important;
        }
        .leaflet-dragging .leaflet-grab {
            cursor: move !important;
        }
    </style>
    """
    mapa.get_root().html.add_child(folium.Element(cursor_css))

    # Renderizar mapa interactivo
    result = st_folium(mapa, width=900, height=600, returned_objects=["last_clicked"], key="mapa_punto_interes")

    # Captura clic y muestra detalles con storytelling
    clicked = result.get("last_clicked")
    if clicked and "lat" in clicked and "lng" in clicked:
        st.session_state.punto_lat = clicked["lat"]
        st.session_state.punto_lon = clicked["lng"]

        st.success(
            f"📍 Punto seleccionado correctamente. "
            f"El análisis de entorno abarcará un radio de `{st.session_state.radio_analisis} metros` desde aquí."
        )

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Latitud", f"{clicked['lat']:.6f}")
        with col2:
            st.metric("Longitud", f"{clicked['lng']:.6f}")
        with col3:
            st.metric("Radio de análisis", f"{st.session_state.radio_analisis} m")

        if st.button("✅ Confirmar y generar visualizaciones", type="primary", use_container_width=True):
            st.session_state.step = 5
            st.rerun()
    else:
        st.info("👆 Haz clic sobre el mapa para elegir tu punto de estudio.")

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔙 Volver al paso anterior", use_container_width=True):
            st.session_state.step = 3
            st.rerun()
    with col2:
        if st.button("🔄 Reiniciar análisis", use_container_width=True):
            st.session_state.step = 1
            st.rerun()

# ========================================
# PASO 5: GENERACIÓN DE MAPAS Y ANÁLISIS
# ========================================
elif st.session_state.step == 5:
    st.header("📊 Diagnóstico Urbano Completo")

    st.markdown(f"""
    <b>Localidad seleccionada:</b> {st.session_state.localidad_sel}  
    <b>Radio de análisis:</b> {st.session_state.radio_analisis} metros  
    <b>Punto de interés:</b> Lat {st.session_state.punto_lat:.6f}, Lon {st.session_state.punto_lon:.6f}

    La herramienta generará visualizaciones y métricas que describen el entorno urbano alrededor del punto elegido. Analiza la densidad, acceso a servicios y el contexto socioespacial de la zona seleccionada.
    """, unsafe_allow_html=True)

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

    # Crear punto y área de análisis
    punto = Point(st.session_state.punto_lon, st.session_state.punto_lat)
    punto_gdf = gpd.GeoDataFrame([{"geometry": punto}], crs="EPSG:4326")
    punto_proj = punto_gdf.to_crs(epsg=3116)
    area_proj = punto_proj.buffer(st.session_state.radio_analisis)
    area_wgs = area_proj.to_crs(epsg=4326).iloc[0]

    # Filtrar datos dentro del área de análisis
    manzanas_zona = manzanas[manzanas.geometry.intersects(area_wgs)]

    # Contar estaciones de transporte dentro del área de análisis
    estaciones_zona = []
    for _, row in transporte.iterrows():
        if hasattr(row["geometry"], "geoms"):
            for pt in row["geometry"].geoms:
                if area_wgs.contains(pt):
                    estaciones_zona.append(pt)
        elif isinstance(row["geometry"], Point):
            if area_wgs.contains(row["geometry"]):
                estaciones_zona.append(row["geometry"])

    # Contar colegios dentro del área de análisis
    colegios_zona = []
    for _, row in colegios.iterrows():
        if hasattr(row["geometry"], "geoms"):
            for pt in row["geometry"].geoms:
                if area_wgs.contains(pt):
                    colegios_zona.append(pt)
        elif isinstance(row["geometry"], Point):
            if area_wgs.contains(row["geometry"]):
                colegios_zona.append(row["geometry"])

    
 
    
    # ========================================
    # VISUALIZACIÓN: MAPA DE ESTACIONES DE TRANSPORTE
    # ========================================
    st.markdown("""
    ### 🚇 Accesibilidad en Transporte Público

    En este mapa puedes visualizar todas las estaciones de transporte público dentro del área de análisis determinada. 
    Cada punto rojo representa una estación disponible alrededor del punto seleccionado, ayudándote a entender la conectividad y accesibilidad de la zona.

    El área sombreada muestra el alcance del entorno estudiado, manteniendo la uniformidad estética en todos los mapas y métricas urbanas.
    """)

    # Detecta las estaciones dentro de la zona circular de análisis
    estaciones_area = []
    estaciones_coords = []
    nombres_estaciones = []  # Nueva lista para almacenar nombres

    for _, row in transporte.iterrows():
        geom = row["geometry"]
        nombres_row = row.get("nombres", "Estación sin nombre")  # Obtener nombres de la fila
        
        # Separar nombres si hay múltiples estaciones (separadas por ";")
        lista_nombres = [n.strip() for n in str(nombres_row).split(";")]
        
        # Manejar Multipoint y Point simple
        if hasattr(geom, "geoms"):
            for idx, pt in enumerate(geom.geoms):
                if area_wgs.contains(pt):
                    coord_tuple = (pt.x, pt.y)
                    if coord_tuple not in estaciones_coords:
                        estaciones_area.append(pt)
                        estaciones_coords.append(coord_tuple)
                        # Asignar nombre correspondiente o genérico si no hay suficientes
                        nombre = lista_nombres[idx] if idx < len(lista_nombres) else lista_nombres[0]
                        nombres_estaciones.append(nombre)
        elif isinstance(geom, Point):
            if area_wgs.contains(geom):
                coord_tuple = (geom.x, geom.y)
                if coord_tuple not in estaciones_coords:
                    estaciones_area.append(geom)
                    estaciones_coords.append(coord_tuple)
                    nombres_estaciones.append(lista_nombres[0] if lista_nombres else "Estación")

    fig_transporte = go.Figure()

    # Render destacado y uniforme del área
    fig_transporte.add_trace(go.Scattermapbox(
        lat=list(area_wgs.exterior.xy[1]),
        lon=list(area_wgs.exterior.xy[0]),
        mode='lines',
        fill='toself',
        name=f'Área de análisis ({st.session_state.radio_analisis}m)',
        fillcolor='rgba(255, 165, 0, 0.12)',
        line=dict(color='orange', width=2)
    ))

    # Los puntos de estaciones con nombres reales en el tooltip
    if estaciones_area:
        lats = [pt.y for pt in estaciones_area]
        lons = [pt.x for pt in estaciones_area]

        fig_transporte.add_trace(go.Scattermapbox(
            lat=lats,
            lon=lons,
            mode='markers',
            name='Estaciones de Transporte',
            marker=dict(
                size=14,
                color='#E63946',
                opacity=0.95,
                symbol='circle'
            ),
            text=nombres_estaciones,  # Usar nombres reales
            hoverinfo='text'
        ))

    # Punto central seleccionado por el usuario
    fig_transporte.add_trace(go.Scattermapbox(
        lat=[st.session_state.punto_lat],
        lon=[st.session_state.punto_lon],
        mode='markers',
        name='Punto de interés',
        marker=dict(
            size=17,
            color='#3498DB'
        )
    ))

    fig_transporte.update_layout(
        mapbox_style="carto-positron",
        mapbox_center={"lat": st.session_state.punto_lat, "lon": st.session_state.punto_lon},
        mapbox_zoom=14,
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
        title=f"Estaciones de transporte público (radio {st.session_state.radio_analisis} m)",
        showlegend=True,
        height=600
    )

    st.plotly_chart(fig_transporte, use_container_width=True)

    # Métricas visuales uniformes
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Estaciones en el entorno", len(estaciones_area))
    with col2:
        if estaciones_area:
            densidad = len(estaciones_area) / (3.14159 * (st.session_state.radio_analisis / 1000) ** 2)
            st.metric("Densidad de estaciones\n (por km²)", f"{densidad:.2f}")


    # ========================================
    # VISUALIZACIÓN: MAPA DE CENTROS EDUCATIVOS
    # ========================================
    st.markdown("""
    ### 🏫 Oferta Educativa en el Entorno

    Visualiza todos los centros educativos dentro del área de análisis que seleccionaste. 
    Cada punto morado representa la ubicación de un colegio disponible para la comunidad, facilitando la evaluación de acceso educativo y nivel de cobertura del sector.

    El área sombreada corresponde a los metros de radio definidos, manteniendo la uniformidad visual en toda la plataforma.
    """)

    # Detectar colegios dentro del área circular de análisis
    colegios_area = []
    colegios_coords = []
    nombres_colegios = []  # Nueva lista para almacenar nombres

    for _, row in colegios.iterrows():
        geom = row["geometry"]
        nombres_row = row.get("nombres", "Colegio sin nombre")  # Obtener nombres de la fila
        
        # Separar nombres si hay múltiples colegios (separados por ";")
        lista_nombres = [n.strip() for n in str(nombres_row).split(";")]
        
        # Manejar MultiPoint y Point simple
        if hasattr(geom, "geoms"):
            for idx, pt in enumerate(geom.geoms):
                if area_wgs.contains(pt):
                    coord_tuple = (pt.x, pt.y)
                    if coord_tuple not in colegios_coords:
                        colegios_area.append(pt)
                        colegios_coords.append(coord_tuple)
                        # Asignar nombre correspondiente o genérico si no hay suficientes
                        nombre = lista_nombres[idx] if idx < len(lista_nombres) else lista_nombres[0]
                        nombres_colegios.append(nombre)
        elif isinstance(geom, Point):
            if area_wgs.contains(geom):
                coord_tuple = (geom.x, geom.y)
                if coord_tuple not in colegios_coords:
                    colegios_area.append(geom)
                    colegios_coords.append(coord_tuple)
                    nombres_colegios.append(lista_nombres[0] if lista_nombres else "Colegio")

    fig_educacion = go.Figure()

    # Área de análisis sombreada con estilo uniforme
    fig_educacion.add_trace(go.Scattermapbox(
        lat=list(area_wgs.exterior.xy[1]),
        lon=list(area_wgs.exterior.xy[0]),
        mode='lines',
        fill='toself',
        name=f'Área de análisis ({st.session_state.radio_analisis}m)',
        fillcolor='rgba(128, 0, 128, 0.07)',  # Morado muy suave
        line=dict(color='#6C3483', width=2)
    ))

    # Puntos de colegios con nombres reales en el tooltip
    if colegios_area:
        lats = [pt.y for pt in colegios_area]
        lons = [pt.x for pt in colegios_area]

        fig_educacion.add_trace(go.Scattermapbox(
            lat=lats,
            lon=lons,
            mode='markers',
            name='Colegios',
            marker=dict(
                size=13,
                color='#8E44AD',   # Morado
                opacity=0.88,
                symbol='circle'
            ),
            text=nombres_colegios,  # Usar nombres reales
            hoverinfo='text'
        ))

    # Punto central seleccionado por el usuario (azul estándar del flujo)
    fig_educacion.add_trace(go.Scattermapbox(
        lat=[st.session_state.punto_lat],
        lon=[st.session_state.punto_lon],
        mode='markers',
        name='Punto de interés',
        marker=dict(
            size=17,
            color='#3498DB'
        )
    ))

    fig_educacion.update_layout(
        mapbox_style="carto-positron",
        mapbox_center={"lat": st.session_state.punto_lat, "lon": st.session_state.punto_lon},
        mapbox_zoom=14,
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
        title=f"Centros educativos en el entorno ({len(colegios_area)} colegios)",
        showlegend=True,
        height=600
    )

    st.plotly_chart(fig_educacion, use_container_width=True)

    # Métricas profesionalizadas
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Colegios en el entorno", len(colegios_area))
    with col2:
        if colegios_area:
            densidad = len(colegios_area) / (3.14159 * (st.session_state.radio_analisis / 1000) ** 2)
            st.metric("Densidad educativa\n (por km²)", f"{densidad:.2f}")

        # ========================================
    # VISUALIZACIÓN: COMPOSICIÓN SOCIOECONÓMICA (ESTRATO)
    # ========================================
    st.markdown("""
    ### 🏘️ Composición Socioeconómica en el Entorno

    En este mapa exploramos cómo se distribuyen los diferentes estratos socioeconómicos dentro del área de análisis seleccionada.
    Cada polígono corresponde a una manzana urbana y el color representa el estrato predominante en cada una, ayudando a visualizar la diversidad y estructura social del sector.

    La leyenda te ayudará a identificar rápidamente cómo se organiza el tejido urbano alrededor de tu punto de interés.
    """)

    # Colores consistentes para cada estrato
    estratos_unicos = sorted(manzanas_zona["estrato"].unique())
    color_estrato = {
        1: '#8B0000',  # Rojo oscuro
        2: '#FF4500',  # Rojo naranja
        3: '#FFD700',  # Dorado
        4: '#90EE90',  # Verde claro
        5: '#4169E1',  # Azul real
        6: '#9370DB'   # Púrpura medio
    }

    fig_estrato = go.Figure()

    # Marco del área de análisis (naranja uniforme con el resto)
    fig_estrato.add_trace(go.Scattermapbox(
        lat=list(area_wgs.exterior.xy[1]),
        lon=list(area_wgs.exterior.xy[0]),
        mode='lines',
        name=f'Área de análisis ({st.session_state.radio_analisis}m)',
        line=dict(color='orange', width=2),
        showlegend=False
    ))

    # Agrupa y pinta las manzanas por estrato, leyenda compacta
    trazas_agregadas = set()
    for estrato in estratos_unicos:
        manzanas_estrato = manzanas_zona[manzanas_zona["estrato"] == estrato]
        for idx, (_, manzana) in enumerate(manzanas_estrato.iterrows()):
            if manzana.geometry.geom_type == 'Polygon':
                coords = list(manzana.geometry.exterior.coords)
                mostrar_leyenda = estrato not in trazas_agregadas
                if mostrar_leyenda:
                    trazas_agregadas.add(estrato)
                fig_estrato.add_trace(go.Scattermapbox(
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

    # Punto central uniformado
    fig_estrato.add_trace(go.Scattermapbox(
        lat=[st.session_state.punto_lat],
        lon=[st.session_state.punto_lon],
        mode='markers',
        name='Punto de interés',
        marker=dict(
            size=17,
            color='#3498DB'
        ),
        showlegend=True
    ))

    fig_estrato.update_layout(
        mapbox_style="carto-positron",
        mapbox_center={"lat": st.session_state.punto_lat, "lon": st.session_state.punto_lon},
        mapbox_zoom=14,
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
        title="Distribución de estratos socioeconómicos",
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

    st.plotly_chart(fig_estrato, use_container_width=True)

    # Distribución gráfica y numérica (profesional)
    st.markdown("**Resumen visual de estratos en el entorno:**")
    dist_estratos = manzanas_zona["estrato"].value_counts().sort_index()
    col1, col2 = st.columns([1, 1])
    with col1:
        for estrato, cantidad in dist_estratos.items():
            porcentaje = cantidad / len(manzanas_zona) * 100
            st.write(f"- Estrato {estrato}: {cantidad} manzanas ({porcentaje:.1f}%)")
    with col2:
        fig_estratobarras = go.Figure(data=[
            go.Bar(
                x=[f"E{e}" for e in dist_estratos.index],
                y=dist_estratos.values,
                marker_color=[color_estrato.get(e, '#808080') for e in dist_estratos.index],
                text=dist_estratos.values,
                textposition='auto',
            )
        ])
        fig_estratobarras.update_layout(
            title="Cantidad de manzanas por estrato",
            xaxis_title="Estrato",
            yaxis_title="Cantidad",
            height=300,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig_estratobarras, use_container_width=True)

        # ========================================
    # VISUALIZACIÓN: USO DEL SUELO SEGÚN PLAN DE ORDENAMIENTO TERRITORIAL (POT)
    # ========================================
    st.markdown("""
    ### 🗺️ Distribución de Usos del Suelo (POT)

    Este mapa te permite entender cómo están organizados los usos del suelo dentro del área de análisis, según la planificación oficial de Bogotá (POT).
    Cada color corresponde a una categoría de uso (residencial, dotacional, comercial, servicios, etc.), facilitando la identificación de zonas homogéneas, mixtas o de oportunidad.

    Observa la composición y diversificación del entorno alrededor de tu punto de interés.
    """)

    # Unificar con áreas POT de la zona y asignar colores
    if "id_area" in manzanas_zona.columns and not areas.empty:
        manzanas_pot = manzanas_zona.merge(
            areas[["id_area", "uso_pot_simplificado"]],
            on="id_area",
            how="left"
        )
        manzanas_pot["uso_pot_simplificado"] = manzanas_pot["uso_pot_simplificado"].fillna("Sin clasificación")
    else:
        manzanas_pot = manzanas_zona.copy()
        manzanas_pot["uso_pot_simplificado"] = "Sin clasificación"

    usos_pot = sorted(manzanas_pot["uso_pot_simplificado"].unique())
    palette_pot = px.colors.qualitative.Plotly
    color_pot_map = {uso: palette_pot[i % len(palette_pot)] for i, uso in enumerate(usos_pot)}

    fig_pot = go.Figure()

    # Marco de área de análisis uniforme
    fig_pot.add_trace(go.Scattermapbox(
        lat=list(area_wgs.exterior.xy[1]),
        lon=list(area_wgs.exterior.xy[0]),
        mode='lines',
        name='Área de análisis',
        line=dict(color='orange', width=2),
        showlegend=False
    ))

    trazas_agregadas_pot = set()
    for uso in usos_pot:
        manzanas_uso = manzanas_pot[manzanas_pot["uso_pot_simplificado"] == uso]
        for idx, (_, manzana) in enumerate(manzanas_uso.iterrows()):
            if manzana.geometry.geom_type == 'Polygon':
                coords = list(manzana.geometry.exterior.coords)
                mostrar_leyenda = uso not in trazas_agregadas_pot
                if mostrar_leyenda:
                    trazas_agregadas_pot.add(uso)
                fig_pot.add_trace(go.Scattermapbox(
                    lat=[c[1] for c in coords],
                    lon=[c[0] for c in coords],
                    mode='lines',
                    fill='toself',
                    fillcolor=color_pot_map.get(uso, '#808080'),
                    line=dict(color='black', width=0.5),
                    name=uso,
                    showlegend=mostrar_leyenda,
                    legendgroup=f'pot_{uso}',
                    hovertext=uso,
                    hoverinfo='text'
                ))

    # Punto central (azul uniforme)
    fig_pot.add_trace(go.Scattermapbox(
        lat=[st.session_state.punto_lat],
        lon=[st.session_state.punto_lon],
        mode='markers',
        name='Punto de interés',
        marker=dict(
            size=17,
            color='#3498DB'
        ),
        showlegend=True
    ))

    fig_pot.update_layout(
        mapbox_style="carto-positron",
        mapbox_center={"lat": st.session_state.punto_lat, "lon": st.session_state.punto_lon},
        mapbox_zoom=14,
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
        title="Distribución de usos del suelo según el POT",
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

    st.plotly_chart(fig_pot, use_container_width=True)

    # Distribución visual y texto
    st.markdown("**Resumen de usos del suelo en el área de análisis:**")
    dist_pot = manzanas_pot["uso_pot_simplificado"].value_counts()
    col1, col2 = st.columns([1, 1])
    with col1:
        for uso, cantidad in dist_pot.items():
            porcentaje = cantidad / len(manzanas_pot) * 100
            st.write(f"- {uso}: {cantidad} manzanas ({porcentaje:.1f}%)")
    with col2:
        fig_pot_barras = go.Figure(data=[
            go.Bar(
                x=[uso[:20] + '...' if len(uso) > 20 else uso for uso in dist_pot.index],
                y=dist_pot.values,
                marker_color=[color_pot_map.get(uso, '#808080') for uso in dist_pot.index],
                text=dist_pot.values,
                textposition='auto',
            )
        ])
        fig_pot_barras.update_layout(
            title="Cantidad de manzanas por uso POT",
            xaxis_title="Uso del suelo",
            yaxis_title="Cantidad",
            height=300,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig_pot_barras, use_container_width=True)

        
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
