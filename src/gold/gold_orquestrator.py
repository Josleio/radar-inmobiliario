import os

import duckdb

from .base_sql import (
    obtener_sql_base_silver,
    obtener_sql_id_valido,
    query_validacion_ids,
)
from .marts.conglomerados import procesar_conglomerado
from .marts.tendencias_mart import procesar_tendencias


def ejecutar_validacion_ids(base_silver_sql, id_valido_sql):
    """Ejecuta la validación de calidad de datos usando DuckDB."""
    query = query_validacion_ids(base_silver_sql, id_valido_sql)
    try:
        validacion_ids = duckdb.query(query).df().iloc[0].to_dict()
        print(
            "[*] [DATA QUALITY CHECK] | "
            f"Total analizados: {int(validacion_ids['total_registros_ultima_carpeta'])} | "
            f"IDs Válidos: {int(validacion_ids['ids_validos'])} | "
            f"Inválidos: {int(validacion_ids['ids_invalidos'])} | "
            f"Duplicados resueltos: {int(validacion_ids['ids_duplicados'])}"
        )
    except Exception as e:
        print(f"[-] No se pudo validar la data de Silver. ¿Existen archivos Parquet? Error: {e}")
        return False
    return True

def generar_mart_tendencias():
    """
    Invoca los scripts modulares de cada Mart.
    """

    
    print("\n" + "="*50)
    print("INICIANDO CAPA GOLD: COMPILANDO MARTS (DUCKDB)")
    print("="*50)
    
    id_valido_sql = obtener_sql_id_valido()
    base_silver_sql = obtener_sql_base_silver(id_valido_sql)
    
    # 1. Ejecutar validaciones de Data Quality previas
    if not ejecutar_validacion_ids(base_silver_sql, id_valido_sql):
        return False
        
    # 2. Rutas de salida Optimizadas para Streamlit (Formato Parquet en lugar de CSV)
    ruta_tendencias = os.path.join("data", "gold", "tendencias_mercado.parquet")
    ruta_conglomerado = os.path.join("data", "gold", "conglomerado_barrios.parquet")

    
    try:
        df_tendencias = procesar_tendencias(base_silver_sql, ruta_tendencias)
        df_conglomerado = procesar_conglomerado(base_silver_sql, ruta_conglomerado)
        
        print(f"   -> Resumen: {len(df_tendencias)} filas de tendencias | {len(df_conglomerado)} filas de conglomerados.")
        
        print("\n✅ Capa Gold generada exitosamente mediante Modelado Dimensional.")
        return True
    except Exception as e:
        print(f"\n[-] Fallo crítico en la generación de Marts: {e}")
        return False

if __name__ == "__main__":
    generar_mart_tendencias()