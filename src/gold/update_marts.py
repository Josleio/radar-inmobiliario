import duckdb

def generar_mart_tendencias():
    id_valido_sql = """
    id_inmueble IS NOT NULL
    AND TRIM(id_inmueble) <> ''
    AND REGEXP_MATCHES(TRIM(id_inmueble), '^[A-Z]+-[A-Z0-9]+$')
    AND UPPER(TRIM(id_inmueble)) NOT LIKE '%-UNK%'
    """

    base_silver_sql = f"""
    WITH rangos_def AS (
        SELECT * FROM (VALUES
            (0, 1200000, '[0, 1200000)', 1),
            (1200000, 1800000, '[1200000, 1800000)', 2),
            (1800000, 2500000, '[1800000, 2500000)', 3),
            (2500000, 3500000, '[2500000, 3500000)', 4),
            (3500000, 5000000, '[3500000, 5000000)', 5),
            (5000000, 8000000, '[5000000, 8000000)', 6),
            (8000000, 12000000, '[8000000, 12000000)', 7),
            (12000000, NULL, '[12000000, infinito)', 8)
        ) AS t(min_precio, max_precio, rango_precio, orden)
    ),
    silver_historico AS (
        SELECT
            id_inmueble,
            fuente,
            barrio,
            precio_cop,
            area_m2,
            habitaciones,
            banos,
            precio_x_m2,
            REPLACE(filename, '\\', '/') AS ruta_origen
        FROM read_csv_auto('data/silver/**/*.csv', union_by_name = true, filename = true)
    ),
    silver_con_carpeta AS (
        SELECT
            *,
            REGEXP_EXTRACT(ruta_origen, 'data/silver/([^/]+)/([^/]+)/', 1) AS fecha_carpeta,
            REGEXP_EXTRACT(ruta_origen, 'data/silver/([^/]+)/([^/]+)/', 2) AS hora_carpeta
        FROM silver_historico
    ),
    ultima_carpeta AS (
        SELECT
            fecha_carpeta,
            hora_carpeta
        FROM silver_con_carpeta
        WHERE fecha_carpeta IS NOT NULL
          AND fecha_carpeta <> ''
          AND hora_carpeta IS NOT NULL
          AND hora_carpeta <> ''
        GROUP BY fecha_carpeta, hora_carpeta
        ORDER BY fecha_carpeta DESC, hora_carpeta DESC
        LIMIT 1
    ),
    silver_ultima_carpeta AS (
        SELECT s.*
        FROM silver_con_carpeta s
        INNER JOIN ultima_carpeta u
            ON s.fecha_carpeta = u.fecha_carpeta
           AND s.hora_carpeta = u.hora_carpeta
    ),
    inmuebles_validos_id AS (
        SELECT *
        FROM silver_ultima_carpeta
                WHERE {id_valido_sql}
    ),
    inmuebles_unicos AS (
        SELECT
            id_inmueble,
            fuente,
            barrio,
            precio_cop,
            area_m2,
            habitaciones,
            banos,
            precio_x_m2
        FROM (
            SELECT
                *,
                ROW_NUMBER() OVER (
                    PARTITION BY id_inmueble
                    ORDER BY ruta_origen DESC
                ) AS rn
            FROM inmuebles_validos_id
        ) dedupe
        WHERE rn = 1
    )
    """

    query_validacion_ids = f"""
    {base_silver_sql}
    SELECT
        COUNT(*) AS total_registros_ultima_carpeta,
        SUM(CASE WHEN {id_valido_sql} THEN 1 ELSE 0 END) AS ids_validos,
        SUM(CASE WHEN NOT ({id_valido_sql}) THEN 1 ELSE 0 END) AS ids_invalidos,
        COUNT(*) - COUNT(DISTINCT id_inmueble) AS ids_duplicados
    FROM silver_ultima_carpeta;
    """
    validacion_ids = duckdb.query(query_validacion_ids).df().iloc[0].to_dict()
    print(
        "[ID CHECK] ultima carpeta silver | "
        f"total={int(validacion_ids['total_registros_ultima_carpeta'])}, "
        f"validos={int(validacion_ids['ids_validos'])}, "
        f"invalidos={int(validacion_ids['ids_invalidos'])}, "
        f"duplicados={int(validacion_ids['ids_duplicados'])}"
    )

    query = f"""
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
    
    resultado = duckdb.query(query).df()
    resultado.to_csv('data/tendencias_mercado.csv', index=False)

    query_barrios = f"""
    {base_silver_sql},
    barrios AS (
        SELECT
            barrio,
            AVG(precio_cop) AS precio_promedio_barrio,
            COUNT(*) AS cantidad_inmuebles
        FROM inmuebles_unicos
        WHERE precio_cop IS NOT NULL
          AND precio_cop > 0
          AND barrio IS NOT NULL
          AND TRIM(barrio) <> ''
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

    conglomerado = duckdb.query(query_barrios).df()
    conglomerado.to_csv('data/conglomerado_barrios.csv', index=False)
    print("✅ Marts analíticos actualizados: tendencias_mercado.csv y conglomerado_barrios.csv")

    return resultado, conglomerado

if __name__ == "__main__":
    generar_mart_tendencias()