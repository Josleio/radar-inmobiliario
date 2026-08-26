from typing import Optional

from .base_extractor import BaseExtractor


class SantaFeExtractor(BaseExtractor):
    """Subclase polimórfica para el SSR de Arrendamientos Santa Fe."""
    
    def __init__(self):
        # Observa cómo activamos use_cloudscraper=True desde el inicializador
        super().__init__(source_name="santafe_ssr", file_extension="html", use_cloudscraper=True)

    def extract(self) -> Optional[str]: # pyright: ignore[reportIncompatibleMethodOverride]
        url = "https://arrendamientossantafe.com/propiedades/?page=1&bussines_type=Arrendar&real_estate_type=Apartamento"
        
        respuesta = self.client.fetch(url)
        # Devolvemos el HTML como texto plano, la superclase lo guardará correctamente gracias al self.file_extension
        return respuesta.text if respuesta else None

def run_web_scrapers():
    """Instancia y ejecuta todas las subclases Web (SSR)."""
    resultados = {
        "santafe": SantaFeExtractor().run()
    }
    return resultados