"""Golden de la fase 2 con el archivo real, más archivo sucio y doble importación.

Los conteos y la aritmética están verificados contra `data/Datos_prueba_Gnosoft.xlsx`
(no contra el `DOMAIN.md`): 40 filas de Carga, 120 sesiones, demanda D4 = 28 > 24.
El archivo no se modifica: se lee como bytes.
"""

from pathlib import Path

import sqlalchemy as sa
from sqlalchemy.orm import Session

from app.importer.analisis import analizar_libro
from app.importer.coercion import minutos
from app.importer.confirmacion import confirmar_importacion
from app.importer.lectura import buscar_hoja, leer_libro
from app.importer.modelos import PreviewImportacion
from app.models.carga import AsignacionCargaDB, DisponibilidadBloqueoDB
from app.models.catalogo import (
    AptitudDB,
    AsignaturaDB,
    BloqueDB,
    CursoDB,
    DocenteDB,
    GradoDB,
)
from app.models.horario import EscenarioCambioDB, EscenarioDB
from app.models.recursos import RecursoDB, TipoRecursoDB
from app.repositories.carga import RepositorioAsignacionCarga, RepositorioDisponibilidad
from app.repositories.catalogo import RepositorioBloque, RepositorioCurso, RepositorioDocente
from app.repositories.horario import RepositorioEscenario, RepositorioEscenarioCambio
from tests.xlsxutil import libro_minimo

DATOS = Path(__file__).resolve().parents[2] / "data" / "Datos_prueba_Gnosoft.xlsx"

#: Tablas que escribe la confirmación, en el orden de FK.
TABLAS: tuple[type, ...] = (
    GradoDB,
    CursoDB,
    BloqueDB,
    AsignaturaDB,
    DocenteDB,
    AptitudDB,
    TipoRecursoDB,
    RecursoDB,
    AsignacionCargaDB,
    DisponibilidadBloqueoDB,
    EscenarioDB,
    EscenarioCambioDB,
)

CONTEOS_REALES: dict[str, int] = {
    "leeme": 13,
    "bloques": 6,
    "cursos": 4,
    "grados": 2,
    "docentes": 6,
    "asignaturas": 10,
    "aptitudes": 11,
    "asignaciones": 40,
    "tipos_recurso": 4,
    "recursos": 16,
    "disponibilidad": 180,
    "bloqueos": 1,
    "escenarios": 1,
    "escenario_cambios": 6,
}


def _analizar(contenido: bytes, nombre: str = "libro.xlsx") -> PreviewImportacion:
    return analizar_libro(leer_libro(contenido), archivo_nombre=nombre)


def _real() -> PreviewImportacion:
    return _analizar(DATOS.read_bytes(), DATOS.name)


def _contar(sesion: Session, modelo: type) -> int:
    return sesion.scalar(sa.select(sa.func.count()).select_from(modelo)) or 0


def _conteos(sesion: Session) -> dict[str, int]:
    return {modelo.__tablename__: _contar(sesion, modelo) for modelo in TABLAS}


def test_golden_1_conteos_del_archivo_real() -> None:
    preview = _real()

    assert preview.conteos == CONTEOS_REALES


def test_golden_1_bloques_derivados() -> None:
    """`Bloques` no trae `tipo` ni `duracion_min`: se derivan (DOMAIN.md trampa 3)."""
    preview = _real()

    assert [bloque.codigo for bloque in preview.bloques] == ["B1", "B2", "B3", "B4", "B5", "B6"]
    assert [minutos(bloque.inicio) for bloque in preview.bloques] == [
        420,
        480,
        540,
        600,
        660,
        720,
    ]
    assert [bloque.orden for bloque in preview.bloques] == [1, 2, 3, 4, 5, 6]
    assert {bloque.duracion_min for bloque in preview.bloques} == {60}
    assert {str(bloque.tipo) for bloque in preview.bloques} == {"clase"}
    assert str(preview.bloques[-1].fin) == "13:00:00"


def test_golden_1_cursos_grados_y_docentes() -> None:
    preview = _real()

    assert [(curso.codigo, curso.grado, curso.estudiantes) for curso in preview.cursos] == [
        ("7A", 7, 30),
        ("7B", 7, 28),
        ("6A", 6, 30),
        ("6B", 6, 28),
    ]
    assert preview.grados == (6, 7)
    assert [docente.codigo for docente in preview.docentes] == [
        "D1",
        "D2",
        "D3",
        "D4",
        "D5",
        "D6",
    ]
    assert {docente.max_sesiones_semana for docente in preview.docentes} == {24}


