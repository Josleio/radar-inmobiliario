import json
import pytest
from pathlib import Path
from datetime import datetime

@pytest.fixture
def archivos_bronze_reales():
    """Obtiene dinámicamente los archivos descargados hoy en la capa Bronze."""
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    ruta_bronze = Path(f"data/bronze/{fecha_hoy}")
    
    if not ruta_bronze.exists():
        pytest.skip(f"No hay carpeta bronze para hoy ({fecha_hoy}). Ejecuta la ingesta primero.")
        
    archivos = list(ruta_bronze.rglob("*.json")) + list(ruta_bronze.rglob("*.html"))
    if not archivos:
        pytest.skip("La carpeta bronze de hoy está vacía.")
        
    return archivos

def test_frescura_archivos_bronze(archivos_bronze_reales):
    """
    PRUEBA DE FRESCURA (Freshness):
    Verifica que los archivos fueron creados o modificados en la fecha actual.
    Evita procesar archivos viejos si el script de extracción falló silenciosamente.
    """
    hoy = datetime.now().date()
    for archivo in archivos_bronze_reales:
        # Extraemos la fecha de modificación (mtime) del archivo en el sistema operativo
        mtime = datetime.fromtimestamp(archivo.stat().st_mtime).date()
        assert mtime == hoy, f"El archivo {archivo.name} es antiguo (modificado el {mtime})."

def test_integridad_archivos_bronze(archivos_bronze_reales):
    """
    PRUEBA DE INTEGRIDAD:
    Verifica que los JSON sean parseables y los HTML contengan estructura real,
    descartando errores 500, 502 o páginas de bloqueo de Cloudflare.
    """
    for archivo in archivos_bronze_reales:
        contenido = archivo.read_text(encoding="utf-8")
        
        if archivo.suffix == '.json':
            try:
                # Si la API devolvió un 404/502 en HTML por error, esto lanzará JSONDecodeError
                json.loads(contenido)
            except json.JSONDecodeError:
                pytest.fail(f"Fallo de integridad: {archivo.name} no es un JSON válido.")
                
        elif archivo.suffix == '.html':
            # Verificaciones básicas de un DOM válido y ausencia de bloqueos
            contenido_lower = contenido.lower()
            assert "<html" in contenido_lower or "<div" in contenido_lower, \
                f"{archivo.name} no parece ser un documento HTML válido."
            assert "502 bad gateway" not in contenido_lower, \
                f"{archivo.name} contiene un error de servidor (502)."
            assert "just a moment..." not in contenido_lower, \
                f"{archivo.name} fue bloqueado por la pantalla de desafío de Cloudflare."

def _contar_ids_distintos(objeto):
    """Recorre recursivamente el JSON buscando valores de id y cuenta cuáles son distintos."""
    ids = set()

    def recorrer(valor):
        if isinstance(valor, dict):
            for clave, item in valor.items():
                if clave == 'id':
                    try:
                        ids.add(str(item))
                    except Exception:
                        pass
                recorrer(item)
        elif isinstance(valor, list):
            for item in valor:
                recorrer(item)

    recorrer(objeto)
    return len(ids)


def test_volumen_minimo_extraccion(archivos_bronze_reales):
    """
    PRUEBA DE VOLUMEN MÍNIMO:
    Asegura que las respuestas no vengan vacías o con una cantidad irrisoria de registros.
    """
    UMBRAL_MINIMO = 3  # Exigimos al menos 3 inmuebles por fuente para considerarlo un éxito

    for archivo in archivos_bronze_reales:
        if archivo.suffix == '.json':
            datos = json.loads(archivo.read_text(encoding="utf-8"))
            cantidad = _contar_ids_distintos(datos)

            assert cantidad >= UMBRAL_MINIMO, (
                f"¡Alerta de Volumen! {archivo.name} solo trajo {cantidad} ids distintos dentro del JSON."
            )

        elif archivo.suffix == '.html':
            contenido = archivo.read_text(encoding="utf-8")
            # Contamos cuántas tarjetas de propiedades hay basándonos en la clase estándar del scraper
            cantidad_tarjetas = contenido.count("property-card")

            assert cantidad_tarjetas >= UMBRAL_MINIMO, \
                f"¡Alerta de Volumen! {archivo.name} solo contiene {cantidad_tarjetas} etiquetas 'property-card'."