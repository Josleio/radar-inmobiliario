import duckdb

def generar_mart_tendencias():
    # DuckDB lee directamente todos los CSV de la carpeta Silver.
    query = """
    WITH stats_barrio AS (
        SELECT 
            barrio,
            COUNT(id_inmueble) as total_ofertas,
            AVG(precio_x_m2) as avg_precio_m2,
            -- Window function: ranking de barrios más caros
            RANK() OVER(ORDER BY AVG(precio_x_m2) DESC) as ranking_precio
        FROM read_csv_auto('data/silver/**/*.csv', union_by_name = true)
        WHERE precio_x_m2 IS NOT NULL
        GROUP BY barrio
    )
    SELECT * FROM stats_barrio WHERE total_ofertas > 2;
    """
    
    # Ejecuta el SQL complejo y lo guarda en un CSV listo para Power BI
    resultado = duckdb.query(query).df()
    resultado.to_csv('data/tendencias_mercado.csv', index=False)
    print("✅ Mart analítico actualizado.")

if __name__ == "__main__":
    generar_mart_tendencias()