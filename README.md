# 🏢 Radar Inmobiliario - ETL Data Pipeline

> ⚠️ **PROJECT STATUS: MIGRATING FROM MVP (V1) TO ENTERPRISE ARCHITECTURE (V2)** ⚠️
> * **Current Codebase (V1):** The current repository contains the MVP (Minimum Viable Product). This iteration was built to validate extraction logic, bypass bot-protection blocks (WAF), and perform basic transformations.
> * **Active Development (V2):** Based on data quality bottlenecks identified in V1, the pipeline is actively being re-architected. V2 implements a robust Medallion Architecture orchestrated with **Dagster**, enforcing Zero-Trust data contracts via **Pydantic**, and modeling analytics with **dbt-DuckDB**.
> 
> 
> *The documentation below reflects the V2 Target Architecture currently under active deployment.*

## 📋 Descripción

Este proyecto es un pipeline de datos (ETL/ELT) automatizado y resiliente diseñado para extraer, limpiar y transformar datos no estructurados del sector inmobiliario. El objetivo principal es estructurar la información caótica de la web aplicando principios de desarrollo seguro e integridad de datos para habilitar el análisis de tendencias de mercado.

## ⚙️ Arquitectura de Datos (V2 Target Architecture)

El flujo de datos está diseñado bajo el modelo Medallion, priorizando la validación defensiva y la escalabilidad:

* **🥉 Capa Bronze (Raw):** Ingesta de datos crudos no estructurados (`.json` / `.html`) extraídos de fuentes web. Orquestado íntegramente a través de **Dagster**. Almacenamiento inmutable.
* **🥈 Capa Silver (Cleansed & Contracts):** Implementación de validación *Zero-Trust*. Uso de **Pydantic** y **dbt** para forzar esquemas estrictos, limpiar valores nulos y deduplicar registros. Los datos malformados son aislados en una capa de cuarentena antes de que puedan corromper la base de datos central.
* **🥇 Capa Gold (Semantic Marts):** Transformación analítica avanzada utilizando **dbt-DuckDB** y SQL. Generación de vistas semánticas, clasificación probabilística por rango de precios y agregaciones complejas (CTEs, non-equi joins).
* **📊 Serving Layer:** Consumo final de los modelos *Gold* a través de tableros interactivos construidos con **Streamlit**.

## 🛠️ Stack Tecnológico (V2)

* **Lenguaje:** Python 3.14, SQL
* **Orquestación:** Dagster
* **Data Quality & Contracts:** Pydantic
* **Transformación & Modelado:** dbt (data build tool)
* **Motor de Base de Datos:** DuckDB
* **Visualización:** Streamlit
* **Control de Versiones:** Git & GitHub

## 🚧 Roadmap y Estado de Migración

* [x] V1: Scripts de extracción y lógica defensiva inicial (`try-except`).
* [x] V1: Limpieza básica con Pandas y exportación a archivos planos.
* [x] V2: Diseño arquitectónico de flujos en Dagster.
* [ ] V2: Refactorización de limpieza hacia validadores estrictos de Pydantic.
* [ ] V2: Migración de transformaciones SQL nativas a modelos de dbt.
* [ ] V2: Integración final de DuckDB como motor analítico central.

## 💻 Configuración y Uso Local (MVP V1)

Para ejecutar la versión inicial de este pipeline localmente sin conflictos de dependencias, sigue este orden estricto:

### 1. Preparar el Entorno

Asegúrate de estar en la raíz del proyecto (`realestate_analytics/`) y crea un entorno virtual aislado:

**En Windows:**

```bash
python -m venv .venv
.venv\Scripts\activate

```

### 2. Instalación y Ejecución

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar el orquestador principal del MVP
python main.py

```

## 📂 Estructura del Proyecto

```text
realestate_analytics/
├── data/
│   ├── bronze/ (Archivos crudos .json / .html)
│   └── silver/ (Archivos Parquet estandarizados)
├── src/
│   ├── bronze/ (Extractores web y manejo de reintentos)
│   ├── silver/ (Lógica de sanitización y Pydantic models - En progreso)
│   ├── gold/   (Consultas SQL y modelos analíticos)
│   └── utils/  (Helpers compartidos)
├── tests/      (Test placeholders y mock data)
├── requirements.txt
└── main.py     (Orquestador central MVP)

```
