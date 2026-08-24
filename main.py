import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest

from src.bronze import run_api_extractors, run_web_scrapers
from src.gold import generar_mart_tendencias
from src.silver import limpiar_anutibara_api, limpiar_panda_api, limpiar_santafe_ssr


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
    conteos_web = []

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
        cantidad_santafe = 0 if df_santafe is None else len(df_santafe)
        conteos_web.append({"fuente": "Santa Fe", "cantidad_inmuebles": cantidad_santafe})
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

        print("📊 CANTIDAD DE INMUEBLES ENCONTRADOS SSR")
        df_resumen_web = pd.DataFrame(conteos_web)
        print(df_resumen_web.to_string(index=False))

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


def obtener_rutas_bronze_recientes():
    """
    Escanea la carpeta Bronze de hoy de forma recursiva para recuperar las rutas de los 
    archivos crudos más recientes. Soporta anidamiento en subcarpetas (APIs, SSRs, etc).
    """
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    ruta_bronze = Path(f"data/bronze/{fecha_hoy}")
    
    api_rutas = {}
    web_rutas = {}
    
    if not ruta_bronze.exists():
        print(f"[-] No se encontró la carpeta Bronze para hoy: {ruta_bronze}")
        return api_rutas, web_rutas
        
    # Usar rglob para buscar en todas las subcarpetas y ordenar por la más reciente
    archivos = list(ruta_bronze.rglob("*.*"))
    archivos.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
    for archivo in archivos:
        if not archivo.is_file():
            continue
            
        nombre = archivo.name.lower()
        # Solo tomamos el primero que aparezca (el más reciente) para cada fuente
        if "panda" in nombre and "panda" not in api_rutas:
            api_rutas["panda"] = str(archivo)
        elif "anutibara" in nombre and "anutibara" not in api_rutas:
            api_rutas["anutibara"] = str(archivo)
        elif "santafe" in nombre and "santafe" not in web_rutas:
            web_rutas["santafe"] = str(archivo)
            
    return api_rutas, web_rutas


def menu_principal():
    """Interfaz interactiva por consola para ejecutar módulos aislados."""
    while True:
        print("\n" + "="*50)
        print("PANEL DE CONTROL - RADAR INMOBILIARIO")
        print("="*50)
        print("1. Ejecutar Pipeline Completo y abrir Dashboards")
        print("2. Extraccion e ingesta de Datos (Bronze)")
        print("3. Transformación y Limpieza de Datos(Silver)")
        print("4. Cargar Datos a Mart de Tendencias (Gold)")
        print("5. Abrir Dashboards")
        print("0. Salir")
        
        opcion = input("\nSelecciona una opción (0-5): ").strip()
        
        if opcion == '0':
            print("Saliendo del Radar Inmobiliario...")
            break
            
        elif opcion == '1':
            rutas_api, rutas_web = ejecutar_ingesta_bronze()
            if ejecutar_pruebas_ingestion() == 0:
                dataframes = ejecutar_transformacion_silver(rutas_api, rutas_web)
                if dataframes and ejecutar_pruebas_cleaning() == 0:
                    generar_mart_tendencias()
            print("\n✅ Pipeline completo finalizado.")
            
        elif opcion == '2':
            ejecutar_ingesta_bronze()
            ejecutar_pruebas_ingestion()
            print("\n✅ Extracción Bronze finalizada.")
            
        elif opcion == '3':
            # Intentamos recuperar los archivos de Bronze de hoy
            rutas_api, rutas_web = obtener_rutas_bronze_recientes()
            if not rutas_api and not rutas_web:
                print("\n[!] No hay datos crudos para hoy. Por favor, ejecuta Bronze primero (Opción 2).")
            else:
                dataframes = ejecutar_transformacion_silver(rutas_api, rutas_web)
                if dataframes:
                    ejecutar_pruebas_cleaning()
                print("\n✅ Transformación Silver finalizada.")
                
        elif opcion == '4':
            generar_mart_tendencias()
            print("\n✅ Capa Gold finalizada.")
            
        elif opcion == '5':
            print("\n[1] Abrir Dashboard Web (Streamlit - Automático)")
            print("[2] Abrir Archivo de Power BI (Requiere tener un .pbix)")
            sub_op = input("Elige (1-2): ").strip()
            
            if sub_op == '1':
                print("Iniciando servidor web...")

                archivo_dashboard = "Dashboard_web.py" 
                
                if os.path.exists(archivo_dashboard):
                    try:
                        subprocess.Popen([
                            sys.executable, "-m", "streamlit", "run", archivo_dashboard,
                            "--browser.gatherUsageStats=false"
                        ])
                    except Exception as e:
                        print(f"[-] Ocurrió un error al lanzar Streamlit: {e}")
                else:
                    print(f"[-] ERROR: No se encontró el archivo '{archivo_dashboard}' en la raíz del proyecto.")
                    
            elif sub_op == '2':
                # Reemplaza 'dashboard.pbix' con la ruta real de tu archivo de Power BI
                ruta_pbi = os.path.abspath("dashboard.pbix")
                if os.path.exists(ruta_pbi):
                    print("Abriendo Power BI...")
                    os.startfile(ruta_pbi)
                else:
                    print("[-] No se encontró el archivo 'dashboard.pbix' en esta carpeta.")
            
        else:
            print("[-] Opción inválida. Intenta nuevamente.")
            

if __name__ == "__main__":

    menu_principal()