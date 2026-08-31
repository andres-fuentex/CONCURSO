# importacion de librerias necesarioas
import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium
from shapely.geometry import Point
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import os
import urllib.parse

# Configuración de la Página
st.set_page_config(
    page_title="Bogotá Inteligente",
    page_icon="💛", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# INICIO: MOSTRAR LOGO EN CABECERA
ruta_logo = "BACK_END/logo.png"

# columnas para centrarlo o ajustarlo
col_logo1, col_logo2, col_logo3 = st.columns([1, 2, 1])

with col_logo2:
    if os.path.exists(ruta_logo):
        
        st.image(ruta_logo, width=350, caption="Datos al Ecosistema 2025")
    else:
        # Fallback por si la imagen no carga
        st.title("🏙️ Bogotá Inteligente")
        st.warning(f"Nota: No se encontró el logo en '{ruta_logo}'")

st.markdown("---")

# Inyección de Estilos

st.markdown("""
    <style>
        /* Títulos en Rojo Bogotá */
        h1 { color: #DA291C; font-family: 'Helvetica', sans-serif; font-weight: 800; }
        h2, h3 { color: #2C3E50; }
        
        /* Resaltados en Amarillo */
        .highlight { background-color: #F1C40F; padding: 2px 5px; border-radius: 3px; color: #000; font-weight: bold; }
        
        /* Caja de introducción limpia */
        .intro-box { 
            background-color: #f8f9fa; 
            padding: 20px; 
            border-left: 5px solid #DA291C; 
            border-radius: 5px; 
            font-size: 1.1em;
        }
    </style>
""", unsafe_allow_html=True)

# Encabezado y Bienvenida 
st.title("Bogotá Inteligente: Tu Barrio en Datos 🏙️")
st.subheader("Toma decisiones inteligentes sobre el territorio de tu ciudad.")

# Texto introductorio
st.markdown("""
<div class="intro-box">
    ¿Alguna vez te has preguntado qué tan seguro es realmente un barrio, qué colegios tiene cerca o qué se puede construir allí?<br><br>
    Esta herramienta conecta los <b>datos oficiales de la ciudad</b> contigo. Olvídate de los mapas complicados; aquí traducimos la información técnica en respuestas claras para que conozcas la vocación real de cualquier rincón de Bogotá.
</div>
""", unsafe_allow_html=True)

st.write("")

# Explicación de valor con iconos
col_info1, col_info2, col_info3, col_info4, col_info5,  col_info6 = st.columns(6)

with col_info1:
    st.markdown("### 👮 Seguridad")
    st.info("Conoce el **Top 3 de delitos** reales. No es lo mismo un barrio donde roban celulares a uno con hurto de casas.")

with col_info2:
    st.markdown("### 🏡 Normativa")
    st.warning("Consulta el POT vigente. Descubre si tu vecino será un edificio residencial o una zona industrial ruidosa.")

with col_info3:
    st.markdown("### 🚌 Movilidad")
    st.success("Mide la conectividad real. Ubica las estaciones de **Transmilenio y SITP** a pasos de tu ubicación.")

with col_info4:
    st.markdown("### 🏫 Educación")
    st.error("Para las familias: encuentra la oferta de **Colegios Oficiales y Privados** en el sector.")

with col_info5:
    st.markdown("### 🩺 Salud")
    st.info("Prioriza el cuidado. Ubica la red de **Hospitales y Clínicas (IPS)** disponibles.")

with col_info6:
    st.markdown("### 🌳 Zonas Verdes")
    st.success("Respira mejor. Encuentra las **Zonas Verdes** ideales para el deporte, el descanso o pasear a tu mascota.")

st.markdown("---")


# Función de Carga de Datos (Conectada a DATOS_LIMPIOS)
@st.cache_data
def cargar_datasets():
    """
    Descarga, valida y cachea los datasets geoespaciales.
    Forzamos la corrección de coordenadas para Verde y Salud.
    """
    BASE_URL = "https://github.com/andres-fuentex/CONCURSO/raw/main/DATOS_LIMPIOS/"
    
    archivos = {
        "localidades": "dim_localidad.geojson",
        "areas":       "dim_area.geojson",
        "manzanas":    "tabla_hechos.geojson",
        "transporte":  "dim_transporte.geojson",
        "colegios":    "dim_colegios.geojson",
        "salud":       "dim_salud.geojson", 
        "verde":       "dim_verde.geojson"
    }
    
    dataframes = {}
    errores = []

    for nombre_clave, nombre_archivo in archivos.items():
        try:
            url_completa = f"{BASE_URL}{nombre_archivo}"
            gdf = gpd.read_file(url_completa)
            
            # --- CURACIÓN ESPECÍFICA DE COORDENADAS ---
            
            # CASO 1: PARQUES (dim_verde)
            # Vienen en planas (91130...), hay que decirles que son Bogotá (3116) y pasar a GPS (4326)
            if nombre_clave == "verde":
                if gdf.crs is None:
                    gdf.set_crs(epsg=3116, inplace=True) # Asumimos Magna Bogotá
                gdf = gdf.to_crs(epsg=4326) # Convertimos a GPS
            
            # CASO 2: SALUD (dim_salud)
            # Vienen en GPS (-74...), pero a veces sin etiqueta. Aseguramos que sea 4326.
            elif nombre_clave == "salud":
                if gdf.crs is None:
                    gdf.set_crs(epsg=4326, inplace=True)
                else:
                    gdf = gdf.to_crs(epsg=4326)

            # CASO 3: EL RESTO
            # Verificación estándar
            else:
                if gdf.crs is None:
                    gdf.set_crs(epsg=4326, inplace=True)
                elif gdf.crs.to_string() != "EPSG:4326":
                    gdf = gdf.to_crs("EPSG:4326")
                
            dataframes[nombre_clave] = gdf
            
        except Exception as e:
            errores.append(f"Error cargando {nombre_clave}: {str(e)}")
    
    if errores:
        for err in errores:
            st.error(err)
        return None
        
    return dataframes

# Inicialización del Estado
if "step" not in st.session_state:
    st.session_state.step = 1


# PASO 1: SINCRONIZACIÓN Y CARGA DE DATOS

if st.session_state.step == 1:
    st.markdown("### 🔌 Conectando con tu Ciudad")
    
    st.markdown("""
    Para darte un diagnóstico confiable, estamos conectando en tiempo real con el repositorio de **Datos Abiertos de Bogotá**.
    
    Este proceso garantiza que consultes la información más reciente sobre:
    * 🛡️ **Seguridad:** Datos directos de la Secretaría de Seguridad.
    * 🗺️ **Normativa:** Reglas de juego del POT (Decreto 555).
    * 🚌 **Infraestructura:** Red oficial de Transmilenio y Educación.
    * 🌳 **Calidad de vida:** acceso a servicios de salud y zonas verdes.
    """)

    # CSS PARA BOTÓN VERDE
    st.markdown("""
        <style>
        /* Forzamos el estilo del botón solo para que sea Verde Éxito */
        div.stButton > button {
            background-color: #27AE60 !important; /* Verde Esmeralda */
            color: white !important;
            font-weight: bold;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 5px;
        }
        div.stButton > button:hover {
            background-color: #2ECC71 !important; /* Verde más claro al pasar mouse */
            color: white !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # Usamos spinner
    with st.spinner("⏳ Sincronizando mapas y estadísticas oficiales... por favor espera."):
        try:
            # Ejecutamos la carga
            dataframes = cargar_datasets()
            
            if dataframes:
                # Guardamos en memoria silenciosamente
                st.session_state.update(dataframes)
                
                # Mensaje de  limpio
                st.success("✅ **¡Conexión Exitosa!** Todos los datos de Bogotá están listos para tu análisis.")
                
                st.markdown("---")
                
                # Botón de acción centrado 
                col_izq, col_centro, col_der = st.columns([1, 2, 1])
                with col_centro:
                    if st.button("📍 Comenzar a Explorar", use_container_width=True):
                        st.session_state.step = 2
                        st.rerun()
            else:
                st.error("❌ No pudimos conectar con los datos. Por favor revisa tu internet.")
                
        except Exception as e:
            st.error(f"Ocurrió un error técnico: {e}")


# PASO 2: SELECCIÓN DE LOCALIDAD (EXPERIENCIA MEJORADA)

elif st.session_state.step == 2:
    # CSS PERSONALIZADO PARA BOTONES
    st.markdown("""
        <style>
        /* 1. Estilo para el botón PRINCIPAL (Verde - Confirmar) */
        /* Buscamos botones con el atributo kind="primary" */
        div.stButton > button[kind="primary"] {
            background-color: #27AE60 !important;
            border-color: #27AE60 !important;
            color: white !important;
            font-size: 16px !important;
            border-radius: 8px !important;
            height: 50px !important;
            transition: all 0.3s ease;
        }
        div.stButton > button[kind="primary"]:hover {
            background-color: #2ECC71 !important;
            border-color: #2ECC71 !important;
            transform: scale(1.02);
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }

        /* 2. Estilo para el botón SECUNDARIO (Gris - Volver) */
        /* Buscamos botones normales (kind="secondary") */
        div.stButton > button[kind="secondary"] {
            background-color: #95A5A6 !important;
            border-color: #95A5A6 !important;
            color: white !important;
            border-radius: 8px !important;
            height: 50px !important;
        }
        div.stButton > button[kind="secondary"]:hover {
            background-color: #7F8C8D !important;
            border-color: #7F8C8D !important;
            color: white !important;
        }
        </style>
    """, unsafe_allow_html=True)

    st.header("🗺️ Paso 2: Ubica tu Localidad")

    col_mapa, col_datos = st.columns([3, 1])

    with col_datos:
        st.markdown("### ¿Cómo funciona?")
        st.info("""
        Bogotá tiene 20 localidades, cada una con su propia identidad.
        
        👉 **Haz clic en el mapa** sobre la zona que te interesa investigar.
        
        El sistema te mostrará inmediatamente los **3 delitos más frecuentes** en esa zona para que conozcas el contexto real antes de seguir.
        """)
        
        st.markdown("---")
        # Botón de regreso
        if st.button("⬅ Volver al Inicio", type="secondary", use_container_width=True):
            st.session_state.step = 1
            st.rerun()

    with col_mapa:
        # Colores Identidad 
        COLOR_BASE = "#776314"     # Amarillo
        COLOR_LINEA = "#1B0BA8"    # Azul
        COLOR_HOVER = "#AA1A0F"    # Rojo 

        localidades = st.session_state.localidades
        centro_urbano = [4.6097, -74.0817] 

        m = folium.Map(
            location=centro_urbano, 
            zoom_start=11, 
            tiles="OpenStreetMap",
            control_scale=True
        )
        
        folium.GeoJson(
            localidades,
            style_function=lambda feature: {
                "fillColor": COLOR_BASE,
                "color": COLOR_LINEA,
                "weight": 2,
                "fillOpacity": 0.5,
            },
            highlight_function=lambda feature: {
                "fillColor": COLOR_HOVER,
                "color": "white",
                "weight": 3,
                "fillOpacity": 0.7,
            },
            tooltip=folium.GeoJsonTooltip(
                fields=["nombre_localidad"],
                aliases=["Localidad:"],
                style="font-family: sans-serif; font-size: 14px;",
                sticky=True
            )
        ).add_to(m)

        output = st_folium(m, width=None, height=550, returned_objects=["last_clicked"])

    # Lógica de Selección y Ranking
    clicked = output.get("last_clicked")
    contenedor_resultado = st.container()

    if clicked and "lat" in clicked and "lng" in clicked:
        punto = Point(clicked["lng"], clicked["lat"])
        
        seleccion = None
        perfil_seguridad = "Sin datos"
        
        for _, row in localidades.iterrows():
            if row["geometry"].contains(punto):
                seleccion = row["nombre_localidad"]
                if "top_3_delitos" in row:
                    perfil_seguridad = row["top_3_delitos"]
                break
        
        if seleccion:
            st.session_state.localidad_clic = seleccion
            
            with contenedor_resultado:
                st.markdown("---")
                col_res1, col_res2, col_res3 = st.columns([1, 1.5, 1])
                
                with col_res1:
                    st.markdown(f"### 📍 {seleccion}")
                    st.caption("Has seleccionado esta zona.")
                
                with col_res2:
                    
                    st.markdown("**🚨 Top 3 Riesgos de Seguridad:**")
                    
                    if "," in perfil_seguridad:
                        delitos = perfil_seguridad.split(",")
                        html_lista = ""
                        iconos = ["🥇", "🥈", "🥉"] 
                        
                        for i, delito in enumerate(delitos):
                            if i < 3: 
                                texto_delito = delito.split(".")[-1].strip() if "." in delito else delito.strip()
                                html_lista += f"<div style='margin-bottom:5px; font-size:15px;'>{iconos[i]} <b>{texto_delito}</b></div>"
                        
                        st.markdown(html_lista, unsafe_allow_html=True)
                    else:
                        st.info(perfil_seguridad)
                
                with col_res3:
                    st.write("") 
                    st.write("") 
                    
                    if st.button("🔍 Analizar esta Zona", type="primary", use_container_width=True):
                        st.session_state.localidad_sel = seleccion
                        st.session_state.step = 3
                        st.rerun()


# PASO 3: DEFINICIÓN DEL ENTORNO DE ANÁLISIS

elif st.session_state.step == 3:
    st.header("📍 Paso 3: Define tu Entorno de Análisis")

    # CSS Botón Verde
    st.markdown("""
        <style>
        div.stButton > button[kind="primary"] {
            background-color: #27AE60 !important;
            color: white !important;
            border-radius: 8px;
        }
        </style>
    """, unsafe_allow_html=True)

    
    # 1. BARRA LATERAL DE CONTROLES
    
    col_controles, col_mapa = st.columns([1, 2])

    with col_controles:
        
        st.markdown(f"### 1. Ubicación en {st.session_state.localidad_sel}")
        st.info("Haz clic en el mapa para marcar el punto exacto.")
        
        st.markdown("---")
        
        st.markdown("### 2. Alcance")
        radio_analisis = st.select_slider(
            "¿Qué tan lejos quieres mirar?",
            options=[300, 600, 900, 1200, 1500, 1800, 2100],
            value=st.session_state.get('radio_analisis', 600),
            help="Define el radio del círculo rojo en el mapa."
        )
        st.session_state.radio_analisis = radio_analisis

        tiempo_caminata = int(radio_analisis / 80)
        if radio_analisis <= 600:
            desc_radio = "🚶‍♂️ **Vecindario (5-8 min):** Comercio local."
        elif radio_analisis <= 1200:
            desc_radio = "🚲 **Barrio (10-15 min):** Colegios y rutas."
        else:
            desc_radio = "🚗 **Zona Amplia:** Impacto zonal."
            
        st.caption(f"{desc_radio}")

    
    # 2. MAPA INTERACTIVO  CENTRADO DINÁMICO
    
    with col_mapa:
        localidades = st.session_state.localidades
        localidad_geo = localidades[localidades["nombre_localidad"] == st.session_state.localidad_sel]
        
        bounds = localidad_geo.total_bounds
        
        
        if "punto_lat" in st.session_state:
            # Si hay pin, centramos en el pin y hacemos ZOOM IN 
            centro_mapa = [st.session_state.punto_lat, st.session_state.punto_lon]
            zoom_inicial = 15
        else:
            # Si no hay pin, centramos en la localidad con ZOOM OUT 
            centro_mapa = [(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2]
            zoom_inicial = 13

        m = folium.Map(
            location=centro_mapa,
            zoom_start=zoom_inicial,
            tiles="OpenStreetMap",
            control_scale=True
        )

        folium.GeoJson(
            localidad_geo,
            style_function=lambda x: {
                "fillColor": "#F1C40F",  # Mantenemos tu amarillo
                "color": "#DA291C",      # Borde color Rojo Bogotá para que contraste
                "weight": 3,             # Borde un poco más grueso
                "fillOpacity": 0.35,     # Aumentamos la opacidad para que no se pierda con las calles
                "dashArray": "5, 5"
            }
        ).add_to(m)

        m.get_root().html.add_child(folium.Element("""
            <style>.leaflet-container { cursor: crosshair !important; }</style>
        """))

        if "punto_lat" in st.session_state:
            folium.Marker(
                [st.session_state.punto_lat, st.session_state.punto_lon],
                icon=folium.Icon(color="red", icon="info-sign"),
                tooltip="Punto de Análisis"
            ).add_to(m)
            
            folium.Circle(
                location=[st.session_state.punto_lat, st.session_state.punto_lon],
                radius=st.session_state.radio_analisis,
                color="#E74C3C",
                fill=True,
                fill_opacity=0.2
            ).add_to(m)

        mapa_output = st_folium(m, width=None, height=500, returned_objects=["last_clicked"])

    
    # 3. LÓGICA Y BOTONES
    
    
    clicked = mapa_output.get("last_clicked")
    if clicked and "lat" in clicked and "lng" in clicked:
        punto_temp = Point(clicked["lng"], clicked["lat"])
        
        if localidad_geo.geometry.iloc[0].contains(punto_temp):
            st.session_state.punto_lat = clicked["lat"]
            st.session_state.punto_lon = clicked["lng"]
            st.rerun() 
        else:
            st.toast("⚠️ El punto está fuera de la localidad. Intenta más adentro.", icon="🚫")

    st.markdown("---")
    
    col_atras, col_accion = st.columns([1, 4])
    
    with col_atras:
        
        if st.button("⬅ Atrás"):
            # Borramos el punto para que si vuelve a entrar, el mapa esté limpio
            for key in ['punto_lat', 'punto_lon']:
                if key in st.session_state: del st.session_state[key]
            st.session_state.step = 2
            st.rerun()
            
    with col_accion:
        if "punto_lat" in st.session_state:
            if st.button("🚀 Generar Diagnóstico Completo", type="primary", use_container_width=True):
                st.session_state.step = 5
                st.rerun()
        else:
            st.info("👈 Por favor, haz clic en el mapa para continuar.")



# PASO 5: RESULTADOS DEL ANÁLISIS (DASHBOARD FINAL)

elif st.session_state.step == 5:
    st.header("📊 Resultados de tu Análisis")

    st.info(f"""
    **Estás analizando:** Un radio de **{st.session_state.radio_analisis} metros** a la redonda.
    📍 **Punto exacto:** En la localidad de **{st.session_state.localidad_sel}**.
    """)

    
    # 1. MOTOR DE CÁLCULO ESPACIAL
    
    localidades = st.session_state.localidades
    manzanas    = st.session_state.manzanas
    transporte  = st.session_state.transporte
    colegios    = st.session_state.colegios
    areas_pot   = st.session_state.areas

    # nuevos 
    salud = st.session_state.salud
    verde = st.session_state.verde

    # 1.1 Buffer de Análisis
    punto_ref = Point(st.session_state.punto_lon, st.session_state.punto_lat)
    gdf_punto = gpd.GeoDataFrame([{'geometry': punto_ref}], crs="EPSG:4326")
    gdf_buffer = gdf_punto.to_crs(epsg=3116).buffer(st.session_state.radio_analisis).to_crs(epsg=4326)
    area_interes = gdf_buffer.iloc[0]

    # 1.2 Asegurar Proyecciones Idénticas
    if transporte.crs != "EPSG:4326": transporte = transporte.to_crs("EPSG:4326")
    if colegios.crs != "EPSG:4326": colegios = colegios.to_crs("EPSG:4326")
    if manzanas.crs != "EPSG:4326": manzanas = manzanas.to_crs("EPSG:4326")
    if areas_pot.crs != "EPSG:4326": areas_pot = areas_pot.to_crs("EPSG:4326")
    if salud.crs != "EPSG:4326": salud = salud.to_crs("EPSG:4326")
    if verde.crs != "EPSG:4326": verde = verde.to_crs("EPSG:4326")

    

    # 1.3 Cruces Espaciales 
    transporte_zona = transporte[transporte.geometry.intersects(area_interes)]
    colegios_zona = colegios[colegios.geometry.intersects(area_interes)]
    manzanas_zona = manzanas[manzanas.geometry.intersects(area_interes)]
    # nuevos
    salud_zona = salud[salud.geometry.intersects(area_interes)]
    parques_zona = verde[verde.geometry.intersects(area_interes)]
    
    cant_salud = len(salud_zona)
    cant_parques = len(parques_zona)

    # SECCIÓN 1: MOVILIDAD
   
    st.markdown("---")
    st.markdown("### 🚌 1. ¿Qué tan fácil es moverse?")
    st.markdown("Analizamos qué opciones de transporte público (Transmilenio y SITP) tienes 'a la mano'.")

    col_mapa_mov, col_data_mov = st.columns([2, 1])

    with col_mapa_mov:
        fig_t = go.Figure()
        # Zona
        fig_t.add_trace(go.Scattermap(
            lat=list(area_interes.exterior.xy[1]), lon=list(area_interes.exterior.xy[0]),
            mode='lines', fill='toself', name='Zona analizada',
            fillcolor='rgba(255, 165, 0, 0.1)', line=dict(color='orange', width=2)
        ))
        # Estaciones
        if not transporte_zona.empty:
            fig_t.add_trace(go.Scattermap(
                lat=transporte_zona.geometry.y, lon=transporte_zona.geometry.x,
                mode='markers', name='Paraderos',
                marker=dict(size=10, color='#E74C3C', symbol='circle'),
                text=transporte_zona['nombre_estacion'], hoverinfo='text'
            ))
        # Tú
        fig_t.add_trace(go.Scattermap(
            lat=[st.session_state.punto_lat], lon=[st.session_state.punto_lon],
            mode='markers', name='Tú', marker=dict(size=12, color='#3498DB')
        ))
        fig_t.update_layout(
            map_style="carto-positron", 
            map_center={"lat": st.session_state.punto_lat, "lon": st.session_state.punto_lon},
            map_zoom=14, margin={"r":0,"t":0,"l":0,"b":0}, height=350, showlegend=True,
            legend=dict(orientation="h", y=1.1)
        )
        st.plotly_chart(fig_t, use_container_width=True)

    with col_data_mov:
        cant_t = len(transporte_zona)
        st.metric("Puntos de Transporte", cant_t)
        
        if cant_t > 2:
            st.success("✅ **Excelente Conectividad:**\nTienes muchas opciones de ruta cerca.")
        elif cant_t > 0:
            st.warning("⚠️ **Conectividad Media:**\nTienes transporte, pero quizás debas caminar un poco.")
        else:
            st.error("❌ **Zona Apartada:**\nDependerás de vehículo particular o caminatas largas.")

    

    
    # SECCIÓN 2: EDUCACIÓN
    
    st.markdown("---")
    st.markdown("### 🏫 2. ¿Dónde pueden estudiar tus hijos?")
    st.markdown("Ubicación de colegios oficiales y privados en el vecindario.")

    col_mapa_edu, col_data_edu = st.columns([2, 1])

    with col_mapa_edu:
        fig_e = go.Figure()
        fig_e.add_trace(go.Scattermap(
            lat=list(area_interes.exterior.xy[1]), lon=list(area_interes.exterior.xy[0]),
            mode='lines', fill='toself', name='Zona analizada',
            fillcolor='rgba(155, 89, 182, 0.1)', line=dict(color='#8E44AD', width=2)
        ))
        if not colegios_zona.empty:
            fig_e.add_trace(go.Scattermap(
                lat=colegios_zona.geometry.y, lon=colegios_zona.geometry.x,
                mode='markers', name='Colegios',
                marker=dict(size=9, color='#8E44AD', symbol='circle'),
                text=colegios_zona['nombre'], hoverinfo='text'
            ))
        fig_e.add_trace(go.Scattermap(
            lat=[st.session_state.punto_lat], lon=[st.session_state.punto_lon],
            mode='markers', name='Tú', marker=dict(size=12, color='#3498DB')
        ))
        fig_e.update_layout(
            map_style="carto-positron", 
            map_center={"lat": st.session_state.punto_lat, "lon": st.session_state.punto_lon},
            map_zoom=14, margin={"r":0,"t":0,"l":0,"b":0}, height=350, showlegend=False
        )
        st.plotly_chart(fig_e, use_container_width=True)

    with col_data_edu:
        cant_c = len(colegios_zona)
        st.metric("Total Colegios", cant_c)
        
        if cant_c > 4:
            st.success("✅ **Alta Oferta Educativa:**\nVariedad de opciones para las familias.")
        elif cant_c > 0:
            st.info("ℹ️ **Oferta Moderada:**\nColegios accesibles en el sector.")
        else:
            st.error("❌ **Déficit Educativo:**\nNo se identifican colegios en el radio inmediato.")

        if not colegios_zona.empty:
            st.caption("Por tipo:")
            st.dataframe(colegios_zona['sector'].value_counts(), use_container_width=True)

    # --- SECCIÓN SALUD ---
    st.markdown("---")
    st.markdown("### 🩺 5. Salud y Bienestar")
    st.markdown("Identificamos la oferta de servicios médicos (IPS, Hospitales, Clínicas) en tu radio cercano.")

    col_mapa_salud, col_data_salud = st.columns([2, 1])

    with col_mapa_salud:
        fig_s = go.Figure()
        
        # 1. Zona (Círculo Naranja)
        fig_s.add_trace(go.Scattermap(
            lat=list(area_interes.exterior.xy[1]), lon=list(area_interes.exterior.xy[0]),
            mode='lines', fill='toself', name='Zona analizada',
            fillcolor='rgba(255, 165, 0, 0.1)', line=dict(color='orange', width=2)
        ))
        
        # 2. Hospitales (Puntos)
        if not salud_zona.empty:
            fig_s.add_trace(go.Scattermap(
                lat=salud_zona.geometry.y, lon=salud_zona.geometry.x,
                mode='markers', name='Salud',
                # Usamos símbolo de cruz y color Rojo
                marker=dict(size=12, color="#0905F7", symbol='circle'),
                # Ajusta 'nombre_hospital' si tu columna se llama diferente
                text=salud_zona.get('nombre_hospital', 'Centro de Salud'), 
                hoverinfo='text'
            ))
            
        # 3. Tú (Punto Azul)
        fig_s.add_trace(go.Scattermap(
            lat=[st.session_state.punto_lat], lon=[st.session_state.punto_lon],
            mode='markers', name='Tú', marker=dict(size=12, color='#3498DB')
        ))
        
        # Configuración igual a Movilidad
        fig_s.update_layout(
            map_style="carto-positron", 
            map_center={"lat": st.session_state.punto_lat, "lon": st.session_state.punto_lon},
            map_zoom=14, margin={"r":0,"t":0,"l":0,"b":0}, height=350, showlegend=True,
            legend=dict(orientation="h", y=1.1)
        )
        st.plotly_chart(fig_s, use_container_width=True, key="mapa_salud_unico")

    with col_data_salud:
        cant_s = len(salud_zona)
        st.metric("Centros de Salud", cant_s)
        
        if cant_s > 1:
            st.success("✅ **Zona Cubierta:**\nAcceso rápido a atención médica.")
        elif cant_s == 1:
            st.warning("⚠️ **Cobertura Básica:**\nTienes un centro de salud cerca.")
        else:
            st.error("❌ **Sin Cobertura Inmediata:**\nNo hay hospitales en este radio exacto.")

    # --- SECCIÓN PARQUES (POLÍGONOS) ---
    st.markdown("---")
    st.markdown("### 🌳 6. Espacio Público y Verde")
    st.markdown("Zonas de recreación, deporte y descanso al aire libre.")

    col_mapa_ver, col_data_ver = st.columns([2, 1])

    with col_mapa_ver:
        fig_v = go.Figure()
        
        # 1. Zona de Análisis (Círculo Naranja)
        fig_v.add_trace(go.Scattermap(
            lat=list(area_interes.exterior.xy[1]), lon=list(area_interes.exterior.xy[0]),
            mode='lines', fill='toself', name='Zona analizada',
            fillcolor='rgba(255, 165, 0, 0.05)', # Muy transparente
            line=dict(color='orange', width=2)
        ))
        
        # 2. PARQUES (POLÍGONOS REALES)
        if not parques_zona.empty:
            # Importamos json aquí por si acaso
            import json
            # Convertimos las geometrías a GeoJSON para pintarlas
            geojson_parques = json.loads(parques_zona.to_json())
            
            # Usamos Choroplethmap para pintar el relleno verde
            fig_v.add_trace(go.Choroplethmap(
                geojson=geojson_parques,
                locations=parques_zona.index, # ID de enlace
                z=[1] * len(parques_zona),    # Valor dummy para color uniforme
                colorscale=[[0, '#27AE60'], [1, '#27AE60']], # Verde 'Jardín'
                showscale=False,              # Sin barra de colores
                marker_opacity=0.7,
                marker_line_width=1,
                marker_line_color='white',
                name='Zonas Verdes',
                # Texto al pasar el mouse
                text=parques_zona.get('nombre_parque', 'Parque / Zona Verde'),
                hoverinfo='text'
            ))
            
        # 3. Tú 
        fig_v.add_trace(go.Scattermap(
            lat=[st.session_state.punto_lat], lon=[st.session_state.punto_lon],
            mode='markers', name='Tú', marker=dict(size=14, color='#2980B9', symbol='circle')
        ))
        
        fig_v.update_layout(
            map_style="carto-positron", 
            map_center={"lat": st.session_state.punto_lat, "lon": st.session_state.punto_lon},
            map_zoom=14.5, margin={"r":0,"t":0,"l":0,"b":0}, height=350, showlegend=True,
            legend=dict(orientation="h", y=1.1)
        )
        st.plotly_chart(fig_v, use_container_width=True, key="mapa_parques_poligonos")

    with col_data_ver:
        cant_p = len(parques_zona)
        st.metric("Parques Cercanos", cant_p)
        
        
        if cant_p > 4:
            st.success("✅ **¡Entorno Privilegiado!**\nTienes múltiples opciones para salir a correr, pasear a tu mascota o desconectarte del ruido.")
        elif cant_p > 0:
            st.info("🏃 **Vida Activa:**\nTienes espacios verdes a la mano para tu rutina diaria de ejercicio o descanso.")
        else:
            st.error("🏢 **Entorno 100% Urbano:**\nEstás en una zona densa. Tendrás que desplazarte un poco para encontrar zonas verdes amplias.")



    # SECCIÓN 3: ESTRATIFICACIÓN
    
    st.markdown("---")
    st.markdown("### 🏘️ 3. ¿Cómo es el vecindario? (Estratos)")
    st.markdown("Nivel socioeconómico predominante en las manzanas del sector.")

    if not manzanas_zona.empty:
        col_mapa_soc, col_data_soc = st.columns([2, 1])
        with col_mapa_soc:
            manzanas_zona['estrato'] = manzanas_zona['estrato'].astype(int)
            fig_s = px.choropleth_map(
                manzanas_zona, geojson=manzanas_zona.geometry, locations=manzanas_zona.index,
                color="estrato", map_style="carto-positron", zoom=14.5,
                center={"lat": st.session_state.punto_lat, "lon": st.session_state.punto_lon},
                opacity=0.6,
                color_discrete_map={1:'#C0392B', 2:'#E67E22', 3:'#F1C40F', 4:'#2ECC71', 5:'#3498DB', 6:'#8E44AD'}
            )
            fig_s.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=350, showlegend=False)
            fig_s.add_trace(go.Scattermap(lat=list(area_interes.exterior.xy[1]), lon=list(area_interes.exterior.xy[0]), mode='lines', line=dict(color='black', width=2), name='Límite'))
            st.plotly_chart(fig_s, use_container_width=True)
        with col_data_soc:
            st.info(f"Moda: **Estrato {manzanas_zona['estrato'].mode()[0]}**")
            conteo_est = manzanas_zona['estrato'].value_counts().sort_index()
            fig_b = go.Figure(data=[go.Bar(x=[f"E{i}" for i in conteo_est.index], y=conteo_est.values, marker_color='#95A5A6')])
            fig_b.update_layout(height=200, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_b, use_container_width=True)
    else:
        st.warning("Sin datos residenciales.")

    

    
    # SECCIÓN 4: POT 
    
    st.markdown("---")
    st.markdown("### 🏗️ 4. ¿Qué se permite construir? (POT)")
    st.markdown("Vocación normativa proyectada sobre cada manzana del sector.")

    # 1. Copia de seguridad
    manzanas_final = manzanas_zona.copy()
    clasificacion_exitosa = False

    # Solo para ver si hay datos cargados
    # st.write(f"Cantidad de áreas POT cargadas: {len(areas_pot)}")
    # st.write(f"CRS Manzanas: {manzanas_final.crs}")
    # st.write(f"CRS Áreas POT: {areas_pot.crs}")

    if not manzanas_final.empty and not areas_pot.empty:
        try:
            # Asegurar CRS idéntico
            if areas_pot.crs != manzanas_final.crs:
                areas_pot = areas_pot.to_crs(manzanas_final.crs)

            # Reparar geometrías inválidas 
            areas_pot['geometry'] = areas_pot.geometry.buffer(0)
            manzanas_final['geometry'] = manzanas_final.geometry.buffer(0)

            # CRUCE ESPACIAL
            
            # Esto atrapa la manzana si aunque sea un pedacito toca el área del POT.
            cruce = gpd.sjoin(
                manzanas_final,  # Usamos el polígono completo, no el centroide
                areas_pot[['uso_pot_simplificado', 'geometry']], 
                how='left', 
                predicate='intersects' 
            )
            
            # Limpieza de duplicados
            
            # (Simplificación: nos quedamos con la primera que encuentre para no complicar el código)
            cruce = cruce[~cruce.index.duplicated(keep='first')]
            
            # Asignar
            manzanas_final['uso_pot_simplificado'] = cruce['uso_pot_simplificado']
            
            # Rellenar nulos
            manzanas_final['uso_pot_simplificado'] = manzanas_final['uso_pot_simplificado'].fillna('Sin Clasificación')
            
            # Validar si logramos clasificar algo
            if len(manzanas_final[manzanas_final['uso_pot_simplificado'] != 'Sin Clasificación']) > 0:
                clasificacion_exitosa = True
            
        except Exception as e:
            st.error(f"Error técnico en el cruce: {str(e)}")
            manzanas_final['uso_pot_simplificado'] = 'Sin Clasificación'
    else:
        st.warning("No hay datos de POT cargados o manzanas seleccionadas.")
        manzanas_final['uso_pot_simplificado'] = 'Sin Clasificación'

      
    # VISUALIZACIÓN
    
    col_mapa_pot, col_data_pot = st.columns([2, 1])
    
    with col_mapa_pot:
        # Definir colores
        cats = manzanas_final["uso_pot_simplificado"].unique().tolist()
        palette = px.colors.qualitative.Bold # Usamos colores fuertes
        
        
        color_map = {}
        for i, cat in enumerate(cats):
            if cat == "Sin Clasificación":
                color_map[cat] = "#95A5A6" # Gris
            else:
                color_map[cat] = palette[i % len(palette)]
        
        fig_p = px.choropleth_map(
            manzanas_final, 
            geojson=manzanas_final.geometry, 
            locations=manzanas_final.index,
            color="uso_pot_simplificado", 
            color_discrete_map=color_map,
            map_style="carto-positron", 
            zoom=14.5,
            center={"lat": st.session_state.punto_lat, "lon": st.session_state.punto_lon},
            opacity=0.6,
            title="Vocación del Suelo"
        )
        fig_p.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=350, showlegend=True)
        
        # Línea de límite
        if 'area_interes' in locals():
             fig_p.add_trace(go.Scattermap(
                lat=list(area_interes.exterior.xy[1]), 
                lon=list(area_interes.exterior.xy[0]), 
                mode='lines', 
                line=dict(color='black', width=2), 
                name='Zona'
            ))
        st.plotly_chart(fig_p, use_container_width=True)

    with col_data_pot:
        conteo = manzanas_final['uso_pot_simplificado'].value_counts()
        
        # Verificar si hay datos reales
        hay_datos = not (len(conteo) == 1 and 'Sin Clasificación' in conteo)
        
        if clasificacion_exitosa and hay_datos:
            moda = conteo.index[0]
            st.info(f"Uso predominante: **{moda}**")
            
            # Usar los mismos colores del mapa
            colores_barras = [color_map.get(x, '#333') for x in conteo.index]
            
            fig_bp = go.Figure(data=[go.Bar(
                y=[str(x)[:25] for x in conteo.index], 
                x=conteo.values, 
                orientation='h',
                marker_color=colores_barras
            )])
            fig_bp.update_layout(height=250, margin=dict(l=0,r=0,t=0,b=0), yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig_bp, use_container_width=True)
        else:
            st.warning("⚠️ No se cruzó información.")
            st.markdown("""
            **Posibles causas:**
            1. El dataset de 'Áreas' está vacío o no cubre esta zona.
            2. Las coordenadas están desplazadas (revisa el CRS).
            """)
            # Botón de depuración
            if st.checkbox("Ver datos crudos del POT"):
                st.write(areas_pot.head())

    

    
    # SEGURIDAD 
    
    st.markdown("---")
    st.markdown("### 🛡️ Contexto de Seguridad")
    
    localidad_actual = st.session_state.localidad_sel
    datos_loc = localidades[localidades['nombre_localidad'] == localidad_actual].iloc[0]
    seguridad_raw = datos_loc.get('top_3_delitos', 'Dato no disponible')
    
    # Formato Lista para Seguridad
    if "," in seguridad_raw:
        items = seguridad_raw.split(",")
        lista_html = "".join([f"<li>{i.strip()}</li>" for i in items])
        texto_seg = f"<ul>{lista_html}</ul>"
    else:
        texto_seg = seguridad_raw

    st.markdown(f"""
    <div style="background-color: #FDEDEC; padding: 15px; border-left: 5px solid #C0392B; border-radius: 5px;">
        <h4 style="color: #922B21; margin:0;">🚨 En {localidad_actual} ten cuidado con:</h4>
        {texto_seg}
    </div>
    """, unsafe_allow_html=True)

# PASO 5: REPORTE EJECUTIVO

if st.session_state.step == 5: 
    import base64
    import urllib.parse # Asegúrate de tener esto importado

    st.markdown("---")
    st.header("📑 Informe Ejecutivo")

    # ---------------------------------------------------------
    # 1. PREPARACIÓN DE DATOS (URL DEL GEMELO DIGITAL)
    # ---------------------------------------------------------
    # Definimos la URL AQUÍ para usarla tanto en el reporte como en el botón de abajo
    URL_BASE_CESIUM = "https://sfuentesgo.github.io/DATOS_ECOSISTEMA_2025/" 
    
    params_payload = {
        "lat": st.session_state.punto_lat,
        "lon": st.session_state.punto_lon,
        "radio": st.session_state.radio_analisis,
        "loc": st.session_state.localidad_sel,
        "altura": "1000" 
    }
    
    query_string = urllib.parse.urlencode(params_payload)
    url_final = f"{URL_BASE_CESIUM}?{query_string}"

    # ---------------------------------------------------------
    # 2. PROCESAMIENTO DE MAPAS E INDICADORES (Tu código original)
    # ---------------------------------------------------------
    # Recuperar Dataframe de Manzanas...
    if 'manzanas_final' in locals() and not manzanas_final.empty:
        df_reporte = manzanas_final.copy()
    else:
        df_reporte = manzanas_zona.copy()
        # ... (Lógica de cruce POT si es necesario) ...
        if not areas_pot.empty and 'uso_pot_simplificado' not in df_reporte.columns:
            try:
                if areas_pot.crs != df_reporte.crs:
                    areas_pot = areas_pot.to_crs(df_reporte.crs)
                cruce = gpd.sjoin(df_reporte, areas_pot[['uso_pot_simplificado', 'geometry']], how='left', predicate='intersects')
                cruce = cruce[~cruce.index.duplicated(keep='first')]
                df_reporte['uso_pot_simplificado'] = cruce['uso_pot_simplificado']
            except: pass 

    # Calcular KPIs
    num_tm = len(transporte_zona)
    num_col = len(colegios_zona)
    num_salud = len(salud_zona)
    
    # Modas
    # Modas
    if 'uso_pot_simplificado' not in df_reporte.columns: 
        df_reporte['uso_pot_simplificado'] = "Sin Clasificación"
        
    modas_uso = df_reporte['uso_pot_simplificado'].fillna("Sin Clasificación").mode()
    uso_moda = modas_uso[0] if not modas_uso.empty else "Sin Clasificación"
    
    try:
        if 'estrato' in df_reporte.columns: 
            modas_estrato = df_reporte['estrato'].mode()
            estrato_moda = int(modas_estrato[0]) if not modas_estrato.empty else "N/A"
        else: 
            estrato_moda = "N/A"
    except: 
        estrato_moda = "N/A"

    # Seguridad
    localidad = st.session_state.localidad_sel
    datos_loc = localidades[localidades['nombre_localidad'] == localidad].iloc[0]
    seguridad_texto = datos_loc.get('top_3_delitos', 'No disponible')
    
    if "," in seguridad_texto:
        items_seg = seguridad_texto.split(",")
        lista_seguridad_html = "<ul style='margin-top:5px; margin-bottom:5px; padding-left: 20px;'>"
        for item in items_seg:
            lista_seguridad_html += f"<li>{item.strip()}</li>"
        lista_seguridad_html += "</ul>"
    else:
        lista_seguridad_html = f"<p>{seguridad_texto}</p>"

    # Variables Contexto
    radio = st.session_state.radio_analisis
    lat, lon = st.session_state.punto_lat, st.session_state.punto_lon

    # SCORING
    score = 0
    if num_tm >= 2: score += 1
    if num_col >= 1: score += 1
    if uso_moda != "Sin Clasificación": score += 1
    if num_salud >= 1: score += 1
    
    if score >= 3:
        dictamen = "VIABILIDAD ALTA ⭐⭐⭐"
        color_fondo = "#27AE60"
    elif score >= 2:
        dictamen = "VIABILIDAD MEDIA ⭐⭐"
        color_fondo = "#F39C12"
    else:
        dictamen = "VIABILIDAD RESTRINGIDA ⭐"
        color_fondo = "#C0392B"

    # IMAGEN ESTÁTICA MAPA
    with st.spinner("Generando mapa detallado..."):
        try:
            fig_mapa = go.Figure()
            # Zona
            if 'area_interes' in locals():
                lats_poly = list(area_interes.exterior.xy[1])
                lons_poly = list(area_interes.exterior.xy[0])
                fig_mapa.add_trace(go.Scattermap(lat=lats_poly, lon=lons_poly, mode='lines', fill='toself', fillcolor='rgba(52, 152, 219, 0.1)', line=dict(color='#3498DB', width=2)))
            # Puntos
            if not transporte_zona.empty: fig_mapa.add_trace(go.Scattermap(lat=transporte_zona.geometry.y, lon=transporte_zona.geometry.x, mode='markers', marker=dict(size=6, color='#E74C3C')))
            if not colegios_zona.empty: fig_mapa.add_trace(go.Scattermap(lat=colegios_zona.geometry.y, lon=colegios_zona.geometry.x, mode='markers', marker=dict(size=6, color="#9625C7")))
            if not salud_zona.empty: fig_mapa.add_trace(go.Scattermap(lat=salud_zona.geometry.y, lon=salud_zona.geometry.x, mode='markers', marker=dict(size=6, color="#3A07F3")))
            # Usuario
            fig_mapa.add_trace(go.Scattermap(lat=[lat], lon=[lon], mode='markers', marker=dict(size=12, color='black')))
            
            fig_mapa.update_layout(map_style="carto-positron", map_zoom=14.5, map_center={"lat": lat, "lon": lon}, margin={"r":0,"t":0,"l":0,"b":0}, showlegend=False)
            
            img_bytes = fig_mapa.to_image(format="png", width=600, height=350, scale=2)
            b64_mapa = base64.b64encode(img_bytes).decode('utf-8')
            html_mapa = f'<img src="data:image/png;base64,{b64_mapa}" style="width:100%; border-radius:8px; border:1px solid #ccc;">'
        except:
            html_mapa = "<div style='padding:20px; background:#f0f0f0;'>Mapa no disponible</div>"
    
    # Fecha
    from datetime import datetime
    import pytz
    fecha_reporte = datetime.now(pytz.timezone('America/Bogota')).strftime("%d/%m/%Y %I:%M %p") 

    # ---------------------------------------------------------
    # 3. CONSTRUCCIÓN DEL HTML (CON EL LINK INYECTADO)
    # ---------------------------------------------------------
    html_report = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: 'Helvetica', sans-serif; max-width: 800px; margin: 0 auto; color: #333; }}
            .header {{ text-align: center; padding: 25px; background: #2C3E50; color: white; border-radius: 0 0 10px 10px; }}
            .card {{ border: 1px solid #ddd; padding: 20px; border-radius: 8px; margin-top: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }}
            .kpi-table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
            .kpi-table th {{ background-color: #F4F6F7; padding: 8px; text-align: left; border: 1px solid #ddd; font-size: 11px; color: #555; }}
            .kpi-table td {{ padding: 10px; text-align: center; border: 1px solid #ddd; font-size: 16px; font-weight: bold; color: #2C3E50; }}
            .dot {{ height: 10px; width: 10px; border-radius: 50%; display: inline-block; margin-right: 5px; }}
            .dictamen-box {{ margin-top: 20px; padding: 20px; background: {color_fondo}; color: white; text-align: center; border-radius: 8px; }}
            
            /* ESTILO PARA EL BOTÓN DENTRO DEL REPORTE */
            .btn-twin {{
                display: inline-block;
                background-color: #2980B9;
                color: white;
                padding: 10px 20px;
                text-decoration: none;
                border-radius: 5px;
                font-weight: bold;
                margin-top: 15px;
                font-size: 14px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1 style="margin:0;">Ficha de Inteligencia Territorial</h1>
            <p style="margin:5px 0 0;">Bogotá D.C. | Localidad {localidad}</p>
        </div>

        <div class="card">
            <h3 style="margin-top:0; border-bottom: 1px solid #eee; padding-bottom: 10px;">📍 Ubicación y Entorno</h3>
            <p style="font-size: 14px; color: #555;">Coordenadas: {lat:.4f}, {lon:.4f} | Radio: {radio}m</p>
            {html_mapa}
            
            <div style="text-align: center;">
                <a href="{url_final}" target="_blank" class="btn-twin">
                    🚀 Ver en Gemelo Digital 3D
                </a>
            </div>

            <table class="kpi-table">
                <tr>
                    <th><span class="dot" style="background-color: #E74C3C;"></span>TRANSMILENIO</th>
                    <th><span class="dot" style="background-color: #9625C7;"></span>COLEGIOS</th>
                    <th><span class="dot" style="background-color: #3A07F3;"></span>SALUD</th>
                    <th>MODA ESTRATO</th>
                    <th>MODA USO POT</th>
                </tr>
                <tr>
                    <td>{num_tm}</td>
                    <td>{num_col}</td>
                    <td>{num_salud}</td>
                    <td>{estrato_moda}</td>
                    <td style="font-size:12px;">{uso_moda}</td>
                </tr>
            </table>
        </div>

        <div class="card">
            <h3 style="margin-top:0; border-bottom: 1px solid #eee; padding-bottom: 10px;">🛡️ Seguridad (Top 3 Delitos)</h3>
            <div style="background: #FDEDEC; padding: 15px; border-left: 5px solid #C0392B; color: #922B21;">
                {lista_seguridad_html}
            </div>
        </div>

        <div class="dictamen-box">
            <p style="margin:0; font-size:14px; opacity:0.9;">DICTAMEN TÉCNICO</p>
            <h2 style="margin:5px 0 0; font-size:24px;">{dictamen}</h2>
        </div>
        
        <div style="text-align: center; margin-top: 30px; color: #999; font-size: 11px;">
            Generado con Bogotá Visible | {fecha_reporte}
        </div>
    </body>
    </html>
    """

    # ---------------------------------------------------------
    # 4. BOTONES DE ACCIÓN (Interfaz Streamlit)
    # ---------------------------------------------------------
    st.markdown("---")

    # CSS Maestro (Como lo teníamos)
    st.markdown("""
    <style>
    [data-testid="stDownloadButton"] button, [data-testid="stButton"] button, [data-testid="stLinkButton"] a {
        height: 50px !important; width: 100% !important; border-radius: 8px !important; font-weight: 800 !important; border: none !important;
        display: flex !important; align-items: center !important; justify-content: center !important; transition: all 0.3s ease !important;
        color: white !important; margin: 0 !important; text-decoration: none !important; padding: 0 !important;
    }
    [data-testid="stDownloadButton"] button { background-color: #27AE60 !important; }
    [data-testid="stButton"] button { background-color: #7F8C8D !important; }
    [data-testid="stLinkButton"] a { background-color: #2980B9 !important; box-shadow: 0 2px 5px rgba(0,0,0,0.2); }
    [data-testid="stDownloadButton"] button:hover, [data-testid="stButton"] button:hover, [data-testid="stLinkButton"] a:hover {
        transform: translateY(-3px); box-shadow: 0 5px 10px rgba(0,0,0,0.3) !important; color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1.5], gap="small") 

    with col1:
        st.download_button(label="📥 Descargar Ficha", data=html_report, file_name=f"Ficha_{localidad}.html", mime="text/html")

    with col2:
        if st.button("🔄 Reiniciar", use_container_width=True):
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.session_state.step = 1 
            st.rerun()

    with col3:
        # AQUI REUTILIZAMOS LA URL QUE CALCULAMOS ARRIBA
        st.link_button(label="🚀 VER GEMELO DIGITAL", url=url_final, use_container_width=True)

