import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard Fiambrería", page_icon="🧀", layout="wide")

# --- CARGA ---
@st.cache_data
def cargar_datos():
    try:
        df = pd.read_csv('resultado_analisis.csv', sep=';', decimal=',')
        return df
    except FileNotFoundError:
        return None

df = cargar_datos()
if df is None: st.stop()

# --- FEATURE ENGINEERING: CREAR COLUMNA 'RUBRO' ---
# Tomamos la descripción, la separamos por espacios y nos quedamos con la primera palabra
df['Rubro'] = df['Desc'].astype(str).str.split().str[0]

# Opcional: Limpieza rápida si hay rubros con 1 o 2 letras (ej: "DE", "EL") que sean basura
df = df[df['Rubro'].str.len() > 2]

# --- SIDEBAR ---
st.sidebar.header("🔍 Filtros")
# Agregamos filtro por Rubro
lista_rubros = ['Todos'] + sorted(df['Rubro'].unique().tolist())
rubro_seleccionado = st.sidebar.selectbox("Filtrar por Rubro:", lista_rubros)

rango_margen = st.sidebar.slider("Filtro Margen %", 0.0, float(df['Margen_%'].max()), (0.0, float(df['Margen_%'].max())))

# Aplicar Filtros
df_filtrado = df[(df['Margen_%'] >= rango_margen[0]) & (df['Margen_%'] <= rango_margen[1])]

if rubro_seleccionado != 'Todos':
    df_filtrado = df_filtrado[df_filtrado['Rubro'] == rubro_seleccionado]

# --- SEGMENTACIÓN ---
umbral_bajo = 15
umbral_alto = 40
prods_bajos = df_filtrado[df_filtrado['Margen_%'] < umbral_bajo]
prods_medios = df_filtrado[(df_filtrado['Margen_%'] >= umbral_bajo) & (df_filtrado['Margen_%'] <= umbral_alto)]
prods_altos = df_filtrado[df_filtrado['Margen_%'] > umbral_alto]

# --- TÍTULO Y KPIs ---
st.title("📊 Análisis por Categorías")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Productos", len(df_filtrado))
col2.metric("💎 Margen Alto", len(prods_altos), delta=f">{umbral_alto}%")
col3.metric("⚖️ Margen Medio", len(prods_medios), delta_color="off")
col4.metric("⚠️ Margen Bajo", len(prods_bajos), delta=f"<{umbral_bajo}%", delta_color="inverse")

st.markdown("---")

# --- ANÁLISIS POR RUBRO (LO NUEVO) ---
st.subheader("🏷️ Rentabilidad por Familia de Productos")

# Agrupamos datos para ver el promedio por Rubro
# (Solo mostramos rubros con más de 2 productos para evitar ruido)
rubro_stats = df_filtrado.groupby('Rubro').agg({
    'Margen_%': 'median',
    'Desc': 'count',
    'Ganancia_$': 'mean'
}).reset_index()

rubro_stats = rubro_stats[rubro_stats['Desc'] > 2].sort_values(by='Margen_%', ascending=False)

# Gráfico 1: ¿Qué Rubro deja más margen?
fig_rubro = px.bar(
    rubro_stats.head(15), # Top 15 rubros
    x='Rubro',
    y='Margen_%',
    color='Margen_%',
    title="Top Rubros más Rentables (Mediana de Margen)",
    text='Margen_%',
    color_continuous_scale='Teal'
)
fig_rubro.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
st.plotly_chart(fig_rubro, use_container_width=True)

# --- GRÁFICO DETALLADO ---
col_izq, col_der = st.columns(2)

with col_izq:
    st.subheader("📦 Dispersión por Rubro")
    # Boxplot: Muestra si un rubro tiene precios muy variables
    # Filtramos para mostrar solo los top 10 rubros más comunes para que se lea bien
    top_rubros_nombres = df_filtrado['Rubro'].value_counts().head(10).index
    df_top_rubros = df_filtrado[df_filtrado['Rubro'].isin(top_rubros_nombres)]
    
    fig_box = px.box(
        df_top_rubros, 
        x='Rubro', 
        y='Margen_%', 
        color='Rubro',
        title="Variabilidad de Margen en los Rubros Principales"
    )
    st.plotly_chart(fig_box, use_container_width=True)

with col_der:
    st.subheader("💰 Mapa de Rentabilidad")
    def categorizar(m):
        if m > umbral_alto: return "Alto"
        elif m < umbral_bajo: return "Bajo"
        else: return "Medio"
    df_filtrado['Categoría'] = df_filtrado['Margen_%'].apply(categorizar)
    
    fig_scatter = px.scatter(
        df_filtrado,
        x='Costo',
        y='Precio',
        color='Categoría',
        color_discrete_map={"Alto": "green", "Medio": "gold", "Bajo": "red"},
        hover_name='Desc',
        title="Costo vs Precio"
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

# --- TABLA FINAL ---
st.markdown("---")
st.dataframe(
    df_filtrado[['Rubro', 'Desc', 'Costo', 'Precio', 'Margen_%', 'Ganancia_$']].style.format({
        "Precio": "${:,.0f}",
        "Costo": "${:,.0f}",
        "Ganancia_$": "${:,.0f}",
        "Margen_%": "{:.1f}%"
    }).background_gradient(subset=['Margen_%'], cmap='RdYlGn', vmin=0, vmax=50),
    use_container_width=True
)
