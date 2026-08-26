import os
import json
from abc import ABC, abstractmethod
from datetime import datetime
from src.utils.scraper_client import ScraperClient

class BaseExtractor(ABC):
    """
    Superclase abstracta para todos los extractores de la capa Bronze.
    Define el contrato estándar y la lógica de persistencia compartida.
    """
    def __init__(self, source_name: str, file_extension: str, use_cloudscraper: bool = False):
        self.source_name = source_name
        self.file_extension = file_extension
        # Inyección de dependencia del cliente HTTP adaptado según necesidad (Rest o Cloudscraper)
        self.client = ScraperClient(use_cloudscraper=use_cloudscraper)
    
    @abstractmethod
    def extract(self):
        """
        Método abstracto. Cada subclase (API o SSR) DEBE implementar su propia 
        lógica de extracción y retornar los datos crudos (dict, list, str).
        """
        pass
    
    def save_data(self, data):
        """
        Guarda los datos usando Hive Partitioning y genera un archivo de metadata.
        """
        if not data:
            print(f"[-] {self.source_name}: No hay datos para guardar.")
            return None
            
        now = datetime.now()
        
        # 1. Estructura de Hive Partitioning
        hive_path = os.path.join(
            "data", "bronze",
            f"fuente={self.source_name}",
            f"year={now.year}",
            f"month={now.month:02d}",
            f"day={now.day:02d}"
        )
        os.makedirs(hive_path, exist_ok=True)
        
        # 2. Guardar el archivo principal
        timestamp = now.strftime("%H%M%S")
        nombre_archivo = f"raw_data_{timestamp}.{self.file_extension}"
        ruta_completa = os.path.join(hive_path, nombre_archivo)
        
        try:
            with open(ruta_completa, 'w', encoding='utf-8') as archivo:
                if self.file_extension == "json":
                    json.dump(data, archivo, ensure_ascii=False, indent=4)
                else:
                    archivo.write(str(data))
            
            # 3. Generar y guardar Metadata
            metadata = {
                "fuente": self.source_name,
                "timestamp_extraccion": now.isoformat(),
                "formato": self.file_extension,
                "ruta_archivo": ruta_completa,
                "registros_estimados": len(data) if isinstance(data, (list, dict)) else "N/A (HTML)"
            }
            
            ruta_meta = os.path.join(hive_path, f"_metadata_{timestamp}.json")
            with open(ruta_meta, 'w', encoding='utf-8') as f_meta:
                json.dump(metadata, f_meta, ensure_ascii=False, indent=4)
                    
            print(f"[+] BRONZE: Guardado (Hive) -> {ruta_completa}")
            return ruta_completa
            
        except Exception as e:
            print(f"[-] Error fatal guardando {self.source_name}: {e}")
            return None

    def run(self):
        """
        Patrón Template Method: Define el esqueleto de la ejecución.
        No debe ser sobreescrito por las subclases.
        """
        print(f"[*] Ejecutando Extractor: {self.source_name.upper()}")
        datos_crudos = self.extract()
        ruta_guardado = self.save_data(datos_crudos)
        return ruta_guardado