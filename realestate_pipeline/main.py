import pandas as pd

from src.bronze.ingest_api import run_api_extractors
from src.bronze.ingest_web import run_web_scrapers
from src.silver.clean_api import limpiar_anutibara_api, limpiar_panda_api
from src.silver.clean_ssr import limpiar_santafe_ssr


def ejecutar_ingesta_bronze():
    """
    Punto de entrada único. Controla el flujo completo de la capa Bronze.
    Aísla errores para que el fallo de una capa no detenga todo el sistema.
    """
    print("\n" + "="*50)
    print("INICIANDO PIPELINE: INGESTA LAYER 1 (BRONZE)")
    print("="*50)
    
    resumen = {"exitosos": 0, "fallidos": 0}

    print("\n---> FASE 1: Extractores API REST")
    try:
        api_results = run_api_extractors()
        for ruta in api_results.values():
            if ruta: resumen["exitosos"] += 1
            else: resumen["fallidos"] += 1
    except (OSError, ValueError) as e:
        print(f"[!] Error crítico en bloque API: {e}")

    print("\n---> FASE 2: Extractores Web SSR")
    try:
        web_results = run_web_scrapers()
        for ruta in web_results.values():
            if ruta: resumen["exitosos"] += 1
            else: resumen["fallidos"] += 1
    except (OSError, ValueError) as e:
        print(f"[!] Error crítico en bloque WEB: {e}")

    print("\n" + "="*50)
    print("REPORTE DE INGESTA BRONZE")
    print(f"Archivos guardados exitosamente: {resumen['exitosos']}")
    print(f"Fuentes con fallos: {resumen['fallidos']}")
    print("="*50)
    
    if resumen["fallidos"] > 0:
        print("Revisa los logs para identificar qué fuentes fallaron o si hubo bloqueos.")
        
    return api_results, web_results

def ejecutar_transformacion_silver(api_rutas, web_rutas):
    """
    Toma las rutas de los archivos crudos (Bronze) y ejecuta su respectivo
    limpiador para generar los archivos Parquet sin datos PII (Silver).
    """
    print("\n" + "="*50)
    print("INICIANDO PIPELINE: TRANSFORMACIÓN LAYER 2 (SILVER)")
    print("="*50)
    
    dataframes_limpios = []
    
    # 1. Limpiar Pandas (API)
    ruta_panda = api_rutas.get("panda")
    if ruta_panda:
        df_panda = limpiar_panda_api(ruta_panda)
        if df_panda is not None: dataframes_limpios.append(df_panda)
        
    # 2. Limpiar Anutibara (API)
    ruta_anutibara = api_rutas.get("anutibara")
    if ruta_anutibara:
        df_anutibara = limpiar_anutibara_api(ruta_anutibara)
        if df_anutibara is not None: dataframes_limpios.append(df_anutibara)
        
    # 3. Limpiar Santa Fe (SSR)
    ruta_santafe = web_rutas.get("santafe")
    if ruta_santafe:
        df_santafe = limpiar_santafe_ssr(ruta_santafe)
        if df_santafe is not None: dataframes_limpios.append(df_santafe)
        
    # Consolidar todo para mostrarlo en pantalla
    if dataframes_limpios:
        df_master = pd.concat(dataframes_limpios, ignore_index=True)
        print("\n" + "="*50)
        print("📊 TABLA DE INMUEBLES CONSOLIDADOS (SILVER LAYER)")
        print("="*50)
        # Formateamos el precio para que se vea más bonito en consola
        df_display = df_master.copy()
        df_display['precio_cop'] = df_display['precio_cop'].apply(lambda x: f"${x:,.0f}")
        df_display['precio_x_m2'] = df_display['precio_x_m2'].apply(lambda x: f"${x:,.0f}" if pd.notnull(x) else "N/A")
        
        print(df_display.head(10).to_string(index=False))
        print(f"\n[*] Total de inmuebles limpios listos para analítica: {len(df_master)}")
    else:
        print("[-] No se generaron datos limpios en la capa Silver.")

if __name__ == "__main__":
   
    rutas_api, rutas_web = ejecutar_ingesta_bronze()
    
    ejecutar_transformacion_silver(rutas_api, rutas_web)