# Exponemos el orquestador de Gold para que el main.py de la raíz lo llame directo
from .gold_orquestrator import generar_mart_tendencias

__all__ = ["generar_mart_tendencias"]