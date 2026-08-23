import json
import os
from datetime import datetime

import pandas as pd

# CONTRATO DE DATOS (Lista Blanca):
# Solo estas columnas sobrevivirán. Cualquier nodo como 'agents', 'owner_contact', 
# 'phones' o 'emails' será ignorado automáticamente al no estar aquí.
COLUMNAS_PERMITIDAS = [
    'id_inmueble', 'fuente', 'barrio', 'precio_cop', 
    'area_m2', 'habitaciones', 'banos', 'precio_x_m2'
]

def _a_entero(valor):
    """Convierte valores numéricos del API y retorna cero si están vacíos."""
    try:
        return int(float(str(valor).replace(',', '').strip())) if valor not in (None, '') else 0
    except (TypeError, ValueError):
        return 0


def _guardar_silver_csv(df, fuente_nombre):
    """Guarda el DataFrame limpio en la capa Silver en formato CSV."""
    df_exportable = df[df['precio_cop'].fillna(0) > 0].copy()
    if df_exportable.empty:
        return df

    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    timestamp = datetime.now().strftime("%H%M")
    carpeta_hora = f"{timestamp[0:2]}H{timestamp[2:4]}M"
    directorio_silver = os.path.join("data", "silver", fecha_hoy, carpeta_hora)
    os.makedirs(directorio_silver, exist_ok=True)

    seccion = fuente_nombre.replace("_limpio", "")
    directorio_seccion = os.path.join(directorio_silver, f"{seccion}_silver")
    os.makedirs(directorio_seccion, exist_ok=True)

    ruta_csv = os.path.join(directorio_seccion, f"{fuente_nombre}_{timestamp}.csv")
    df_exportable.to_csv(ruta_csv, index=False)
    print(f"[+] SILVER: Datos limpios guardados en CSV -> {ruta_csv}")

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

        precio = _a_entero(item.get('canon', 0))
        codigo = item.get('code')
        if not codigo:
            continue  # Si no tiene código, descartamos
        
        area = _a_entero(item.get('builtArea', 0))
        
        # APLICACIÓN DE LISTA BLANCA (Ignoramos el nodo 'agents' por completo)
        inmueble = {
            'id_inmueble': f"PANDA-{codigo}",
            'fuente': 'Panda Inmobiliaria',
            'barrio': str(item.get('suburb', 'Sin Barrio')).strip(),
            'precio_cop': precio,
            'area_m2': area,
            'habitaciones': _a_entero(item.get('rooms', 0)),
            'banos': _a_entero(item.get('bathrooms', 0)),
            'precio_x_m2': (precio / area) if area > 0 else None
        }
        inmuebles_limpios.append(inmueble)

    df = pd.DataFrame(inmuebles_limpios, columns=COLUMNAS_PERMITIDAS)
    df = df.drop_duplicates(subset=['id_inmueble'], keep='first')
    return _guardar_silver_csv(df, "panda_limpio")


def _extraer_area_y_detalles(property_data):
    """Extrae área, habitaciones y baños."""
    area = 0
    habitaciones = 0
    banos = 0

    facilities = property_data.get('facilities', []) if isinstance(property_data, dict) else []
    for facility in facilities:
        if not isinstance(facility, dict):
            continue
        nombre = facility.get('facility', {}).get('name', '').lower()
        valor = facility.get('value')
        if valor is None:
            continue
        try:
            valor_num = int(float(str(valor).replace(',', '.')))
        except (TypeError, ValueError):
            continue

        if 'area' in nombre:
            area = valor_num
        elif 'alcobas' in nombre or 'habitacion' in nombre:
            habitaciones = valor_num
        elif 'baños' in nombre or 'bano' in nombre or 'bath' in nombre:
            banos = valor_num

    return area, habitaciones, banos


def _listar_promociones_anutibara(datos):
    """Busca recursivamente la colección de inmuebles dentro del JSON."""
    if isinstance(datos, list):
        return datos

    if not isinstance(datos, dict):
        return []

    for clave in ['promotions', 'items', 'data', 'results', 'properties']:
        valor = datos.get(clave)
        if isinstance(valor, list):
            return valor
        if isinstance(valor, dict):
            resultado = _listar_promociones_anutibara(valor)
            if resultado:
                return resultado

    # fallback: recorre recursivamente cualquier lista que contenga elementos con 'property'
    for valor in datos.values():
        if isinstance(valor, list):
            if any(isinstance(item, dict) and 'property' in item for item in valor):
                return valor
            resultado = _listar_promociones_anutibara(valor)
            if resultado:
                return resultado
        elif isinstance(valor, dict):
            resultado = _listar_promociones_anutibara(valor)
            if resultado:
                return resultado

    return []


def limpiar_anutibara_api(ruta_archivo):
    """Lógica de limpieza específica para el JSON real de Anutibara."""
    if not ruta_archivo or not os.path.exists(ruta_archivo):
        return pd.DataFrame(columns=COLUMNAS_PERMITIDAS)

    with open(ruta_archivo, 'r', encoding='utf-8') as f:
        datos_crudos = json.load(f)

    inmuebles_limpios = []
    lista_inmuebles = _listar_promociones_anutibara(datos_crudos)

    for item in lista_inmuebles:
        if not isinstance(item, dict):
            continue

        property_data = item.get('property', {}) if isinstance(item.get('property', {}), dict) else {}
        precio_arriendo = _a_entero(item.get('rentValue', 0))
        precio_venta = _a_entero(item.get('sellValue', 0))
        precio = precio_arriendo if precio_arriendo > 0 else precio_venta

        area, habitaciones, banos = _extraer_area_y_detalles(property_data)
        barrio = str(property_data.get('neighborhood', 'Sin Barrio')).strip()
        property_id = property_data.get('id', item.get('id', 'UNK'))

        inmueble = {
            'id_inmueble': f"ANUTI-{property_id}",
            'fuente': 'Anutibara',
            'barrio': barrio,
            'precio_cop': precio,
            'area_m2': area,
            'habitaciones': habitaciones,
            'banos': banos,
            'precio_x_m2': (precio / area) if area > 0 else None
        }
        inmuebles_limpios.append(inmueble)

    df = pd.DataFrame(inmuebles_limpios, columns=COLUMNAS_PERMITIDAS)
    df = df.drop_duplicates(subset=['id_inmueble'], keep='first')
    return _guardar_silver_csv(df, "anutibara_limpio")