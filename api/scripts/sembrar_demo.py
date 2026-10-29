"""Deja el estado del pitch pre-cargado y repetible (D-007).

No levanta servidores: `demo.ps1` lo llama antes de arrancar la API y la web.

    uv run --directory api python scripts/sembrar_demo.py --reset
    uv run --directory api python scripts/sembrar_demo.py --vacio

`--reset` borra el archivo SQLite, migra y siembra el estado del pitch.
`--vacio` borra y migra pero **no** siembra: la base queda con las 23 tablas vacías, lista
para importar otro Excel desde la UI. Sin ninguno de los dos, exige una base vacía.

Qué deja (y por qué):

- Excel importado: cursos, docentes, carga, salones, aptitudes y el escenario "¿y si…?".
- Una versión en borrador con las 120 sesiones generadas con docentes habilitados.
- **2 sesiones sin colocar** de un curso: el semáforo queda ámbar (`MALLA_INCUMPLIDA` como
  advertencia) y el panel "Por colocar" tiene trabajo real para arrastrar en vivo.
- Cero errores: el horario es publicable.

El "ejemplo de regla en lenguaje natural" **no** se persiste: `/reglas` no lista reglas
existentes, así que sembrarlo sería invisible. Se muestra en vivo escribiendo la frase (el
parser determinista contesta sin red).
"""

from __future__ import annotations

import subprocess
import sys
from collections import Counter
from pathlib import Path

API_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(API_DIR))

from app.config import get_settings  # noqa: E402
from app.db import get_session_factory  # noqa: E402
from app.domain.enums import EstadoVersion  # noqa: E402
from app.domain.horario import HorarioVersion  # noqa: E402
from app.importer.analisis import analizar_libro  # noqa: E402
from app.importer.confirmacion import confirmar_importacion  # noqa: E402
from app.importer.lectura import leer_libro  # noqa: E402
from app.repositories.horario import (  # noqa: E402
    RepositorioHorarioVersion,
    RepositorioSesion,
)
from app.services import horario as servicio  # noqa: E402
from app.solver import resolver  # noqa: E402

DATOS = API_DIR.parent / "data" / "Datos_prueba_Gnosoft.xlsx"
SIN_COLOCAR = 2


def resetear() -> None:
    url = get_settings().database_url
    if not url.startswith("sqlite"):
        raise SystemExit(f"El reset de la demo solo soporta SQLite, no {url}.")
    ruta = Path(url.removeprefix("sqlite:///"))
    for sufijo in ("", "-wal", "-shm"):
        ruta.with_name(ruta.name + sufijo).unlink(missing_ok=True)
    subprocess.run(["alembic", "upgrade", "head"], check=True, cwd=API_DIR)


def sembrar() -> None:
    if not DATOS.exists():
        raise SystemExit(f"Falta el Excel de la demo: {DATOS}")

    fabrica = get_session_factory()
    with fabrica() as sesion:
        if RepositorioHorarioVersion(sesion).listar():
            raise SystemExit(
                "La base ya tiene versiones de horario. Corré con --reset para empezar de cero."
            )

        preview = analizar_libro(leer_libro(DATOS.read_bytes()), archivo_nombre=DATOS.name)
        confirmar_importacion(sesion, preview)

        version = RepositorioHorarioVersion(sesion).agregar(
            HorarioVersion(numero=1, estado=EstadoVersion.borrador, nota="estado del pitch")
        )
        sesion.commit()

        estado = servicio.cargar_estado(sesion, version)
        resultado = resolver(
            estado,
            "habilitados",
            None,
            None,
            None,
            False,
            None,
            horario_version_id=version.id,
        )
        if not resultado.sesiones:
            raise SystemExit(f"El solver no encontró plan: {resultado.diagnostico}")

        servicio.persistir_plan(sesion, version, resultado)
        servicio.guardar_conflictos(sesion, version)
        sesion.commit()

        # Dejar dos sesiones sin colocar: semáforo ámbar y panel "Por colocar" con trabajo.
        colocadas = RepositorioSesion(sesion).listar_por_version(version.id)
        curso = min(colocadas, key=lambda item: item.curso_id).curso_id
        del_curso = [item for item in colocadas if item.curso_id == curso]
        for item in del_curso[-SIN_COLOCAR:]:
            servicio.eliminar_sesion(sesion, version, item.id)
        servicio.guardar_conflictos(sesion, version)
        sesion.commit()

        conflictos = servicio.guardar_conflictos(sesion, version)
        sesion.commit()
        restantes = RepositorioSesion(sesion).listar_por_version(version.id)

    conteo = Counter(f"{item.codigo}/{item.gravedad}" for item in conflictos)
    print(f"Versión {version.numero} en {version.estado}: {len(restantes)} sesiones.")
    for clave, cantidad in sorted(conteo.items()):
        print(f"  {clave}: {cantidad}")
    if not conteo:
        print("  sin conflictos (inesperado: debería quedar la malla incompleta)")


def main() -> None:
    if "--vacio" in sys.argv:
        resetear()
        print("Base vacía y migrada. Importá tu Excel desde /importar.")
        return
    if "--reset" in sys.argv:
        resetear()
    sembrar()


if __name__ == "__main__":
    main()
