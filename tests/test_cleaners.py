import pandas as pd  # noqa: I001
import pytest
from pathlib import Path
from datetime import datetime

@pytest.fixture
def archivos_silver_reales():
    """Busca el CSV más reciente de cada fuente generado hoy en Silver."""
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    ruta_silver = Path(f"data/silver/{fecha_hoy}")
    
    if not ruta_silver.exists():
        pytest.skip(f"No hay carpeta silver generada para hoy ({fecha_hoy}). Ejecuta main.py primero.")
        
    archivos_por_fuente = {}
    for archivo in ruta_silver.rglob("*.csv"):
        if "cuarentena" in archivo.parts:
            continue
        fuente = archivo.parent.name
        anterior = archivos_por_fuente.get(fuente)
        if anterior is None or archivo.stat().st_mtime > anterior.stat().st_mtime:
            archivos_por_fuente[fuente] = archivo

    archivos = list(archivos_por_fuente.values())
    if not archivos:
        pytest.skip(f"No hay archivos CSV en la carpeta silver de hoy: {ruta_silver}.")
        
    return archivos

def test_contrato_columnas_silver(archivos_silver_reales):
    """Valida que los archivos cumplan estrictamente con el contrato de columnas requeridas."""
    columnas_requeridas = [
        "id_inmueble", "fuente", "barrio", "precio_cop", 
        "area_m2", "habitaciones", "banos", "precio_x_m2"
    ]
    for archivo in archivos_silver_reales:
        df = pd.read_csv(archivo)
        
        assert not df.empty, f"El archivo {archivo.name} está vacío."
        
        for col in columnas_requeridas:
            assert col in df.columns, f"Falta la columna requerida '{col}' en {archivo.name}"

def test_integridad_ids_y_precios(archivos_silver_reales):
    """Valida que no existan IDs nulos y que los precios sean positivos."""
    for archivo in archivos_silver_reales:
        df = pd.read_csv(archivo)
        
        assert not df["id_inmueble"].isnull().any(), f"Hay IDs nulos en {archivo.name}"
        assert (df["precio_cop"] > 0).all(), f"Se encontraron precios <= 0 en {archivo.name}"

def test_ausencia_duplicados_silver(archivos_silver_reales):
    """Valida que no existan inmuebles duplicados dentro del mismo archivo CSV."""
    for archivo in archivos_silver_reales:
        df = pd.read_csv(archivo)
        duplicados = df.duplicated(subset=['id_inmueble']).sum()
        assert duplicados == 0, f"¡Alerta! El archivo {archivo.name} tiene {duplicados} IDs duplicados."

def test_tipos_datos_correctos_silver(archivos_silver_reales):
    """Valida que las métricas financieras y estructurales sean estrictamente numéricas."""
    for archivo in archivos_silver_reales:
        df = pd.read_csv(archivo)
        
        assert pd.api.types.is_numeric_dtype(df['precio_cop']), f"'precio_cop' en {archivo.name} no es numérico."
        assert pd.api.types.is_numeric_dtype(df['area_m2']), f"'area_m2' en {archivo.name} no es numérico."
        assert pd.api.types.is_numeric_dtype(df['habitaciones']), f"'habitaciones' en {archivo.name} no es numérico."
        assert pd.api.types.is_numeric_dtype(df['banos']), f"'banos' en {archivo.name} no es numérico."
        assert pd.api.types.is_numeric_dtype(df['precio_x_m2']), f"'precio_x_m2' en {archivo.name} no es numérico."
        


