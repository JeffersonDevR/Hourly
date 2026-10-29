"""Parser determinista de reglas (D-004).

El camino crítico del pitch no depende de la IA: las frases del guion son pocas y
repetitivas. Este parser cubre las formas del contrato y, si no matchea, el llamador
delega en el proveedor. Nunca inventa una regla: devuelve `None`.
"""

from __future__ import annotations

import re
import unicodedata

from app.ai.base import ReglaEstructurada

DIAS = {
    "lunes": 1,
    "martes": 2,
    "miercoles": 3,
    "jueves": 4,
    "viernes": 5,
}

#: Formas que significan "no puede". Ganan sobre las de liberar: "no disponible" contiene
#: "disponible" y sin este orden el parser invierte la regla.
RESTRINGEN = (
    "no puede",
    "no podra",
    "no esta disponible",
    "no disponible",
    "sin clase",
    "bloquea",
    "bloquear",
)
LIBERAN = ("libre", "libera", "liberar", "disponible")

DOCENTE = re.compile(r"\bD(\d{1,3})\b", re.IGNORECASE)
BLOQUE = re.compile(r"\bB(\d{1,2})\b", re.IGNORECASE)


def _normalizar(texto: str) -> str:
    sin_acentos = "".join(
        letra
        for letra in unicodedata.normalize("NFD", texto.lower())
        if unicodedata.category(letra) != "Mn"
    )
    return re.sub(r"\s+", " ", sin_acentos).strip()


def interpretar_determinista(texto: str) -> ReglaEstructurada | None:
    """`D2 sin clase el martes` → `ReglaEstructurada`. `None` si ningún patrón matchea."""
    normalizado = _normalizar(texto)

    docente = DOCENTE.search(texto)
    dias = tuple(
        sorted(
            numero
            for nombre, numero in DIAS.items()
            if re.search(rf"\b{nombre}\b", normalizado)
        )
    )
    if docente is None or not dias:
        return None

    bloque = BLOQUE.search(texto)
    bloquea = True
    if any(forma in normalizado for forma in LIBERAN):
        bloquea = False
    if any(forma in normalizado for forma in RESTRINGEN):
        bloquea = True

    return ReglaEstructurada(
        docente_codigo=f"D{int(docente.group(1))}",
        dias=dias,
        bloque_codigo=f"B{int(bloque.group(1))}" if bloque else None,
        bloquea=bloquea,
    )
