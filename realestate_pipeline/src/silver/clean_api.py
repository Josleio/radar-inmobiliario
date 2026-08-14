import json
import os
import pandas as pd
from datetime import datetime

# CONTRATO DE DATOS (Lista Blanca):
# Solo estas columnas sobrevivirán. Cualquier nodo como 'agents', 'owner_contact', 
# 'phones' o 'emails' será ignorado automáticamente al no estar aquí.
COLUMNAS_PERMITIDAS = [
    'id_inmueble', 'fuente', 'barrio', 'precio_cop', 
    'area_m2', 'habitaciones', 'banos', 'precio_x_m2'
]

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
    """Lee el JSON crudo de Panda, extrae solo la lista blanca y retorna un DF."""
    if not ruta_archivo or not os.path.exists(ruta_archivo):
        return pd.DataFrame(columns=COLUMNAS_PERMITIDAS)
        
    with open(ruta_archivo, 'r', encoding='utf-8') as f:
        datos_crudos = json.load(f)
        
    inmuebles_limpios = []
    lista_inmuebles = datos_crudos if isinstance(datos_crudos, list) else datos_crudos.get('data', [])
    
    for item in lista_inmuebles:
        # Ignoramos si no es arriendo
        if not item.get('forRent', False): continue
            
        precio = int(item.get('price', 0))
        area = int(item.get('builtArea', 0))
        
        # APLICACIÓN DE LISTA BLANCA (Ignoramos el nodo 'agents' por completo)
        inmueble = {
            'id_inmueble': f"PANDA-{item.get('code', 'UNK')}",
            'fuente': 'Panda Inmobiliaria',
            'barrio': str(item.get('suburb', 'Sin Barrio')).strip(),
            'precio_cop': precio,
            'area_m2': area,
            'habitaciones': int(item.get('rooms', 0)),
            'banos': int(item.get('bathrooms', 0)),
            'precio_x_m2': (precio / area) if area > 0 else None
        }
        
        if inmueble['precio_cop'] > 0:
            inmuebles_limpios.append(inmueble)
            
    df = pd.DataFrame(inmuebles_limpios, columns=COLUMNAS_PERMITIDAS)
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