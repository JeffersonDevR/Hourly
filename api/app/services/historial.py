"""Historial de cambios: el único escritor de `historial_cambio`.

Regla 3 de `AGENTS.md`: nada se aplica sin confirmación y todo cambio va al historial
para poder deshacer. Centralizarlo acá evita que cada router invente su formato de
`antes`/`despues` y que alguna mutación quede sin traza.

No hace `commit()`: la entrada se escribe en la misma transacción que el cambio, así
que o quedan los dos o no queda ninguno.
"""

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.domain.procesos import HistorialCambio
from app.models.converters import a_dominio
from app.models.historial import HistorialCambioDB


def registrar_cambio(
    sesion: Session,
    *,
    entidad: str,
    entidad_id: uuid.UUID | str,
    accion: str,
    antes: dict[str, Any] | None = None,
    despues: dict[str, Any] | None = None,
    horario_version_id: uuid.UUID | None = None,
) -> HistorialCambio:
    """Agrega una entrada al historial y la devuelve como entidad de dominio.

    Args:
        entidad: tabla o agregado afectado ('sesion', 'docente', ...).
        entidad_id: PK de la fila; UUID o código (`tipo_recurso` usa strings).
        accion: verbo en español ('crear', 'mover', 'eliminar', ...).
        antes/despues: estado serializable antes y después del cambio. `crear` no tiene
            `antes`; `eliminar` no tiene `despues`.
        horario_version_id: versión a la que pertenece el cambio, si aplica.
    """
    fila = HistorialCambioDB(
        entidad=entidad,
        entidad_id=str(entidad_id),
        accion=accion,
        antes=antes,
        despues=despues,
        horario_version_id=horario_version_id,
    )
    sesion.add(fila)
    sesion.flush()
    return a_dominio(fila)
