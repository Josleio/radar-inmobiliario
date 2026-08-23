import pandas as pd
import pytest
from datetime import datetime
from pathlib import Path
from src.bronze.__init__ import run_api_extractors, run_web_scrapers
from src.silver.clean_api import limpiar_anutibara_api, limpiar_panda_api
from src.silver.clean_ssr import limpiar_santafe_ssr
from src.gold.update_marts import generar_mart_tendencias


def guardar_cuarentena(df):
    """Guarda los registros con precio nulo o cero fuera del consolidado Silver."""
    if df.empty:
        return None

    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    timestamp = datetime.now().strftime("%H%M")
    carpeta_hora = f"{timestamp[0:2]}H{timestamp[2:4]}M"
    directorio = Path("data") / "silver" / fecha_hoy / carpeta_hora / "cuarentena"
    directorio.mkdir(parents=True, exist_ok=True)
    ruta_csv = directorio / f"cuarentena_{timestamp}.csv"
    df.to_csv(ruta_csv, index=False)
    print(f"[!] Se encontraron {len(df)} inmuebles con precios nulos o en 0.")
    print(f"[!] Registros enviados a cuarentena -> {ruta_csv}")
    return ruta_csv


def ejecutar_ingesta_bronze():
    """
    Controla la ejecución de la capa Bronze de forma aislada.
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
        api_results = {}

    print("\n---> FASE 2: Extractores Web SSR")
    try:
        web_results = run_web_scrapers()
        for ruta in web_results.values():
            if ruta: resumen["exitosos"] += 1
            else: resumen["fallidos"] += 1
    except (OSError, ValueError) as e:
        print(f"[!] Error crítico en bloque WEB: {e}")
        web_results = {}

    print("\n" + "="*50)
    print("REPORTE DE INGESTA BRONZE")
    print(f"Archivos guardados exitosamente: {resumen['exitosos']}")
    print(f"Fuentes con fallos: {resumen['fallidos']}")
    print("="*50)
    
    return api_results, web_results

def ejecutar_pruebas_ingestion():
    """Ejecuta los tests de calidad de la capa Bronze (Frescura, Volumen, Integridad)."""
    print("\n" + "="*50)
    print("EJECUTANDO PRUEBAS DE INGESTA (BRONZE)")
    print("="*50)
    exit_code = pytest.main(["tests/test_ingestion.py", "-q"])
    if exit_code == 0:
        print("[✅] Pruebas de ingesta superadas. Los datos crudos son confiables.")
    else:
        print("[!] Las pruebas de ingesta FALLARON.")
    return exit_code

def ejecutar_transformacion_silver(api_rutas, web_rutas):
    """
    Toma las rutas crudas y ejecuta los limpiadores para generar los CSV (Silver).
    """
    print("\n" + "="*50)
    print("INICIANDO PIPELINE: TRANSFORMACIÓN LAYER 2 (SILVER)")
    print("="*50)

    dataframes_limpios = []
    conteos_api = []

    # 1. Limpiar Pandas (API)
    ruta_panda = api_rutas.get("panda")
    if ruta_panda:
        df_panda = limpiar_panda_api(ruta_panda)
        cantidad_panda = 0 if df_panda is None else len(df_panda)
        conteos_api.append({"fuente": "Panda Inmobiliaria", "cantidad_inmuebles": cantidad_panda})
        if df_panda is not None and not df_panda.empty:
            dataframes_limpios.append(df_panda)

    # 2. Limpiar Anutibara (API)
    ruta_anutibara = api_rutas.get("anutibara")
    if ruta_anutibara:
        df_anutibara = limpiar_anutibara_api(ruta_anutibara)
        cantidad_anutibara = 0 if df_anutibara is None else len(df_anutibara)
        conteos_api.append({"fuente": "Anutibara", "cantidad_inmuebles": cantidad_anutibara})
        if df_anutibara is not None and not df_anutibara.empty:
            dataframes_limpios.append(df_anutibara)

    # 3. Limpiar Santa Fe (SSR)
    ruta_santafe = web_rutas.get("santafe")
    if ruta_santafe:
        df_santafe = limpiar_santafe_ssr(ruta_santafe)
        if df_santafe is not None and not df_santafe.empty:
            dataframes_limpios.append(df_santafe)

    # Separar precios inválidos antes de consolidar y ejecutar las pruebas Silver.
    if dataframes_limpios:
        df_todos = pd.concat(dataframes_limpios, ignore_index=True)
        mascara_cuarentena = df_todos["precio_cop"].fillna(0) <= 0
        df_cuarentena = df_todos[mascara_cuarentena].copy()
        guardar_cuarentena(df_cuarentena)
        df_master = df_todos[~mascara_cuarentena].copy()
        dataframes_limpios = [df for df in dataframes_limpios if df is not None and not df.empty]
        dataframes_limpios = [df[df["precio_cop"].fillna(0) > 0] for df in dataframes_limpios]
        dataframes_limpios = [df for df in dataframes_limpios if not df.empty]
    else:
        df_master = pd.DataFrame()

    # Consolidar para vista previa
    if not df_master.empty:
        df_resumen_apis = pd.DataFrame(conteos_api)
        print("\n" + "="*50)
        print("📊 CANTIDAD DE INMUEBLES ENCONTRADOS POR API")
        print("="*50)
        print(df_resumen_apis.to_string(index=False))

        print("\n" + "="*50)
        print("📊 TABLA DE INMUEBLES CONSOLIDADOS (SILVER LAYER)")
        print("="*50)
        df_display = df_master.copy()
        df_display['precio_cop'] = df_display['precio_cop'].apply(lambda x: f"${x:,.0f}")
        df_display['precio_x_m2'] = df_display['precio_x_m2'].apply(lambda x: f"${x:,.0f}" if pd.notnull(x) else "N/A")

        print(df_display.head(10).to_string(index=False))
        print(f"\n[*] Total de inmuebles limpios listos para analítica: {len(df_master)}")
    else:
        print("[-] No se generaron datos limpios en la capa Silver.")

    return dataframes_limpios

def ejecutar_pruebas_cleaning():
    """Ejecuta la batería de pruebas estructurales de la capa Silver."""
    print("\n" + "="*50)
    print("EJECUTANDO PRUEBAS DE CALIDAD SILVER (CLEANING)")
    print("="*50)
    exit_code = pytest.main(["tests/test_cleaners.py", "-q"])
    if exit_code == 0:
        print("[✅] Pruebas de la capa Silver superadas con éxito.")
    else:
        print("[!] Las pruebas de calidad Silver FALLARON.")
    return exit_code


if __name__ == "__main__":
    # 1. Ejecutar Ingesta Bronze
    rutas_api, rutas_web = ejecutar_ingesta_bronze()
    
    # 2. Gate de Calidad 1: Auditoría de Ingesta (Bronze)
    exit_ingesta = ejecutar_pruebas_ingestion()
    if exit_ingesta != 0:
        raise SystemExit("Pipeline abortado por fallos de calidad en la capa Bronze.")
        
    # 3. Ejecutar Transformación a Silver
    dataframes_limpios = ejecutar_transformacion_silver(rutas_api, rutas_web)
    
    # 4. Gate de Calidad 2: Auditoría de Limpieza (Silver)
    if dataframes_limpios:
        exit_cleaning = ejecutar_pruebas_cleaning()
        if exit_cleaning != 0:
            raise SystemExit("Pipeline abortado por fallos estructurales en la capa Silver.")
        
    generar_mart_tendencias()