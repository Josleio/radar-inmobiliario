# 🏢 Radar Inmobiliario - ETL Data Pipeline

## Descripcion 
Este proyecto es un pipeline de datos (ETL) automatizado diseñado para extraer, limpiar y transformar datos no estructurados del sector inmobiliario. El objetivo principal es estructurar la información caótica de la web para habilitar el análisis de tendencias y métricas de mercado mediante una arquitectura robusta.

## ⚙️ Arquitectura de Datos
El flujo de datos está diseñado bajo el modelo Medallion para garantizar la calidad e integridad:
*   **🥉 Capa Bronze (Raw):** Ingesta de datos crudos no estructurados extraídos de fuentes web mediante scripts en Python.
*   **🥈 Capa Silver (Cleansed):** Limpieza, manejo de valores nulos (excepciones) y estandarización de formatos utilizando APIs de LLM para forzar esquemas JSON estrictos.
*   **🥇 Capa Gold (Curated):** Inyección de los datos modelados en una base de datos relacional (SQL) listos para el consumo de dashboards analíticos.

## 🛠️ Stack Tecnológico
*   **Lenguajes:** Python 3.14, SQL
*   **Orquestación:** Apache Airflow (En migración)
*   **Infraestructura & Cloud:** AWS (S3 / RDS - En despliegue)
*   **Procesamiento:** Extracción basada en IA (JSON strict formatting)

## 🚧 Estado del Proyecto 
Este proyecto se encuentra en desarrollo activo e iteración continua:
- [x] Desarrollo de scripts de extracción y lógica defensiva (`try-except`).
- [x] Implementación de IA para estructuración de datos.
- [ ] Refactorización modular para ejecución en clúster.
- [ ] Migración de la orquestación local a DAGs de **Apache Airflow**.
- [ ] Integración de almacenamiento distribuido mediante **AWS**.

## Configuración y Uso Local

Para ejecutar este pipeline localmente sin conflictos de dependencias (especialmente con los motores de compresión de datos), sigue este orden estricto:

### 1. Preparar el Entorno
Asegúrate de estar en la raíz del proyecto (`realestate_analytics/`) y crea un entorno virtual aislado para no contaminar las librerías globales de tu sistema:

**En Windows:**
```bash

python -m venv .venv
.venv\Scripts\activate

```
1. Clonar el repositorio.
2. Instalar dependencias: `pip install -r requirements.txt`
3. Ejecutar el orquestador principal: `python main.py`
   
## 🏗️ Arquitectura del Proyecto

El flujo de datos está estructurado en tres capas lógicas para garantizar resiliencia ante fallos de red y consistencia en el modelado de datos:

*   **Bronze (Datos Crudos):** Almacenamiento inmutable de la ingesta diaria.
*   **Silver (Datos Limpios):** Estandarización relacional y sanitización de seguridad.
*   **Gold (Analítica):** Modelos dimensionales y agregaciones (Pendiente de implementación).

## Structure

- `src/utils`: shared helpers
- `src/bronze`: raw ingestion layer
- `src/silver`: cleaning layer
- `src/gold`: database and modeling layer
- `src/notifications`: alerting layer
- `tests`: test placeholders and mock data


```text
realestate_analytics/
├── data/
│   ├── bronze/ (JSON/HTML crudos por fecha)
│   └── silver/ (Archivos Parquet limpios)
├── src/
│   ├── bronze/ (Extractores REST y SSR)
│   ├── silver/ (Filtros de Data Contract y eliminación PII)
│   └── utils/  (Clientes HTTP HTTP y manejo de reintentos)
└── main.py     (Orquestador central)
