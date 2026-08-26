import random
import time

import cloudscraper
import requests
from requests.exceptions import RequestException


class ScraperClient:
    """
    Cliente HTTP personalizado.
 
    """
    def __init__(self, use_cloudscraper=False):
        self.use_cloudscraper = use_cloudscraper
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0'
        ]
        if self.use_cloudscraper:
            self.session = cloudscraper.create_scraper(
                browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False}
            )
        else:
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'es-419,es;q=0.9,es-ES;q=0.8,en;q=0.7',
            })

    def fetch(self, url, method='GET', params=None, headers=None, cookies=None, retries=3, delay_range=(2.0, 5.0)):
        """
        Realiza la petición HTTP con reintentos, esperas aleatorias y exponential backoff.
        """
        temp_headers = self.session.headers.copy()
        if headers:
            temp_headers.update(headers)
        
        # Rotar User-Agent en cada llamada si no es cloudscraper
        if not self.use_cloudscraper:
            temp_headers['User-Agent'] = random.choice(self.user_agents)

        for attempt in range(retries):
            try:
                if method.upper() == 'GET':
                    response = self.session.get(url, params=params, headers=temp_headers, cookies=cookies, timeout=20)
                else:
                    raise ValueError(f"Método {method} no implementado.")
                
                # Manejo de códigos de estado de bloqueo
                if response.status_code in [403, 503, 429]:
                    print(f"[!] Bloqueo detectado ({response.status_code}) en {url}")
                    if self.use_cloudscraper:
                        raise PermissionError(f"Cloudflare/WAF detectado: {response.status_code}")
                    else:
                        # Forzar reintento con espera más larga
                        raise RequestException(f"Status {response.status_code}")

                response.raise_for_status()
                return response
                
            except (RequestException, PermissionError) as e:
                # Exponential backoff: aumenta el tiempo de espera en cada reintento
                wait_multiplier = 2 ** attempt
                sleep_time = random.uniform(*delay_range) * wait_multiplier
                
                print(f"[!] Intento {attempt + 1}/{retries} fallido para {url}: {e}")
                
                if attempt < retries - 1:
                    print(f"[*] Reintentando en {sleep_time:.2f}s...")
                    time.sleep(sleep_time)
                else:
                    print(f"[-] Fallo definitivo en {url} tras {retries} intentos.")
                    return None