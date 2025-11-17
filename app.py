import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Dashboard Rentabilidad",
    page_icon="📈",
    layout="wide"
)

# --- FUNCIÓN DE CARGA DE DATOS ---
@st.cache_data
def cargar_datos():
    # Al estar en el mismo repo, solo ponemos el nombre del archivo.
    # Mantenemos el formato que generamos: punto y coma y coma decimal.
    try:
        df = pd.read_csv('resultado_analisis.csv', sep=';', decimal=',')
        return df
    except FileNotFoundError:
        return None

# Cargamos los datos
df = cargar_datos()

# --- CONTROL DE ERRORES ---
if df is None:
    st.error("""
    ❌ **No se encuentra el archivo 'resultado_analisis.csv'.**
    
    Asegúrate de que:
    1. El archivo 'resultado_analisis.csv' esté subido al repositorio.
    2. Esté en la misma carpeta que este archivo 'app.py'.
    3. El nombre esté escrito exactamente igual.
    """)
    st.stop()

# --- SIDEBAR (BARRA LATERAL DE FILTROS) ---
st.sidebar.header("🔍 Filtros de Análisis")

st.sidebar.write("Usa estos filtros para encontrar oportunidades.")

# 1. Filtro de Búsqueda de Texto
busqueda = st.sidebar.text_input("Buscar producto por nombre:", placeholder="Ej: Salamin")

# 2. Filtro por Margen
min_val = float(df['Margen_%'].min())
max_val = float(df['Margen_%'].max())

rango_margen = st.sidebar.slider(
    "Filtrar por % de Margen:",
    min_value=min_val,
    max_value=max_val,
    value=(min_val, max_val)
)

# --- APLICACIÓN DE FILTROS ---
df_filtrado = df[
    (df['Margen_%'] >= rango_margen[0]) & 
    (df['Margen_%'] <= rango_margen[1])
]

if busqueda:
    df_filtrado = df_filtrado[df_filtrado['Desc'].str.contains(busqueda, case=False, na=False)]

# --- PÁGINA PRINCIPAL ---
st.title("📊 Monitor de Rentabilidad")
st.markdown("Análisis interactivo de costos, precios y márgenes de ganancia.")

# --- KPIs (MÉTRICAS CLAVE) ---
# Usamos columnas para mostrar los números grandes
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

kpi1.metric("Productos Analizados", len(df_filtrado))
kpi2.metric("Margen Promedio", f"{df_filtrado['Margen_%'].mean():.2f}%")
kpi3.metric("Precio Venta Promedio", f"${df_filtrado['Precio'].mean():,.0f}")
kpi4.metric("Ganancia Promedio x Unidad", f"${df_filtrado['Ganancia_$'].mean():,.0f}")

st.markdown("---")

# --- GRÁFICOS ---
col_graf1, col_graf2 = st.columns(2)

with col_graf1:
    st.subheader("🏆 Top 10: Mayor Rentabilidad")
    # Ordenamos y tomamos los 10 mejores
    top_10_margen = df_filtrado.nlargest(10, 'Margen_%')
    
    fig_bar = px.bar(
        top_10_margen, 
        x='Margen_%', 
        y='Desc',
        orientation='h',
        text='Margen_%',
        title="Productos con mayor porcentaje de ganancia",
        color='Margen_%',
        color_continuous_scale='Greens'
    )
    fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_bar, use_container_width=True)

with col_graf2:
    st.subheader("📉 Estrategia de Precios (Costo vs Precio)")
    # Scatter plot: permite ver outliers
    fig_scatter = px.scatter(
        df_filtrado,
        x='Costo',
        y='Precio',
        size='Margen_%', # El tamaño de la burbuja es el margen
        color='Ganancia_$', # El color es la ganancia en plata
        hover_name='Desc',
        title="Relación Costo-Precio (Burbuja = % Margen)",
        color_continuous_scale='Bluered'
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

# --- TABLA DE DATOS ---
st.markdown("---")
st.subheader("📋 Detalle de Productos")

# Mostramos la tabla con formato condicional (verde oscuro = más margen)
st.dataframe(
    df_filtrado.style.format({
        "Precio": "${:,.2f}",
        "Costo": "${:,.2f}",
        "Ganancia_$": "${:,.2f}",
        "Margen_%": "{:.2f}%"
    }).background_gradient(subset=['Margen_%'], cmap='Greens'),
    use_container_width=True
)

# Botón para descargar lo que estás viendo
csv_export = df_filtrado.to_csv(index=False, sep=';', decimal=',')
st.download_button(
    label="📥 Descargar estos datos filtrados",
    data=csv_export,
    file_name='analisis_exportado.csv',
    mime='text/csv',
)
