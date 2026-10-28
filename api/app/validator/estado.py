"""Estado del horario como dataclasses: entrada común del validador.

`validar()` (fase 3) y `diagnosticar_carga()` (fase 2) reciben la misma foto del
horario. Este módulo no conoce SQLAlchemy ni FastAPI: quien llama hidrata las tuplas.

Los `id` de las entidades son los de la DB cuando el estado viene de los repositorios.
Cuando el estado se arma en memoria (importación, tests) basta con que sean coherentes
entre sí: el validador solo compara identificadores.
"""

from dataclasses import dataclass

from app.domain.carga import AsignacionCarga, DisponibilidadBloqueo
from app.domain.catalogo import Aptitud, Asignatura, Bloque, Curso, Docente
from app.domain.horario import EscenarioCambio, Sesion
from app.domain.recursos import Recurso


@dataclass(frozen=True, slots=True)
class EstadoHorario:
    """Foto completa del horario.

    Todos los campos tienen default vacío para que un estado parcial (solo la carga,
    sin sesiones) siga siendo válido: `diagnosticar_carga` corre antes de generar.
    """

    cursos: tuple[Curso, ...] = ()
    docentes: tuple[Docente, ...] = ()
    bloques: tuple[Bloque, ...] = ()
    asignaturas: tuple[Asignatura, ...] = ()
    aptitudes: tuple[Aptitud, ...] = ()
    asignaciones: tuple[AsignacionCarga, ...] = ()
    bloqueos: tuple[DisponibilidadBloqueo, ...] = ()
    recursos: tuple[Recurso, ...] = ()
    escenario_cambios: tuple[EscenarioCambio, ...] = ()
    sesiones: tuple[Sesion, ...] = ()
