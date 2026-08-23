import os

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Radar Inmobiliario", page_icon="🏢", layout="wide")

@st.cache_data
def cargar_datos():
    """Carga los nuevos datos de la capa Gold generados por DuckDB en formato Parquet."""
    # Cambiamos la lectura de .csv a .parquet 
    ruta_tendencias = os.path.join("data", "gold", "tendencias_mercado.parquet")
    ruta_conglomerado = os.path.join("data", "gold", "conglomerado_barrios.parquet")
    
    try:
        df_tendencias = pd.read_parquet(ruta_tendencias) if os.path.exists(ruta_tendencias) else pd.DataFrame()
        df_conglomerado = pd.read_parquet(ruta_conglomerado) if os.path.exists(ruta_conglomerado) else pd.DataFrame()
        return df_tendencias, df_conglomerado
    except Exception as e:
        st.error(f"Error cargando los datos: {e}")
        return pd.DataFrame(), pd.DataFrame()

def main():
    st.title("🏢 Radar Inmobiliario - Analytics (Powered by DuckDB)")
    st.markdown("Dashboard automático leyendo los Data Marts modulares.")
    
    df_tendencias, df_conglomerado = cargar_datos()
    
    if df_tendencias.empty or df_conglomerado.empty:
        st.warning("No hay datos en la capa Gold. Por favor, ejecuta el pipeline completo primero (Opción 1).")
        return
        
    total_inmuebles = df_conglomerado['cantidad_inmuebles'].sum()
    total_barrios = df_conglomerado['cantidad_barrios'].sum()
    
    # KPIs Top
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Inmuebles Validados", f"{int(total_inmuebles)}")
    col2.metric("Barrios Analizados", f"{int(total_barrios)}")
    col3.metric("Rango Más Ofertado", df_tendencias.sort_values('cantidad_inmuebles', ascending=False).iloc[0]['rango_precio'])
    
    st.markdown("---")
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.subheader("Volumen de Oferta por Rango de Precio")
        fig1 = px.bar(
            df_tendencias, 
            x='rango_precio', 
            y='cantidad_inmuebles',
            labels={'rango_precio': 'Rango (COP)', 'cantidad_inmuebles': 'Cantidad'},
            color='cantidad_inmuebles',
            color_continuous_scale='Teal'
        )
        st.plotly_chart(fig1, use_container_width=True)
        
    with col_chart2:
        st.subheader("Promedio de Valor por Conglomerado")
        fig2 = px.pie(
            df_conglomerado, 
            values='cantidad_barrios', 
            names='rango_precio_promedio',
            title='Distribución de Barrios según su Rango de Precio',
            hole=0.4
        )
        st.plotly_chart(fig2, use_container_width=True)
        
    st.markdown("---")
    st.subheader("Explorador de Conglomerados de Barrios")
    st.markdown("Agrupación automática de zonas de la ciudad basada en sus precios promedio.")
    
    # Formateo de la tabla de conglomerados
    df_show = df_conglomerado.copy()
    df_show['promedio_del_conglomerado'] = df_show['promedio_del_conglomerado'].apply(lambda x: f"${x:,.0f}")
    
    st.dataframe(
        df_show[['rango_precio_promedio', 'cantidad_barrios', 'promedio_del_conglomerado', 'cantidad_inmuebles', 'barrios']], 
        use_container_width=True,
        hide_index=True
    )

if __name__ == "__main__":
    main()