def test_golden_1_asignaturas_aptitudes_y_colores() -> None:
    preview = _real()

    nombres = [asignatura.nombre for asignatura in preview.asignaturas]
    assert len(nombres) == 10
    assert len(set(nombres)) == 10
    # Inglés la dictan D4 y D6: 11 aptitudes para 10 asignaturas.
    assert len(preview.aptitudes) == 11
    assert {("Inglés", "D4"), ("Inglés", "D6")} <= {
        (aptitud.asignatura, aptitud.docente) for aptitud in preview.aptitudes
    }
    # Paleta determinista: dos análisis del mismo archivo dan los mismos colores.
    colores = {asignatura.nombre: asignatura.color for asignatura in preview.asignaturas}
    otra_vez = {asignatura.nombre: asignatura.color for asignatura in _real().asignaturas}
    assert colores == otra_vez
    assert len(set(colores.values())) == 10


def test_golden_1_carga_y_demanda_por_docente() -> None:
    preview = _real()

    assert len(preview.asignaciones) == 40
    por_curso: dict[str, int] = {}
    for asignacion in preview.asignaciones:
        actual = por_curso.get(asignacion.curso, 0)
        por_curso[asignacion.curso] = actual + asignacion.sesiones_semana
    assert por_curso == {"7A": 30, "7B": 30, "6A": 30, "6B": 30}
    assert sum(por_curso.values()) == 120

    demanda: dict[str, int] = {}
    for asignacion in preview.asignaciones:
        demanda[asignacion.docente_principal] = (
            demanda.get(asignacion.docente_principal, 0) + asignacion.sesiones_semana
        )
    assert dict(sorted(demanda.items())) == {
        "D1": 24,
        "D2": 16,
        "D3": 24,
        "D4": 28,
        "D5": 16,
        "D6": 12,
    }


def test_golden_1_salones() -> None:
    preview = _real()

    assert set(preview.tipos_recurso) == {
        "GENERAL",
        "LAB_CIENCIAS",
        "CANCHA",
        "SALA_INFORMATICA",
    }
    assert len(preview.recursos) == 16
    por_tipo: dict[str, int] = {}
    for recurso in preview.recursos:
        por_tipo[recurso.tipo_recurso] = por_tipo.get(recurso.tipo_recurso, 0) + 1
    assert por_tipo == {
        "GENERAL": 4,
        "LAB_CIENCIAS": 4,
        "CANCHA": 4,
        "SALA_INFORMATICA": 4,
    }
    assert min(recurso.capacidad for recurso in preview.recursos) == 30
    titulares = {
        recurso.curso_titular for recurso in preview.recursos if recurso.curso_titular is not None
    }
    assert titulares == {"7A", "7B", "6A", "6B"}


def test_golden_1_disponibilidad_y_escenario() -> None:
    preview = _real()

    assert len(preview.bloqueos) == 1
    bloqueo = preview.bloqueos[0]
    assert (bloqueo.docente, bloqueo.dia, bloqueo.bloque) == ("D1", 5, "B6")
    assert preview.escenario is not None
    assert preview.escenario.nombre == "D2 sin clase el martes"
    assert len(preview.escenario.cambios) == 6
    assert {cambio.docente for cambio in preview.escenario.cambios} == {"D2"}
    assert {cambio.dia for cambio in preview.escenario.cambios} == {2}
    assert {cambio.bloque for cambio in preview.escenario.cambios} == {
        "B1",
        "B2",
        "B3",
        "B4",
        "B5",
        "B6",
    }
    assert all(cambio.disponible_nuevo is False for cambio in preview.escenario.cambios)


def test_golden_1_hallazgos() -> None:
    """DURACION_BLOQUE_INCONSISTENTE, SIN_DESCANSOS y DOCENTE_SOBRECARGA (D4 28/24)."""
    preview = _real()
    codigos = [hallazgo.codigo for hallazgo in preview.hallazgos]

    assert "DURACION_BLOQUE_INCONSISTENTE" in codigos
    assert codigos.count("DURACION_BLOQUE_INCONSISTENTE") == 1
    assert "SIN_DESCANSOS" in codigos
    assert "FILAS_VACIAS_IGNORADAS" in codigos
    assert "DUPLICADO" not in codigos
    assert "CURSO_NO_RECONOCIDO" not in codigos
    assert "DOCENTE_NO_RECONOCIDO" not in codigos
    assert "APTITUD_FALTANTE" not in codigos

    sobrecargas = [h for h in preview.hallazgos if h.codigo == "DOCENTE_SOBRECARGA"]
    assert len(sobrecargas) == 1
    sobrecarga = sobrecargas[0]
    assert (sobrecarga.hoja, sobrecarga.columna) == ("Carga", "docente_principal_id")
    assert "D4" in sobrecarga.mensaje
    assert "28" in sobrecarga.mensaje
    assert "24" in sobrecarga.mensaje
    # Es un error de datos, pero no bloquea la escritura de la fila.
    assert sobrecarga.severidad == "error"
    assert sobrecarga.bloqueante is False

    # El único error del archivo real es la sobrecarga: nada más impide importar.
    assert [hallazgo.codigo for hallazgo in preview.errores] == ["DOCENTE_SOBRECARGA"]


