import json
import os
from datetime import datetime
from src.utils.scraper_client import ScraperClient

def _guardar_bronze(datos, fuente_nombre, extension="json"):
    """
    Guarda los datos crudos en la carpeta data/bronze/YYYY-MM-DD/
    """
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    
    directorio_bronze = os.path.join("data", "bronze", fecha_hoy)
    os.makedirs(directorio_bronze, exist_ok=True)
    
    nombre_archivo = f"{fuente_nombre}.{extension}"
    ruta_completa = os.path.join(directorio_bronze, nombre_archivo)
    
    with open(ruta_completa, 'w', encoding='utf-8') as archivo:
        if extension == "json":
            json.dump(datos, archivo, ensure_ascii=False, indent=4)
        else:
            archivo.write(str(datos))
            
    print(f"[+] BRONZE: Datos guardados -> {ruta_completa}")
    return ruta_completa

def extraer_panda(client: ScraperClient):
    """Extrae datos de la API de Panda Inmobiliaria."""
    url = 'https://www.pandainmobiliaria.com/api/properties'
    headers = {
        'referer': 'https://www.pandainmobiliaria.com/inmuebles/ciudad/medellin',
    }
    
    print("[*] Ejecutando Extractor: Panda Inmobiliaria (API)")
    respuesta = client.fetch(url, headers=headers)
    
    if respuesta:
        datos_json = respuesta.json()
        ruta = _guardar_bronze(datos_json, "panda_api")
        return ruta
    return None

def extraer_anutibara(client: ScraperClient):
    """Extrae datos de la API de Anutibara (Página 1)."""
    url = 'https://api.arrendamientosnutibara.com/promotion/search/neighbourhood'
    headers = {
        'origin': 'https://anutibara.com',
        'referer': 'https://anutibara.com/',
    }
    params = {
        'neighborhood': '', 'page': '1', 'priceStart': '1',
        'status': 'PROMOCION', 'type': 'APARTAMENTO',
    }
    
    print("[*] Ejecutando Extractor: Anutibara (API)")
    respuesta = client.fetch(url, params=params, headers=headers)
    
    if respuesta:
        datos_json = respuesta.json()
        ruta = _guardar_bronze(datos_json, "anutibara_api")
        return ruta
    return None

def run_api_extractors():
    """Ejecuta todos los extractores API."""
    client = ScraperClient(use_cloudscraper=False)
    resultados = {"panda": extraer_panda(client), "anutibara": extraer_anutibara(client)}
    return resultados