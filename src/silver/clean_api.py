import json
import os
import pandas as pd
from datetime import datetime
from pydantic import ValidationError
from .schema import InmuebleSilver


def _guardar_silver_parquet(df, fuente_nombre):
    """Guarda el DataFrame limpio en la capa Silver en formato Parquet."""
    if df.empty:
        return None
        
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    timestamp = datetime.now().strftime("%H%M%S")
    
    directorio_silver = os.path.join("data", "silver", fecha_hoy)
    os.makedirs(directorio_silver, exist_ok=True)
    
    ruta_parquet = os.path.join(directorio_silver, f"{fuente_nombre}_{timestamp}.parquet")
    df.to_parquet(ruta_parquet, index=False)
    print(f"[+] SILVER: Datos limpios (Sin PII) guardados en Parquet -> {ruta_parquet}")
    
    return df

def limpiar_panda_api(ruta_archivo):
    """Lee el JSON crudo de Panda y lo pasa por el tamiz de Pydantic."""
    if not ruta_archivo or not os.path.exists(ruta_archivo):
        return pd.DataFrame()
        
    with open(ruta_archivo, 'r', encoding='utf-8') as f:
        datos_crudos = json.load(f)
        
    inmuebles_limpios = []
    lista_inmuebles = datos_crudos if isinstance(datos_crudos, list) else datos_crudos.get('data', [])
    
    registros_exitosos = 0
    registros_fallidos = 0
    
    for item in lista_inmuebles:
        if not item.get('forRent', False): continue
            
        # 1. Construimos el diccionario base
        raw_dict = {
            'id_inmueble': f"PANDA-{item.get('code', 'UNK')}",
            'fuente': 'Panda Inmobiliaria',
            'barrio': item.get('suburb'),
            'precio_cop': item.get('price', 0),
            'area_m2': item.get('builtArea', 0),
            'habitaciones': item.get('rooms', 0),
            'banos': item.get('bathrooms', 0)
        }
        
        # 2. Validación con Pydantic
        try:
            inmueble_validado = InmuebleSilver(**raw_dict)
            # model_dump() exporta solo los campos definidos en Pydantic
            inmuebles_limpios.append(inmueble_validado.model_dump())
            registros_exitosos += 1
        except ValidationError as e:
            registros_fallidos += 1
            # Podrías loguear 'e' para ver exactamente por qué falló
            
    print(f"[*] PANDA Validación: {registros_exitosos} válidos, {registros_fallidos} descartados por contrato.")
    
    df = pd.DataFrame(inmuebles_limpios)
    return _guardar_silver_parquet(df, "panda_limpio")

def limpiar_anutibara_api(ruta_archivo):
    """Lógica de limpieza específica para el JSON de Anutibara."""
    if not ruta_archivo or not os.path.exists(ruta_archivo):
        return pd.DataFrame(columns=COLUMNAS_PERMITIDAS)
        
    with open(ruta_archivo, 'r', encoding='utf-8') as f:
        datos_crudos = json.load(f)
        
    inmuebles_limpios = []
    # Dependiendo de la estructura real de Anutibara, iteramos:
    # (Simularemos la estructura basándonos en tu prompt anterior)
    lista_inmuebles = datos_crudos.get('items', []) if isinstance(datos_crudos, dict) else datos_crudos
    
    for item in lista_inmuebles:
        precio = int(item.get('price', 0))
        area = int(item.get('area', 0))
        
        inmueble = {
            'id_inmueble': f"ANUTI-{item.get('id', 'UNK')}",
            'fuente': 'Anutibara',
            'barrio': str(item.get('neighborhood', 'Sin Barrio')).strip(),
            'precio_cop': precio,
            'area_m2': area,
            'habitaciones': int(item.get('bedrooms', 0)),
            'banos': int(item.get('bathrooms', 0)),
            'precio_x_m2': (precio / area) if area > 0 else None
        }
        if inmueble['precio_cop'] > 0:
            inmuebles_limpios.append(inmueble)

    df = pd.DataFrame(inmuebles_limpios, columns=COLUMNAS_PERMITIDAS)
    return _guardar_silver_parquet(df, "anutibara_limpio")