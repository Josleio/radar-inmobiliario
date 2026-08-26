from .base_extractor import BaseExtractor


class PandaExtractor(BaseExtractor):
    """Subclase polimórfica para la API de Panda Inmobiliaria."""
    def __init__(self):
        # Configura la base con su nombre, extensión JSON y cliente normal (requests)
        super().__init__(source_name="panda_api", file_extension="json", use_cloudscraper=False)

    def extract(self):
        url = 'https://www.pandainmobiliaria.com/api/properties'
        headers = {'referer': 'https://www.pandainmobiliaria.com/inmuebles/ciudad/medellin'}
        
        respuesta = self.client.fetch(url, headers=headers)
        return respuesta.json() if respuesta else None

class AnutibaraExtractor(BaseExtractor):
    """Subclase polimórfica para la API de Anutibara."""
    def __init__(self):
        super().__init__(source_name="anutibara_api", file_extension="json", use_cloudscraper=False)

    def extract(self):
        url = 'https://api.arrendamientosnutibara.com/promotion/search/neighbourhood'
        headers = {
            'origin': 'https://anutibara.com',
            'referer': 'https://anutibara.com/',
        }
        params = {
            'neighborhood': '', 'page': '1', 'priceStart': '1',
            'status': 'PROMOCION', 'type': 'APARTAMENTO',
        }
        
        respuesta = self.client.fetch(url, params=params, headers=headers)
        return respuesta.json() if respuesta else None

def run_api_extractors():
    """Instancia y ejecuta todas las subclases API."""
    # Las clases manejan todo por debajo de la mesa gracias a run()
    resultados = {
        "panda": PandaExtractor().run(),
        "anutibara": AnutibaraExtractor().run()
    }
    return resultados