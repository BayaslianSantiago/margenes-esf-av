import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIGURACIÓN VISUAL ---
st.set_page_config(
    page_title="Dashboard Ganancia",
    page_icon="📊",
    layout="wide"
)

# --- CARGA DE DATOS ---
@st.cache_data
def cargar_datos():
    try:
        # Lectura con formato argentino (punto y coma / coma decimal)
        df = pd.read_csv('resultado_analisis.csv', sep=';', decimal=',')
        return df
    except FileNotFoundError:
        return None

df = cargar_datos()

if df is None:
    st.error("❌ No se encuentra el archivo 'resultado_analisis.csv' en el repositorio.")
    st.stop()

# --- SIDEBAR (FILTROS) ---
st.sidebar.header("🔍 Filtros")

# 1. Buscador
busqueda = st.sidebar.text_input("Buscar producto:", placeholder="Ej: Queso")

# 2. Slider de Margen
margen_min = float(df['Margen_%'].min())
margen_max = float(df['Margen_%'].max())

rango_margen = st.sidebar.slider(
    "Filtrar por Margen %", 
    0.0, margen_max, (0.0, margen_max)
)

# --- APLICAR FILTROS ---
df_filtrado = df[
    (df['Margen_%'] >= rango_margen[0]) & 
    (df['Margen_%'] <= rango_margen[1])
]

if busqueda:
    df_filtrado = df_filtrado[df_filtrado['Desc'].str.contains(busqueda, case=False, na=False)]

# --- LÓGICA DE SEGMENTACIÓN (El semáforo) ---
UMBRAL_BAJO = 15
UMBRAL_ALTO = 40

prods_bajos = df_filtrado[df_filtrado['Margen_%'] < UMBRAL_BAJO]
prods_medios = df_filtrado[(df_filtrado['Margen_%'] >= UMBRAL_BAJO) & (df_filtrado['Margen_%'] <= UMBRAL_ALTO)]
prods_altos = df_filtrado[df_filtrado['Margen_%'] > UMBRAL_ALTO]

# --- PÁGINA PRINCIPAL ---
st.title("📊 Estado de Rentabilidad")
st.markdown("Monitoreo de márgenes y segmentación de productos.")

# --- KPIs ---
k1, k2, k3, k4 = st.columns(4)

k1.metric(
    "Total Productos", 
    len(df_filtrado),
    help="Productos visibles con los filtros actuales"
)

k2.metric(
    "💎 Margen Alto", 
    len(prods_altos),
    delta=f">{UMBRAL_ALTO}%",
    help="Productos muy rentables"
)

k3.metric(
    "⚖️ Margen Medio", 
    len(prods_medios),
    delta=f"{UMBRAL_BAJO}-{UMBRAL_ALTO}%",
    delta_color="off",
    help="Productos estándar"
)

k4.metric(
    "⚠️ Margen Bajo", 
    len(prods_bajos),
    delta=f"<{UMBRAL_BAJO}%",
    delta_color="inverse", # Rojo si aumenta
    help="Productos con poca ganancia (Revisar precios)"
)

st.markdown("---")

# --- GRÁFICOS ---
col_izq, col_der = st.columns(2)

with col_izq:
    st.subheader("🏆 Top 10 Mejores Márgenes")
    # Gráfico de barras simple
    top_10 = df_filtrado.nlargest(10, 'Margen_%')
    
    fig_bar = px.bar(
        top_10, 
        x='Margen_%', 
        y='Desc', 
        orientation='h', 
        text='Margen_%',
        color='Margen_%',
        color_continuous_scale='Greens'
    )
    fig_bar.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False)
    st.plotly_chart(fig_bar, use_container_width=True)

with col_der:
    st.subheader("💰 Mapa de Rentabilidad (Costo vs Precio)")
    
    # Creamos columna temporal para colorear el gráfico
    def categorizar(m):
        if m > UMBRAL_ALTO: return "Alto (>40%)"
        elif m < UMBRAL_BAJO: return "Bajo (<15%)"
        else: return "Medio"
    
    df_filtrado['Categoría'] = df_filtrado['Margen_%'].apply(categorizar)
    
    # Gráfico de dispersión con colores fijos (Semáforo)
    fig_scatter = px.scatter(
        df_filtrado,
        x='Costo',
        y='Precio',
        size='Margen_%', # Tamaño de burbuja = Margen
        color='Categoría',
        # Asignamos colores específicos: Alto=Verde, Medio=Amarillo, Bajo=Rojo
        color_discrete_map={
            "Alto (>40%)": "green", 
            "Medio": "#ffcc00", # Amarillo oro
            "Bajo (<15%)": "red"
        },
        hover_name='Desc',
        title="Distribución de Precios (Color = Rentabilidad)"
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

# --- TABLA DETALLADA ---
st.markdown("---")
st.subheader("📋 Listado de Productos")

st.dataframe(
    df_filtrado[['Desc', 'Costo', 'Precio', 'Ganancia_$', 'Margen_%']].style.format({
        "Precio": "${:,.0f}",
        "Costo": "${:,.0f}",
        "Ganancia_$": "${:,.0f}",
        "Margen_%": "{:.1f}%"
    }).background_gradient(subset=['Margen_%'], cmap='RdYlGn', vmin=0, vmax=50),
    use_container_width=True
)
