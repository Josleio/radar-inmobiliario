import os
import re
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime

COLUMNAS_PERMITIDAS = [
    'id_inmueble', 'fuente', 'barrio', 'precio_cop', 
    'area_m2', 'habitaciones', 'banos', 'precio_x_m2'
]

def _guardar_silver_csv(df, fuente_nombre):
    """Guarda el DataFrame limpio en la capa Silver en formato CSV."""
    df_exportable = df[df['precio_cop'].fillna(0) > 0].copy()
    if df_exportable.empty: return df
        
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

def limpiar_santafe_ssr(ruta_archivo):
    """Lee el HTML de Bronze, extrae con BeautifulSoup y retorna DF."""
    if not ruta_archivo or not os.path.exists(ruta_archivo):
        return pd.DataFrame(columns=COLUMNAS_PERMITIDAS)
        
    with open(ruta_archivo, 'r', encoding='utf-8') as f:
        html_crudo = f.read()
        
    soup = BeautifulSoup(html_crudo, 'html.parser')
    inmuebles_limpios = []
    
    contenedores = soup.find_all('div', class_='property-card')
    for div in contenedores:
        datos_limpios = {col: None for col in COLUMNAS_PERMITIDAS}
        datos_limpios['fuente'] = 'Santa Fe'
        datos_limpios['habitaciones'] = 0
        datos_limpios['banos'] = 0
        datos_limpios['area_m2'] = 0
        
        # ID
        span_id = div.find('span', class_='id')
        if span_id:
            match_id = re.search(r'REF:\s*([A-Z0-9]+)', span_id.text)
            if match_id: datos_limpios['id_inmueble'] = f"SF-{match_id.group(1)}"
                
        # Barrio
        div_sector = div.find('div', class_='sector')
        if div_sector and div_sector.find('p', class_='d-inline'):
            match_barrio = re.search(r'Ubicación:\s*(.+)', div_sector.find('p', class_='d-inline').text)
            if match_barrio: datos_limpios['barrio'] = match_barrio.group(1).strip()
        
        # Precio
        div_precio = div.find('div', class_='precio')
        if div_precio:
            precio_limpio = re.sub(r'[^\d]', '', div_precio.text)
            datos_limpios['precio_cop'] = int(precio_limpio) if precio_limpio else None
            
        # Detalles
        div_detalles = div.find('div', class_='detail-prop')
        if div_detalles:
            span_alcobas = div_detalles.find('span', class_='alcobas')
            if span_alcobas:
                habs_str = re.sub(r'[^\d]', '', span_alcobas.text)
                datos_limpios['habitaciones'] = int(habs_str) if habs_str else 0
                
            span_area = div_detalles.find('span', class_='area')
            if span_area:
                match_area = re.search(r'(\d+)\s*m', span_area.text, re.IGNORECASE)
                if match_area: datos_limpios['area_m2'] = int(match_area.group(1))
        
        # Validar y calcular
        if datos_limpios['id_inmueble'] and datos_limpios['precio_cop']:
            if datos_limpios['area_m2'] > 0:
                datos_limpios['precio_x_m2'] = datos_limpios['precio_cop'] / datos_limpios['area_m2']
            inmuebles_limpios.append(datos_limpios)
            
    df = pd.DataFrame(inmuebles_limpios, columns=COLUMNAS_PERMITIDAS)
    return _guardar_silver_csv(df, "santafe_limpio")