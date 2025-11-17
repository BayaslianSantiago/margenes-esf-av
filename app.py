import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard Rentabilidad Pro", page_icon="🧀", layout="wide")

# --- CARGA (Igual que antes) ---
@st.cache_data
def cargar_datos():
    try:
        df = pd.read_csv('resultado_analisis.csv', sep=';', decimal=',')
        return df
    except FileNotFoundError:
        return None

df = cargar_datos()
if df is None:
    st.stop()

# --- SIDEBAR MEJORADO ---
st.sidebar.header("🔍 Configuración")

# Filtros
busqueda = st.sidebar.text_input("Buscar producto:", placeholder="Ej: Salamin")
rango_margen = st.sidebar.slider("Filtro Margen %:", 0.0, float(df['Margen_%'].max()), (0.0, float(df['Margen_%'].max())))

# --- NUEVO: SIMULADOR ---
st.sidebar.markdown("---")
st.sidebar.subheader("🔮 Simulador de Impacto")
st.sidebar.write("Si aumentaras el precio de estos productos...")
aumento_simulado = st.sidebar.slider("Aumento de Precio (%)", 0, 50, 0)

# Aplicar Filtros
df_filtrado = df[
    (df['Margen_%'] >= rango_margen[0]) & 
    (df['Margen_%'] <= rango_margen[1])
]
if busqueda:
    df_filtrado = df_filtrado[df_filtrado['Desc'].str.contains(busqueda, case=False, na=False)]

# --- LÓGICA DEL SIMULADOR ---
# Calculamos cuánta plata extra entraría si aplicamos ese % de aumento
dinero_extra = (df_filtrado['Precio'] * (aumento_simulado/100)).sum()

# --- PÁGINA PRINCIPAL ---
st.title("📊 Monitor de Rentabilidad e Inteligencia")

# KPIs
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Productos", len(df_filtrado))
kpi2.metric("Margen Mediana", f"{df_filtrado['Margen_%'].median():.2f}%")
kpi3.metric("Prod. Críticos (<15%)", len(df_filtrado[df_filtrado['Margen_%'] < 15]))

# El KPI 4 cambia dinámicamente con el simulador
kpi4.metric(
    label=f"Ganancia Extra (Si +{aumento_simulado}%)",
    value=f"${dinero_extra:,.0f}",
    delta="Proyección Mensual" if aumento_simulado > 0 else None,
    help="Dinero adicional facturado si vendieras 1 unidad de cada producto con el aumento simulado."
)

st.markdown("---")

# --- PESTAÑAS PARA ORGANIZAR ---
tab1, tab2, tab3 = st.tabs(["📈 Análisis Visual", "📦 Segmentación de Precios", "📋 Datos & Descargas"])

with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Distribución de Márgenes")
        # HISTOGRAMA: Muestra dónde se concentran tus productos
        fig_hist = px.histogram(
            df_filtrado, 
            x="Margen_%", 
            nbins=20, 
            title="¿Cómo se distribuyen mis ganancias?",
            color_discrete_sequence=['#2E8B57'] # Verde bosque
        )
        # Agregamos una línea vertical en la mediana
        fig_hist.add_vline(x=df_filtrado['Margen_%'].median(), line_dash="dash", line_color="red", annotation_text="Mediana")
        st.plotly_chart(fig_hist, use_container_width=True)
        st.caption("Si la curva está muy a la izquierda, tienes muchos productos poco rentables.")

    with col2:
        st.subheader("Top 10 Rentabilidad")
        top_10 = df_filtrado.nlargest(10, 'Margen_%')
        fig_bar = px.bar(top_10, x='Margen_%', y='Desc', orientation='h', color='Margen_%', color_continuous_scale='Greens')
        fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_bar, use_container_width=True)

with tab2:
    st.subheader("Rentabilidad según Precio del Producto")
    st.markdown("Analiza si ganas más con productos baratos o caros.")
    
    # Creamos categorías de precio al vuelo para este gráfico
    # Usamos 'qcut' de pandas para dividir en 3 grupos iguales (Terciles)
    try:
        df_filtrado['Categoría Precio'] = pd.qcut(df_filtrado['Precio'], q=3, labels=["Económico", "Medio", "Premium"])
        
        fig_box = px.box(
            df_filtrado, 
            x="Categoría Precio", 
            y="Margen_%", 
            color="Categoría Precio",
            points="all", # Muestra los puntos individuales también
            title="Dispersión de Márgenes por Tipo de Producto"
        )
        st.plotly_chart(fig_box, use_container_width=True)
        st.info("💡 **Tip de Negocio:** Si la caja 'Premium' está muy abajo, estás perdiendo oportunidad en los productos caros.")
    except ValueError:
        st.warning("No hay suficientes datos filtrados para crear categorías de precio.")

with tab3:
    col_tabla, col_descarga = st.columns([3, 1])
    
    with col_tabla:
        st.dataframe(df_filtrado.style.format({"Precio": "${:,.2f}", "Costo": "${:,.2f}", "Margen_%": "{:.2f}%"}).background_gradient(subset=['Margen_%'], cmap='Greens'), use_container_width=True)
    
    with col_descarga:
        st.subheader("Acciones")
        # Botón especial para descargar SOLO los críticos
        criticos = df_filtrado[df_filtrado['Margen_%'] < 15]
        st.write(f"Hay **{len(criticos)}** productos urgentes.")
        
        st.download_button(
            label="🚨 Descargar Lista Crítica",
            data=criticos.to_csv(index=False, sep=';', decimal=',').encode('utf-8'),
            file_name='productos_revisar_precio.csv',
            mime='text/csv',
            type='primary' # Lo hace rojo/destacado
        )
        
        st.write("---")
        st.download_button(
            label="📥 Descargar Todo Filtrado",
            data=df_filtrado.to_csv(index=False, sep=';', decimal=',').encode('utf-8'),
            file_name='analisis_completo.csv',
            mime='text/csv'
        )
