"""Importación de Excel: preview con errores por fila y confirmación idempotente.

Flujo (ARCHITECTURE.md, fase 2):

1. `leer_libro` — openpyxl, todas las hojas, valores JSON-safe (D-016).
2. `analizar_libro` — validación por fila y plan de importación (`PreviewImportacion`).
3. `aplicar_correcciones` — PATCH de celdas, con revalidación completa.
4. `confirmar_importacion` — upsert por clave natural en una transacción (D-009).

Ningún módulo de este paquete importa FastAPI. La aritmética de sobrecarga vive en
`app.validator.diagnostico` (regla 1 de AGENTS.md), no acá.
"""

from app.importer.analisis import analizar_libro, color_de_asignatura
from app.importer.confirmacion import confirmar_importacion
from app.importer.correcciones import Correccion, CorreccionInvalida, aplicar_correcciones
from app.importer.lectura import ArchivoInvalido, HojaCruda, leer_libro
from app.importer.modelos import ConfirmaImportacion, Hallazgo, PreviewImportacion
from app.importer.plantilla import MEDIA_TYPE_XLSX, NOMBRE_ARCHIVO, plantilla_bytes

__all__ = [
    "MEDIA_TYPE_XLSX",
    "NOMBRE_ARCHIVO",
    "ArchivoInvalido",
    "ConfirmaImportacion",
    "Correccion",
    "CorreccionInvalida",
    "Hallazgo",
    "HojaCruda",
    "PreviewImportacion",
    "analizar_libro",
    "aplicar_correcciones",
    "color_de_asignatura",
    "confirmar_importacion",
    "leer_libro",
    "plantilla_bytes",
]
