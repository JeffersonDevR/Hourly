"""Repositorio genérico: CRUD delgado sobre un agregado.

Sin reglas de negocio y sin `commit()`: la transacción la controla quien llama
(servicio o router). `flush()` sí, para que el `id` y las marcas de tiempo existan
antes de devolver la entidad.
"""

import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Session

from app.models.base import Base
from app.models.converters import a_dominio, a_modelo


class Repositorio[M: Base, D, K]:
    """`obtener`/`listar`/`agregar`/`actualizar`/`eliminar` para un modelo.

    `K` es el tipo de la clave: `uuid.UUID` normalmente, `str` para `tipo_recurso` y
    una tupla para las PK compuestas (`aptitud`, `conflicto_sesion`).
    """

    modelo: type[M]

    def __init__(self, sesion: Session) -> None:
        self.sesion = sesion

    def obtener(self, clave: K) -> D | None:
        fila = self.sesion.get(self.modelo, clave)
        return None if fila is None else a_dominio(fila)

    def listar(self) -> list[D]:
        filas = self.sesion.scalars(sa.select(self.modelo)).all()
        return [a_dominio(fila) for fila in filas]

    def agregar(self, entidad: D) -> D:
        fila = a_modelo(entidad)
        self.sesion.add(fila)
        self.sesion.flush()
        return a_dominio(fila)

    def actualizar(self, entidad: D) -> D:
        fila = self.sesion.merge(a_modelo(entidad))
        self.sesion.flush()
        return a_dominio(fila)

    def eliminar(self, clave: K) -> bool:
        fila = self.sesion.get(self.modelo, clave)
        if fila is None:
            return False
        self.sesion.delete(fila)
        self.sesion.flush()
        return True


class RepositorioCodigo[M: Base, D](Repositorio[M, D, uuid.UUID]):
    """Agregado identificado además por un `codigo` único (clave natural, D-009)."""

    def obtener_por_codigo(self, codigo: str) -> D | None:
        fila = self.sesion.scalars(
            sa.select(self.modelo).where(self.modelo.codigo == codigo)
        ).first()
        return None if fila is None else a_dominio(fila)
