# 🏢 Radar Inmobiliario - ETL Data Pipeline

## Descripcion 
Este proyecto es un pipeline de datos (ETL) automatizado diseñado para extraer, limpiar y transformar datos no estructurados del sector inmobiliario. El objetivo principal es estructurar la información caótica de la web para habilitar el análisis de tendencias y métricas de mercado.


## ⚙️ Arquitectura de Datos (Medallion Architecture)

*   **🥉 Capa Bronze (Raw):** Ingesta de datos crudos (`.json` y `.html`) extraídos directamente de APIs REST (Panda Inmobiliaria, Nutibara) y renderizado SSR (Arrendamientos Santa Fe). Los datos se almacenan "as-is" particionados por fecha de ejecución.
*   **🥈 Capa Silver (Cleansed):** Procesamiento y normalización. Se aplica limpieza de caracteres, eliminación de PII (Información de Identificación Personal), y se fuerza un contrato de datos estricto mediante "listas blancas" de columnas. Los registros que no superan las validaciones de negocio (ej. precios irreales) son enviados a un sistema de **Cuarentena**. Los datos limpios se exportan en formato `.csv`.
*   **🥇 Capa Gold (Curated):** Transformación analítica y Data Marts. Se utiliza DuckDB para ejecutar consultas SQL avanzadas (CTEs, Window Functions) directamente sobre los archivos, deduplicando inmuebles entre fuentes y generando las métricas finales. Los resultados se guardan en `.parquet` para máxima velocidad de lectura en el dashboard.

## 🛠️ Stack Tecnológico

*   **Core:** Python 3.14
*   **Extracción (Bronze):** `requests`, `cloudscraper` (WAF Bypass & Politeness), `beautifulsoup4`
*   **Transformación (Silver):** `pandas`
*   **Modelado SQL (Gold):** `duckdb`, `pyarrow`
*   **Visualización:** `streamlit`

## Linaje de Datos:

Fuentes (API/SSR) ➔ Bronze Layer (JSON/HTML crudo).

Bronze Layer ➔ Transformación Pandas ➔ Silver Layer (Parquet particionado, PII removido).

Silver Layer ➔ DuckDB (SQL) ➔ Gold Layer (Marts analíticos agrupados por barrio).

## 📁 Estructura del Proyecto

```text
radar-inmobiliario/
├── data/                   # Almacenamiento local (Ignorado en Git)
│   ├── bronze/             # JSON y HTML particionado por fecha/hora
│   ├── silver/             # CSVs limpios y estandarizados
│   └── gold/               # Data Marts en formato Parquet
├── src/
│   ├── bronze/
│   │   ├── ingest_api.py   # Paginación y extracción de APIs REST
│   │   └── ingest_web.py   # Navegación y scraping de SSR
│   ├── silver/
│   │   ├── clean_api.py    # Filtros, limpieza y normalización de JSONs
│   │   └── clean_ssr.py    # Parseo de DOM (BS4) y extracción CSS
│   ├── gold/
│   │   ├── gold_orquestrator.py # Ejecución de validaciones y modelos
│   │   ├── base_sql.py     # Consultas SQL maestras y CTEs (DuckDB)
│   │   └── marts/          # Lógica modular de reportes específicos
│   ├── utils/
│   │   └── scraper_client.py # Cliente HTTP con manejo de reintentos y anti-bot
│   └── notifications/
│       └── telegram_bot.py # Módulo de alertas del pipeline
├── tests/                  # Pruebas de calidad de datos
├── main.py                 # Orquestador principal y menú interactivo
├── Dashboard_web.py        # Interfaz analítica (Streamlit)
├── requirements.txt        # Dependencias del proyecto
└── README.md
```

## 🚧 Estado del Proyecto 
Este proyecto se encuentra en desarrollo activo e iteración continua:
- [x] Desarrollo de scripts de extracción y lógica defensiva (`try-except`).
- [ ] Migración de la orquestación local a DAGs de **Apache Airflow**.
- [ ] Integración de almacenamiento distribuido mediante **AWS**.
- [ ] Test y limpieza para métricas con mínimo sesgo.


## Configuración y Uso Local

Para ejecutar este pipeline localmente sin conflictos de dependencias (especialmente con los motores de compresión de datos), sigue este orden estricto:

### 1. Preparar el Entorno - Instalar uv
Desde python:
pip install uv
Tambien puedes ir a powershell en Windows e instalar uv en tu computador:

```
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```
Asegúrate de que este bien instalando probando el comando 'uv' en tu ide.
Clona el repositorio, y acciona
```
uv pip install -r requirements.txt
```
se descargaran los requisitos y podras usar el entorno virtual en tu pc, ahora solo acciones main.py!
