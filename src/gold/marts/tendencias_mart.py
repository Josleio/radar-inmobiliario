import duckdb
import os

def query_tendencias(base_silver_sql):
    return f"""
    {base_silver_sql},
    inmuebles_validos_precio AS (
        SELECT
            precio_cop,
            rangos_def.rango_precio,
            rangos_def.orden
        FROM inmuebles_unicos
        INNER JOIN rangos_def
            ON inmuebles_unicos.precio_cop >= rangos_def.min_precio
           AND (rangos_def.max_precio IS NULL OR inmuebles_unicos.precio_cop < rangos_def.max_precio)
        WHERE inmuebles_unicos.precio_cop IS NOT NULL
          AND inmuebles_unicos.precio_cop > 0
    )
    SELECT
        rangos_def.rango_precio,
        COUNT(inmuebles_validos_precio.precio_cop) AS cantidad_inmuebles
    FROM rangos_def
    LEFT JOIN inmuebles_validos_precio USING (rango_precio, orden)
    GROUP BY rangos_def.rango_precio, rangos_def.orden
    ORDER BY rangos_def.orden;
    """

def procesar_tendencias(base_silver_sql, ruta_salida):
    """Ejecuta el Mart de Tendencias y lo exporta a Parquet para rendimiento."""
    query = query_tendencias(base_silver_sql)
    df = duckdb.query(query).df()
    
    os.makedirs(os.path.dirname(ruta_salida), exist_ok=True)
    df.to_parquet(ruta_salida, index=False) # Optimización para el Dashboard
    print(f"[+] Mart creado: Tendencias de Mercado -> {ruta_salida}")
    return df