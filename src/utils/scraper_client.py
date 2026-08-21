import requests
import cloudscraper
import time
import random
from requests.exceptions import RequestException

class ScraperClient:
    """
    Cliente HTTP personalizado.
 
    """
    def __init__(self, use_cloudscraper=False):
        self.use_cloudscraper = use_cloudscraper
        if self.use_cloudscraper:
            self.session = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
        else:
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36 Edg/150.0.0.0',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'es-419,es;q=0.9,es-ES;q=0.8,en;q=0.7',
            })

    def fetch(self, url, method='GET', params=None, headers=None, cookies=None, retries=3, delay_range=(2.0, 5.0)):
        """
        Realiza la petición HTTP con reintentos y esperas aleatorias (politeness).
        """
        temp_headers = self.session.headers.copy()
        if headers:
            temp_headers.update(headers)

        for attempt in range(retries):
            try:
                if method.upper() == 'GET':
                    response = self.session.get(url, params=params, headers=temp_headers, cookies=cookies, timeout=15)
                else:
                    raise ValueError(f"Método {method} no implementado en esta versión básica.")
                
                if response.status_code in [403, 503] and self.use_cloudscraper:
                     raise PermissionError(f"Bloqueo anti-bot (Cloudflare/DDoS) detectado en {url}")

                response.raise_for_status()
                return response
                
            except (RequestException, PermissionError) as e:
                print(f"[!] Intento {attempt + 1}/{retries} fallido para {url}: {e}")
                if attempt < retries - 1:
                    sleep_time = random.uniform(*delay_range)
                    print(f"[*] Esperando {sleep_time:.2f}s antes de reintentar...")
                    time.sleep(sleep_time)
                else:
                    print(f"[-] Todos los intentos fallaron para {url}.")
                    return None