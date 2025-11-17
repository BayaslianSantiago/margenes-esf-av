import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIGURACIÓN VISUAL ---
st.set_page_config(
    page_title="Dashboard Fiambrería",
    page_icon="🧀",
    layout="wide"
)

# --- CARGA DE DATOS ---
@st.cache_data
def cargar_datos():
    try:
        df = pd.read_csv('resultado_analisis.csv', sep=';', decimal=',')
        return df
    except FileNotFoundError:
        return None

df = cargar_datos()

if df is None:
    st.error("❌ Falta el archivo 'resultado_analisis.csv'.")
    st.stop()

# --- SIDEBAR (FILTROS) ---
st.sidebar.header("🔍 Filtros")
busqueda = st.sidebar.text_input("Buscar producto:", placeholder="Ej: Queso")
rango_margen = st.sidebar.slider(
    "Filtrar por Margen %", 
    0.0, float(df['Margen_%'].max()), (0.0, float(df['Margen_%'].max()))
)

# Aplicar filtros
df_filtrado = df[
    (df['Margen_%'] >= rango_margen[0]) & 
    (df['Margen_%'] <= rango_margen[1])
]

if busqueda:
    df_filtrado = df_filtrado[df_filtrado['Desc'].str.contains(busqueda, case=False, na=False)]

# --- PÁGINA PRINCIPAL ---
st.title("📊 Estado del Negocio")
st.markdown("Segmentación de productos según su rentabilidad.")

# --- LÓGICA DE SEGMENTACIÓN (Aquí defines tus umbrales) ---
umbral_bajo = 15
umbral_alto = 40

# Creamos los 3 grupos
prods_bajos = df_filtrado[df_filtrado['Margen_%'] < umbral_bajo]
prods_medios = df_filtrado[(df_filtrado['Margen_%'] >= umbral_bajo) & (df_filtrado['Margen_%'] <= umbral_alto)]
prods_altos = df_filtrado[df_filtrado['Margen_%'] > umbral_alto]

# --- NUEVOS KPIs DE CATEGORÍAS ---
col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Total Productos", 
    len(df_filtrado),
    help="Cantidad total de productos visibles"
)

col2.metric(
    "💎 Margen Alto", 
    len(prods_altos),
    delta=f">{umbral_alto}%",
    help=f"Productos con ganancia superior al {umbral_alto}%"
)

col3.metric(
    "⚖️ Margen Medio", 
    len(prods_medios),
    delta=f"{umbral_bajo}-{umbral_alto}%",
    delta_color="off", # Color gris neutro
    help="Productos estándar del negocio"
)

col4.metric(
    "⚠️ Margen Bajo", 
    len(prods_bajos),
    delta=f"<{umbral_bajo}%",
    delta_color="inverse", # Rojo si aumenta
    help=f"Productos con ganancia inferior al {umbral_bajo}%"
)

st.markdown("---")

# --- GRÁFICOS ---
col_izq, col_der = st.columns(2)

with col_izq:
    st.subheader("🏆 Top 10 Mejores Productos")
    # Tomamos los mejores del segmento Alto (o del total si hay pocos)
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
    st.subheader("💰 Mapa de Rentabilidad")
    # Coloreamos el scatter plot según estas nuevas categorías
    # Creamos una columna temporal para el color del gráfico
    def categorizar(m):
        if m > umbral_alto: return "Alto"
        elif m < umbral_bajo: return "Bajo"
        else: return "Medio"
    
    df_filtrado['Categoría'] = df_filtrado['Margen_%'].apply(categorizar)
    
    fig_scatter = px.scatter(
        df_filtrado,
        x='Costo',
        y='Precio',
        size='Margen_%',
        color='Categoría', # Usamos la nueva categoría para los colores
        color_discrete_map={"Alto": "green", "Medio": "gold", "Bajo": "red"}, # Colores semáforo
        hover_name='Desc',
        title="Distribución de Costos y Precios"
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

# --- TABLA FINAL ---
st.markdown("---")
st.subheader("📋 Listado Detallado")

st.dataframe(
    df_filtrado.style.format({
        "Precio": "${:,.0f}",
        "Costo": "${:,.0f}",
        "Ganancia_$": "${:,.0f}",
        "Margen_%": "{:.1f}%"
    }).background_gradient(subset=['Margen_%'], cmap='RdYlGn', vmin=0, vmax=50),
    use_container_width=True
)
