
import os
from datetime import datetime
from bs4 import BeautifulSoup
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


def _construir_url_santafe(pagina):
    return (
        "https://arrendamientossantafe.com/propiedades/"
        f"?page={pagina}&bussines_type=Arrendar&real_estate_type=Apartamento"
    )


def _contar_inmuebles_en_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    return len(soup.find_all('div', class_='property-card'))

def extraer_santafe(client: ScraperClient, max_paginas=None):
    """
    Extrae el HTML crudo de Arrendamientos Santa Fe recorriendo el paginado.
    - max_paginas=None: recorre hasta que no haya inmuebles o la página se repita.
    - max_paginas=N: limita la extracción a N páginas.

    Guarda un único HTML concatenado para mantener compatibilidad con Silver.
    """
    pagina_actual = 1
    html_paginas = []
    hash_anterior = None

    while True:
        if max_paginas is not None and pagina_actual > max_paginas:
            print(f"[*] Límite alcanzado para Santa Fe: {max_paginas} páginas")
            break

        url = _construir_url_santafe(pagina_actual)
        print(f"[*] Ejecutando Extractor SSR: Santa Fe (Página {pagina_actual})")
        respuesta = client.fetch(url)

        if not respuesta:
            print(f"[-] Sin respuesta en página {pagina_actual}. Se detiene extracción.")
            break

        html_actual = respuesta.text
        hash_actual = hash(html_actual)
        cantidad_inmuebles = _contar_inmuebles_en_html(html_actual)

        if cantidad_inmuebles == 0:
            print(f"[*] Página {pagina_actual} sin inmuebles. Fin del paginado.")
            break

        if hash_anterior is not None and hash_actual == hash_anterior:
            print(
                f"[*] Página {pagina_actual} repite contenido de la anterior. "
                "Fin del paginado."
            )
            break

        html_paginas.append(html_actual)
        print(f"[+] Página {pagina_actual}: {cantidad_inmuebles} inmuebles detectados")

        hash_anterior = hash_actual
        pagina_actual += 1

    if not html_paginas:
        return None

    separador = "\n\n<!-- PAGE_BREAK_SANTAFE -->\n\n"
    html_unificado = separador.join(html_paginas)
    ruta = _guardar_bronze_html(html_unificado, "santafe_ssr")
    print(f"[+] Santa Fe: {len(html_paginas)} páginas extraídas y unificadas")
    return ruta

def run_web_scrapers():
    """Ejecuta todos los extractores web (SSR)."""

    client = ScraperClient(use_cloudscraper=True)

    # Version de prueba rapida (solo 5 paginas):
    # resultados = {"santafe": extraer_santafe(client, max_paginas=5)}

    resultados = {"santafe": extraer_santafe(client)}
    return resultados