
import os
from datetime import datetime
from src.utils.scraper_client import ScraperClient

def _guardar_bronze_html(html_content, fuente_nombre):
    """
    Guarda el HTML crudo en data/bronze/YYYY-MM-DD/SSRs/HHHMM/.
    """
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    timestamp = datetime.now().strftime("%H%M")
    
    directorio_bronze = os.path.join("data", "bronze", fecha_hoy, "SSRs", timestamp)
    os.makedirs(directorio_bronze, exist_ok=True)
    
    # Eliminamos el timestamp para sobrescribir en el mismo día
    nombre_archivo = f"{fuente_nombre}.html"
    ruta_completa = os.path.join(directorio_bronze, nombre_archivo)
    
    with open(ruta_completa, 'w', encoding='utf-8') as archivo:
        archivo.write(html_content)
            
    print(f"[+] BRONZE: HTML crudo guardado -> {ruta_completa}")
    return ruta_completa

def extraer_santafe(client: ScraperClient):
    """
    Extrae el HTML crudo de Arrendamientos Santa Fe.
    Guardamos todo el HTML de la página para parsearlo después.
    """
    url = "https://arrendamientossantafe.com/propiedades/?page=1&bussines_type=Arrendar&real_estate_type=Apartamento"
    print(f"[*] Ejecutando Extractor SSR: Santa Fe (Página 1)")
    
    respuesta = client.fetch(url)
    
    if respuesta:
        ruta = _guardar_bronze_html(respuesta.text, "santafe_ssr")
        return ruta
    return None

def run_web_scrapers():
    """Ejecuta todos los extractores web (SSR)."""
    # Requiere Cloudscraper para sortear protecciones
    client = ScraperClient(use_cloudscraper=True) 
    resultados = {"santafe": extraer_santafe(client)}
    return resultados