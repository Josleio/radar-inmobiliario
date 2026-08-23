def obtener_sql_id_valido():
    """Condición SQL para validar la integridad de los IDs."""
    return """
    id_inmueble IS NOT NULL
    AND TRIM(id_inmueble) <> ''
    AND UPPER(TRIM(id_inmueble)) NOT LIKE '%-UNK%'
    """

def obtener_sql_base_silver(id_valido_sql):
    return f"""
    WITH rangos_def AS (
        SELECT * FROM (VALUES
            (0, 1200000, '[0, 1.2M)', 1),
            (1200000, 1800000, '[1.2M, 1.8M)', 2),
            (1800000, 2500000, '[1.8M, 2.5M)', 3),
            (2500000, 3500000, '[2.5M, 3.5M)', 4),
            (3500000, 5000000, '[3.5M, 5.0M)', 5),
            (5000000, 8000000, '[5.0M, 8.0M)', 6),
            (8000000, 12000000, '[8.0M, 12.0M)', 7),
            (12000000, NULL, '[12.0M, infinito)', 8)
        ) AS t(min_precio, max_precio, rango_precio, orden)
    ),
    silver_historico AS (
        -- DuckDB lee todos los CSVs y auto-detecta las columnas
        SELECT *, 
               REPLACE(filename, '\\', '/') AS ruta_origen,
               REGEXP_EXTRACT(REPLACE(filename, '\\', '/'), 'silver/([^/]+)/', 1) AS fecha_carpeta
        FROM read_csv_auto('data/silver/**/*.csv', filename = true)
    ),
    silver_ultima_carpeta AS (
        -- Filtramos solo los datos del último día ejecutado para no duplicar análisis
        SELECT * FROM silver_historico
        WHERE fecha_carpeta = (SELECT MAX(fecha_carpeta) FROM silver_historico WHERE fecha_carpeta IS NOT NULL)
    ),
    inmuebles_unicos AS (
        -- Deduplicación y filtro de IDs válidos en un solo paso
        SELECT id_inmueble, fuente, barrio, precio_cop, area_m2, habitaciones, banos, precio_x_m2
        FROM (
            SELECT *, ROW_NUMBER() OVER (PARTITION BY id_inmueble ORDER BY ruta_origen DESC) AS rn
            FROM silver_ultima_carpeta
            WHERE {id_valido_sql}
        ) dedupe
        WHERE rn = 1
    )
    """

def query_validacion_ids(base_silver_sql, id_valido_sql):
    return f"""
    {base_silver_sql}
    SELECT
        COUNT(*) AS total_registros_ultima_carpeta,
        SUM(CASE WHEN {id_valido_sql} THEN 1 ELSE 0 END) AS ids_validos,
        SUM(CASE WHEN NOT ({id_valido_sql}) THEN 1 ELSE 0 END) AS ids_invalidos,
        COUNT(*) - COUNT(DISTINCT id_inmueble) AS ids_duplicados
    FROM silver_ultima_carpeta;
    """