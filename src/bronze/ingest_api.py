import json
import os
from datetime import datetime

from src.utils.scraper_client import ScraperClient


def _guardar_bronze(datos, fuente_nombre, extension="json"):
    """
    Guarda los datos crudos en data/bronze/YYYY-MM-DD/APIs/HHHMM/.
    """
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    timestamp = datetime.now().strftime("%H%M")
    carpeta_hora = f"{timestamp[0:2]}H{timestamp[2:4]}M"

    directorio_hora = os.path.join("data", "bronze", fecha_hoy, "APIs", carpeta_hora)
    os.makedirs(directorio_hora, exist_ok=True)

    nombre_archivo = f"{fuente_nombre}.{extension}"
    ruta_completa = os.path.join(directorio_hora, nombre_archivo)
    
    with open(ruta_completa, 'w', encoding='utf-8') as archivo:
        if extension == "json":
            json.dump(datos, archivo, ensure_ascii=False, indent=4)
        else:
            archivo.write(str(datos))
            
    print(f"[+] BRONZE: Datos API guardados -> {ruta_completa}")
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
    """Extrae datos de Anutibara recorriendo sus páginas."""
    url = 'https://api.arrendamientosnutibara.com/promotion/search/neighbourhood'
    headers = {
        'Referer': 'https://anutibara.com/',
    }
    params = {
        'neighborhood': '',
        'priceStart': '1',
        'status': 'PROMOCION',
        'type': 'APARTAESTUDIO,APARTAMENTO,CASA',
    }

    print("[*] Ejecutando Extractor: Anutibara (API, todas las páginas)")
    inmuebles = []
    total_esperado = None
    pagina = 1

    while total_esperado is None or len(inmuebles) < total_esperado:
        params['page'] = str(pagina)
        respuesta = client.fetch(url, params=params, headers=headers)

        if not respuesta:
            print(f"[-] Anutibara: no se pudo obtener la página {pagina}.")
            return None

        datos_pagina = respuesta.json()
        datos = datos_pagina.get('data', {}) if isinstance(datos_pagina, dict) else {}
        inmuebles_pagina = datos.get('promotions', []) if isinstance(datos, dict) else []
        total_esperado = int(datos.get('total', 0) or 0) if isinstance(datos, dict) else 0

        if not isinstance(inmuebles_pagina, list) or not inmuebles_pagina:
            break

        inmuebles.extend(inmuebles_pagina)
        print(f"[*] Anutibara: página {pagina}, {len(inmuebles)}/{total_esperado} inmuebles.")
        pagina += 1

    datos_json = {
        'code': 200,
        'success': True,
        'data': {
            'total': len(inmuebles),
            'promotions': inmuebles,
        },
    }
    return _guardar_bronze(datos_json, "anutibara_api")


def run_api_extractors():
    """Ejecuta todos los extractores API."""
    client = ScraperClient(use_cloudscraper=False)
    resultados = {"panda": extraer_panda(client), "anutibara": extraer_anutibara(client)}
    return resultados