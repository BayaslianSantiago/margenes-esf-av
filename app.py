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
        # Leemos con punto y coma y decimal con coma (formato argentino)
        df = pd.read_csv('resultado_analisis.csv', sep=';', decimal=',')
        return df
    except FileNotFoundError:
        return None

df = cargar_datos()

if df is None:
    st.error("❌ Falta el archivo 'resultado_analisis.csv'.")
    st.stop()

# --- BARRA LATERAL (FILTROS) ---
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
st.markdown("Vista rápida de rentabilidad y precios.")

# --- KPIs INTELIGENTES (Simples de leer) ---
# Calculamos los números
total_prod = len(df_filtrado)
margen_mediana = df_filtrado['Margen_%'].median()
criticos = len(df_filtrado[df_filtrado['Margen_%'] < 15])
roi = (df_filtrado['Ganancia_$'].sum() / df_filtrado['Costo'].sum()) * 100 if df_filtrado['Costo'].sum() > 0 else 0

# Los mostramos en una fila limpia
k1, k2, k3, k4 = st.columns(4)

k1.metric("Total Productos", total_prod)
k2.metric("Margen Típico", f"{margen_mediana:.1f}%", help="La mayoría de tus productos ronda este margen.")
k3.metric("⚠️ Revisar Precio", criticos, delta_color="inverse", help="Productos con margen menor al 15%.")
k4.metric("Retorno Inversión", f"{roi:.1f}%")

st.markdown("---")

# --- GRÁFICOS (Lo esencial) ---
col_izq, col_der = st.columns(2)

with col_izq:
    st.subheader("🏆 Top 10 Mejores Márgenes")
    # Gráfico de barras simple y efectivo
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
    st.subheader("💰 Costo vs. Precio")
    # Gráfico de dispersión para detectar anomalías visualmente
    fig_scatter = px.scatter(
        df_filtrado,
        x='Costo',
        y='Precio',
        size='Margen_%',
        color='Margen_%',
        hover_name='Desc',
        title="Relación de Precios (Color = Margen)",
        color_continuous_scale='Viridis'
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

# --- TABLA FINAL ---
st.markdown("---")
st.subheader("📋 Listado Detallado")

# Tabla simple con gradiente de color para identificar rápido lo bueno y lo malo
st.dataframe(
    df_filtrado.style.format({
        "Precio": "${:,.0f}",
        "Costo": "${:,.0f}",
        "Ganancia_$": "${:,.0f}",
        "Margen_%": "{:.1f}%"
    }).background_gradient(subset=['Margen_%'], cmap='RdYlGn', vmin=0, vmax=50),
    use_container_width=True
)