def test_golden_1_confirmar_escribe_todo(sesion_db: Session) -> None:
    preview = _real()

    escritura = confirmar_importacion(sesion_db, preview)

    assert _conteos(sesion_db) == {
        "grado": 2,
        "curso": 4,
        "bloque": 6,
        "asignatura": 10,
        "docente": 6,
        "aptitud": 11,
        "tipo_recurso": 4,
        "recurso": 16,
        "asignacion_carga": 40,
        "disponibilidad_bloqueo": 1,
        "escenario": 1,
        "escenario_cambio": 6,
    }
    assert escritura.creados == dict(_conteos(sesion_db))
    assert escritura.actualizados == {}

    # Los conteos de la DB coinciden con los del preview, campo por campo.
    assert preview.conteos["cursos"] == _contar(sesion_db, CursoDB)
    assert preview.conteos["aptitudes"] == _contar(sesion_db, AptitudDB)
    assert preview.conteos["asignaciones"] == _contar(sesion_db, AsignacionCargaDB)
    assert preview.conteos["recursos"] == _contar(sesion_db, RecursoDB)
    assert preview.conteos["bloqueos"] == _contar(sesion_db, DisponibilidadBloqueoDB)

    bloques = {bloque.codigo: bloque for bloque in RepositorioBloque(sesion_db).listar()}
    assert bloques["B1"].duracion_min == 60
    assert str(bloques["B1"].tipo) == "clase"
    assert str(bloques["B6"].inicio) == "12:00:00"

    cursos = {curso.codigo: curso for curso in RepositorioCurso(sesion_db).listar()}
    grados = {grado.id: grado.orden for grado in sesion_db.scalars(sa.select(GradoDB))}
    assert grados[cursos["7A"].grado_id] == 7
    assert grados[cursos["6B"].grado_id] == 6

    docentes = {docente.codigo: docente for docente in RepositorioDocente(sesion_db).listar()}
    assert docentes["D4"].max_sesiones_semana == 24

    sumas: dict[str, int] = {}
    for asignacion in RepositorioAsignacionCarga(sesion_db).listar():
        codigo = next(c for c, curso in cursos.items() if curso.id == asignacion.curso_id)
        sumas[codigo] = sumas.get(codigo, 0) + asignacion.sesiones_semana
    assert sumas == {"7A": 30, "7B": 30, "6A": 30, "6B": 30}

    bloqueos = RepositorioDisponibilidad(sesion_db).listar()
    assert len(bloqueos) == 1
    assert bloqueos[0].dia == 5
    assert bloqueos[0].origen == "personal"

    escenario = RepositorioEscenario(sesion_db).listar()[0]
    assert escenario.nombre == "D2 sin clase el martes"
    assert len(RepositorioEscenarioCambio(sesion_db).listar_por_escenario(escenario.id)) == 6


def test_booleanos_float_importan_aptitudes_y_bloqueos(sesion_db: Session) -> None:
    """El test que falla si alguien compara `habilitado` contra la cadena "1"."""
    contenido = libro_minimo()

    # El fixture tiene que reproducir el XML del archivo real: `1.0`, no `1`.
    hojas = leer_libro(contenido)
    aptitudes_hoja = buscar_hoja(hojas, "Asignaturas docentes")
    disponibilidad_hoja = buscar_hoja(hojas, "Disponibilidad")
    assert aptitudes_hoja is not None
    assert disponibilidad_hoja is not None
    habilitado = aptitudes_hoja.valor(aptitudes_hoja.filas[0], "habilitado")
    disponible = disponibilidad_hoja.valor(disponibilidad_hoja.filas[0], "disponible")
    assert isinstance(habilitado, float) and habilitado == 1.0
    assert isinstance(disponible, float) and disponible == 1.0

    preview = _analizar(contenido)
    assert preview.conteos["aptitudes"] == 11
    assert preview.conteos["bloqueos"] == 1

    confirmar_importacion(sesion_db, preview)
    assert _contar(sesion_db, AptitudDB) == 11
    assert _contar(sesion_db, DisponibilidadBloqueoDB) == 1

    bloqueo = RepositorioDisponibilidad(sesion_db).listar()[0]
    assert bloqueo.dia == 5  # Viernes
    assert bloqueo.bloque_id == next(
        bloque.id
        for bloque in RepositorioBloque(sesion_db).listar()
        if bloque.codigo == "B6"
    )


