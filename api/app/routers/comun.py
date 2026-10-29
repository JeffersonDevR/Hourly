"""Piezas compartidas de los routers.

El cuerpo de error de la API es `{codigo, mensaje}` en el nivel superior: `main.py`
aplana el `detail` de `HTTPException`. Estos dos helpers evitan que cada router
invente su propio formato.
"""

from typing import NoReturn

from fastapi import HTTPException


def error(estado: int, codigo: str, mensaje: str) -> NoReturn:
    raise HTTPException(status_code=estado, detail={"codigo": codigo, "mensaje": mensaje})


def no_encontrado(entidad: str) -> NoReturn:
    error(404, "NO_ENCONTRADO", f"{entidad} no encontrado.")
