import duckdb
import os

def query_conglomerado_barrios(base_silver_sql):
    return f"""
    {base_silver_sql},
    barrios AS (
        SELECT
            barrio,
            AVG(precio_cop) AS precio_promedio_barrio,
            COUNT(*) AS cantidad_inmuebles
        FROM inmuebles_unicos
        GROUP BY barrio
    ),
    barrios_clasificados AS (
        SELECT
            b.barrio,
            b.precio_promedio_barrio,
            b.cantidad_inmuebles,
            r.rango_precio AS rango_precio_promedio,
            r.orden
        FROM barrios b
        INNER JOIN rangos_def r
            ON b.precio_promedio_barrio >= r.min_precio
           AND (r.max_precio IS NULL OR b.precio_promedio_barrio < r.max_precio)
    )
    SELECT
        rango_precio_promedio,
        STRING_AGG(barrio, ', ' ORDER BY barrio) AS barrios,
        COUNT(*) AS cantidad_barrios,
        ROUND(AVG(precio_promedio_barrio), 2) AS promedio_del_conglomerado,
        SUM(cantidad_inmuebles) AS cantidad_inmuebles
    FROM barrios_clasificados
    GROUP BY rango_precio_promedio
    ORDER BY MIN(orden);
    """

def procesar_conglomerado(base_silver_sql, ruta_salida):
    """Ejecuta el Mart de Conglomerados y lo exporta a Parquet para rendimiento."""
    query = query_conglomerado_barrios(base_silver_sql)
    df = duckdb.query(query).df()
    
    os.makedirs(os.path.dirname(ruta_salida), exist_ok=True)
    df.to_parquet(ruta_salida, index=False) # Optimización para el Dashboard
    print(f"[+] Mart creado: Conglomerado de Barrios -> {ruta_salida}")
    return df