def test_booleanos_texto_tambien_importan(sesion_db: Session) -> None:
    """Control: '1.0'/'0.0' como texto se leen igual (el archivo real trae floats)."""
    preview = _analizar(libro_minimo(forzar_floats=False))

    assert preview.conteos["aptitudes"] == 11
    assert preview.conteos["bloqueos"] == 1


def test_reimportar_el_mismo_archivo_no_duplica_ni_falla(sesion_db: Session) -> None:
    """D-009: upsert por clave natural, no INSERT a ciegas."""
    confirmar_importacion(sesion_db, _real())
    sesion_db.commit()
    primera = _conteos(sesion_db)

    escritura = confirmar_importacion(sesion_db, _real())
    sesion_db.commit()

    assert escritura.creados == {}
    # Aptitudes y tipos de recurso son solo INSERT: no tienen nada que actualizar.
    assert set(escritura.actualizados) == set(primera) - {"aptitud", "tipo_recurso"}
    assert _conteos(sesion_db) == primera


def test_libro_sucio_reporta_y_confirma_solo_lo_valido(sesion_db: Session) -> None:
    preview = _analizar(libro_minimo(duplicar_curso=True, curso_malo=True))
    codigos = [hallazgo.codigo for hallazgo in preview.hallazgos]

    assert "DUPLICADO" in codigos
    assert "CURSO_NO_RECONOCIDO" in codigos

    duplicado = next(h for h in preview.hallazgos if h.codigo == "DUPLICADO")
    assert (duplicado.hoja, duplicado.fila, duplicado.columna) == ("Cursos", 6, "curso_id")
    assert duplicado.bloqueante is True

    desconocido = next(h for h in preview.hallazgos if h.codigo == "CURSO_NO_RECONOCIDO")
    assert (desconocido.hoja, desconocido.fila, desconocido.columna) == (
        "Carga",
        2,
        "curso_id",
    )

    # La fila duplicada no crea un quinto curso; la carga huérfana no crea una asignación.
    assert preview.conteos["cursos"] == 4
    assert preview.conteos["asignaciones"] == 9
    assert preview.confirmable is True

    confirmar_importacion(sesion_db, preview)

    assert _contar(sesion_db, CursoDB) == 4
    assert {curso.codigo for curso in RepositorioCurso(sesion_db).listar()} == {
        "7A",
        "7B",
        "6A",
        "6B",
    }
    assert _contar(sesion_db, AsignacionCargaDB) == 9
    assert _contar(sesion_db, AptitudDB) == 11


def test_hoja_faltante_es_error_y_no_revienta() -> None:
    """Sin `Salones` el tipo de recurso de la carga queda irresoluble: se reporta."""
    preview = _analizar(libro_minimo(sin_hoja="Salones"))

    faltantes = [h for h in preview.hallazgos if h.codigo == "HOJA_FALTANTE"]
    assert len(faltantes) == 1
    assert faltantes[0].hoja == "Salones"
    assert faltantes[0].bloqueante is True
    assert "TIPO_RECURSO_NO_RECONOCIDO" in {h.codigo for h in preview.hallazgos}
    # Sin tipos de salón no se puede escribir ninguna asignación de carga.
    assert preview.conteos["asignaciones"] == 0
    # Lo que sí se pudo leer sigue siendo importable.
    assert preview.conteos["cursos"] == 4
    assert preview.confirmable is True


def test_bloque_corto_se_interpreta_como_recreo() -> None:
    """El formato no trae `tipo`: un bloque de 20 min no puede ser una clase."""
    from datetime import time

    from app.domain.enums import TipoBloque
    from app.importer.analisis import UMBRAL_RECREO, tipo_de_bloque

    assert tipo_de_bloque(20) is TipoBloque.descanso
    assert tipo_de_bloque(UMBRAL_RECREO) is TipoBloque.descanso
    assert tipo_de_bloque(UMBRAL_RECREO + 1) is TipoBloque.clase
    assert tipo_de_bloque(45) is TipoBloque.clase

    libro = libro_minimo(bloques_extra=[("R1", time(13, 0), time(13, 20))])
    preview = analizar_libro(leer_libro(libro), archivo_nombre="recreo.xlsx")

    codigos = {hallazgo.codigo for hallazgo in preview.hallazgos}
    assert "RECREO_INFERIDO" in codigos
    assert "SIN_DESCANSOS" not in codigos
    recreo = next(bloque for bloque in preview.bloques if bloque.codigo == "R1")
    assert recreo.tipo is TipoBloque.descanso
    assert recreo.duracion_min == 20
