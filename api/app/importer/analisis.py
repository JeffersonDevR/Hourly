"""Análisis del libro: parsing por hoja, validación por fila y plan de importación.

Un solo recorrido, tres consumidores: el preview de `POST /importaciones`, la
revalidación de `PATCH .../filas` y la confirmación. Todos parten de las mismas
`HojaCruda` JSON-safe, así que una corrección de celda se revalida con las mismas
reglas que el análisis original.

Nada de esto toca la DB: acá se decide qué filas son importables y se arma el plan
(`PreviewImportacion`). La escritura vive en `app.importer.confirmacion`.
"""

import re
import uuid
from dataclasses import dataclass, field

from app.domain.carga import AsignacionCarga, DisponibilidadBloqueo
from app.domain.catalogo import Aptitud, Asignatura, Bloque, Curso, Docente
from app.domain.enums import Gravedad, OrigenBloqueo, TipoBloque
from app.domain.horario import EscenarioCambio
from app.importer.coercion import (
    NOMBRE_DIA,
    a_booleano,
    a_dia,
    a_entero,
    a_hora,
    a_texto,
    minutos,
)
from app.importer.lectura import (
    OBLIGATORIAS,
    ORDEN_HOJAS,
    HojaCruda,
    buscar_hoja,
)
from app.importer.modelos import (
    AptitudImportada,
    AsignacionImportada,
    AsignaturaImportada,
    BloqueImportado,
    BloqueoImportado,
    CursoImportado,
    DocenteImportado,
    EscenarioCambioImportado,
    EscenarioImportado,
    Hallazgo,
    PreviewImportacion,
    RecursoImportado,
)
from app.validator.diagnostico import DOCENTE_SOBRECARGA, diagnosticar_carga
from app.validator.estado import EstadoHorario

#: Paleta determinista por orden alfabético: dos importaciones dan los mismos colores
#: (el Excel no trae `asignatura.color`, DOMAIN.md trampa 4).
PALETA: tuple[str, ...] = (
    "#2563EB",
    "#DC2626",
    "#059669",
    "#D97706",
    "#7C3AED",
    "#0891B2",
    "#DB2777",
    "#65A30D",
    "#EA580C",
    "#4F46E5",
    "#0D9488",
    "#9333EA",
)

_MINUTOS = re.compile(r"(\d+)\s*min", re.IGNORECASE)

#: Namespace fijo para los UUID sintéticos del estado que consume el validador.
_NS_ESTADO = uuid.UUID("8f0f3c1e-0000-4000-8000-000000000001")


def _id_estado(*partes: str) -> uuid.UUID:
    return uuid.uuid5(_NS_ESTADO, ":".join(partes))


def color_de_asignatura(nombre: str, catalogo: list[str]) -> str:
    """Color estable: posición del nombre en el catálogo ordenado alfabéticamente."""
    return PALETA[sorted(catalogo).index(nombre) % len(PALETA)]


@dataclass
class _Acumulador:
    """Estado mutable del recorrido. No sale de este módulo."""

    hallazgos: list[Hallazgo] = field(default_factory=list)
    cursos: list[CursoImportado] = field(default_factory=list)
    bloques: list[BloqueImportado] = field(default_factory=list)
    docentes: list[DocenteImportado] = field(default_factory=list)
    nombres_asignatura: list[str] = field(default_factory=list)
    aptitudes: list[tuple[str, str]] = field(default_factory=list)
    asignaciones: list[AsignacionImportada] = field(default_factory=list)
    tipos_recurso: list[str] = field(default_factory=list)
    recursos: list[RecursoImportado] = field(default_factory=list)
    bloqueos: list[BloqueoImportado] = field(default_factory=list)
    cambios: list[EscenarioCambioImportado] = field(default_factory=list)
    filas_disponibilidad: int = 0
    fila_carga_por_docente: dict[str, int] = field(default_factory=dict)
    nombre_carga: str = "Carga"

    def add(
        self,
        codigo: str,
        severidad: Gravedad,
        mensaje: str,
        *,
        hoja: str | None = None,
        fila: int | None = None,
        columna: str | None = None,
    ) -> None:
        self.hallazgos.append(Hallazgo(codigo, severidad, mensaje, hoja, fila, columna))

    @property
    def codigos_cursos(self) -> set[str]:
        return {curso.codigo for curso in self.cursos}

    @property
    def codigos_docentes(self) -> set[str]:
        return {docente.codigo for docente in self.docentes}

    @property
    def codigos_bloques(self) -> set[str]:
        return {bloque.codigo for bloque in self.bloques}


def _orden_hoja(nombre: str | None) -> int:
    if nombre is None:
        return len(ORDEN_HOJAS)
    for posicion, canonica in enumerate(ORDEN_HOJAS):
        if canonica.lower() == nombre.lower():
            return posicion
    return len(ORDEN_HOJAS)


def _texto_requerido(
    acc: _Acumulador, hoja: HojaCruda, fila_numero: int, columna: str, valor: object
) -> str | None:
    texto = a_texto(valor)
    if texto is None:
        acc.add(
            "VALOR_REQUERIDO",
            Gravedad.error,
            f"Falta el valor de '{columna}'.",
            hoja=hoja.nombre,
            fila=fila_numero,
            columna=columna,
        )
    return texto


def _bloques(hoja: HojaCruda, acc: _Acumulador) -> None:
    vistos: set[str] = set()
    for fila in hoja.filas_datos:
        codigo = _texto_requerido(
            acc, hoja, fila.numero, "bloque_id", hoja.valor(fila, "bloque_id")
        )
        if codigo is None:
            continue
        if codigo in vistos:
            acc.add(
                "DUPLICADO",
                Gravedad.error,
                f"El bloque '{codigo}' ya estaba definido; se ignora esta fila.",
                hoja=hoja.nombre,
                fila=fila.numero,
                columna="bloque_id",
            )
            continue
        inicio = a_hora(hoja.valor(fila, "inicio"))
        fin = a_hora(hoja.valor(fila, "fin"))
        if inicio is None or fin is None:
            columna = "inicio" if inicio is None else "fin"
            acc.add(
                "VALOR_REQUERIDO",
                Gravedad.error,
                f"El bloque '{codigo}' no tiene hora de {columna} válida.",
                hoja=hoja.nombre,
                fila=fila.numero,
                columna=columna,
            )
            continue
        duracion = minutos(fin) - minutos(inicio)
        if duracion <= 0:
            acc.add(
                "BLOQUE_INVALIDO",
                Gravedad.error,
                f"El bloque '{codigo}' termina antes de empezar ({inicio:%H:%M}-{fin:%H:%M}).",
                hoja=hoja.nombre,
                fila=fila.numero,
                columna="fin",
            )
            continue
        vistos.add(codigo)
        acc.bloques.append(
            BloqueImportado(
                codigo=codigo,
                orden=len(acc.bloques) + 1,
                inicio=inicio,
                fin=fin,
                duracion_min=duracion,
                tipo=TipoBloque.clase,  # el Excel no trae `tipo` (DOMAIN.md trampa 3)
            )
        )


def _cursos(hoja: HojaCruda, acc: _Acumulador) -> None:
    vistos: set[str] = set()
    for fila in hoja.filas_datos:
        codigo = _texto_requerido(acc, hoja, fila.numero, "curso_id", hoja.valor(fila, "curso_id"))
        if codigo is None:
            continue
        if codigo in vistos:
            acc.add(
                "DUPLICADO",
                Gravedad.error,
                f"El curso '{codigo}' ya estaba definido; se ignora esta fila.",
                hoja=hoja.nombre,
                fila=fila.numero,
                columna="curso_id",
            )
            continue
        grado = int(codigo[0]) if codigo[0].isdigit() else None
        if grado is None:
            acc.add(
                "CURSO_NO_RECONOCIDO",
                Gravedad.error,
                f"El curso '{codigo}' no empieza con un dígito de grado (6, 7, ...).",
                hoja=hoja.nombre,
                fila=fila.numero,
                columna="curso_id",
            )
            continue
        estudiantes = a_entero(hoja.valor(fila, "estudiantes"))
        if estudiantes is None or estudiantes <= 0:
            acc.add(
                "CURSO_SIN_ESTUDIANTES",
                Gravedad.advertencia,
                f"El curso '{codigo}' no declara estudiantes (> 0): la capacidad del "
                "salón no podrá validarse.",
                hoja=hoja.nombre,
                fila=fila.numero,
                columna="estudiantes",
            )
            estudiantes = max(estudiantes or 0, 0)
        vistos.add(codigo)
        acc.cursos.append(
            CursoImportado(
                codigo=codigo,
                nombre=a_texto(hoja.valor(fila, "nombre")) or codigo,
                grado=grado,
                estudiantes=estudiantes,
            )
        )


def _docentes(hoja: HojaCruda, acc: _Acumulador) -> None:
    vistos: set[str] = set()
    for fila in hoja.filas_datos:
        codigo = _texto_requerido(
            acc, hoja, fila.numero, "docente_id", hoja.valor(fila, "docente_id")
        )
        if codigo is None:
            continue
        if codigo in vistos:
            acc.add(
                "DUPLICADO",
                Gravedad.error,
                f"El docente '{codigo}' ya estaba definido; se ignora esta fila.",
                hoja=hoja.nombre,
                fila=fila.numero,
                columna="docente_id",
            )
            continue
        maximo = a_entero(hoja.valor(fila, "max_sesiones_semana"))
        if maximo is None or maximo <= 0:
            acc.add(
                "DOCENTE_SIN_MAXIMO",
                Gravedad.advertencia,
                f"El docente '{codigo}' no declara máximo de sesiones (> 0): CP-SAT lo "
                "tratará como tope duro y puede declarar INFACTIBLE por esa causa.",
                hoja=hoja.nombre,
                fila=fila.numero,
                columna="max_sesiones_semana",
            )
            maximo = max(maximo or 0, 0)
        vistos.add(codigo)
        acc.docentes.append(
            DocenteImportado(
                codigo=codigo,
                nombre=a_texto(hoja.valor(fila, "nombre")) or codigo,
                max_sesiones_semana=maximo,
            )
        )


def _asignaturas_docentes(hoja: HojaCruda, acc: _Acumulador) -> None:
    vistos: set[tuple[str, str]] = set()
    for fila in hoja.filas_datos:
        asignatura = _texto_requerido(
            acc, hoja, fila.numero, "asignatura", hoja.valor(fila, "asignatura")
        )
        if asignatura is None:
            continue
        if asignatura not in acc.nombres_asignatura:
            acc.nombres_asignatura.append(asignatura)

        habilitado = a_booleano(hoja.valor(fila, "habilitado"))
        if habilitado is None:
            acc.add(
                "VALOR_REQUERIDO",
                Gravedad.error,
                f"La habilitación de '{asignatura}' no es 1/0 reconocible.",
                hoja=hoja.nombre,
                fila=fila.numero,
                columna="habilitado",
            )
            continue
        if not habilitado:
            continue  # fila explícita en 0: no es una aptitud, tampoco un error.

        docente = _texto_requerido(
            acc, hoja, fila.numero, "docente_id", hoja.valor(fila, "docente_id")
        )
        if docente is None:
            continue
        if docente not in acc.codigos_docentes:
            acc.add(
                "DOCENTE_NO_RECONOCIDO",
                Gravedad.error,
                f"El docente '{docente}' no existe en la hoja Docentes.",
                hoja=hoja.nombre,
                fila=fila.numero,
                columna="docente_id",
            )
            continue
        clave = (asignatura, docente)
        if clave in vistos:
            acc.add(
                "DUPLICADO",
                Gravedad.error,
                f"Aptitud repetida: '{docente}' ya estaba habilitado para '{asignatura}'.",
                hoja=hoja.nombre,
                fila=fila.numero,
                columna="asignatura",
            )
            continue
        vistos.add(clave)
        acc.aptitudes.append(clave)


def _salones(hoja: HojaCruda, acc: _Acumulador) -> None:
    vistos: set[str] = set()
    for fila in hoja.filas_datos:
        codigo = _texto_requerido(acc, hoja, fila.numero, "salon_id", hoja.valor(fila, "salon_id"))
        if codigo is None:
            continue
        if codigo in vistos:
            acc.add(
                "DUPLICADO",
                Gravedad.error,
                f"El salón '{codigo}' ya estaba definido; se ignora esta fila.",
                hoja=hoja.nombre,
                fila=fila.numero,
                columna="salon_id",
            )
            continue
        tipo = _texto_requerido(acc, hoja, fila.numero, "tipo", hoja.valor(fila, "tipo"))
        if tipo is None:
            continue
        capacidad = a_entero(hoja.valor(fila, "capacidad"))
        if capacidad is None or capacidad <= 0:
            acc.add(
                "VALOR_REQUERIDO",
                Gravedad.error,
                f"El salón '{codigo}' no declara capacidad (> 0).",
                hoja=hoja.nombre,
                fila=fila.numero,
                columna="capacidad",
            )
            continue
        nombre = a_texto(hoja.valor(fila, "nombre")) or codigo
        titular: str | None = None
        if nombre.lower().startswith("aula "):
            candidato = nombre[5:].strip()
            if candidato in acc.codigos_cursos:
                titular = candidato
            else:
                acc.add(
                    "CURSO_NO_RECONOCIDO",
                    Gravedad.error,
                    f"El aula titular '{nombre}' no corresponde a ningún curso de la hoja Cursos.",
                    hoja=hoja.nombre,
                    fila=fila.numero,
                    columna="nombre",
                )
        if tipo not in acc.tipos_recurso:
            acc.tipos_recurso.append(tipo)
        vistos.add(codigo)
        acc.recursos.append(
            RecursoImportado(
                codigo=codigo,
                nombre=nombre,
                tipo_recurso=tipo,
                capacidad=capacidad,
                curso_titular=titular,
            )
        )


def _carga(hoja: HojaCruda, acc: _Acumulador) -> None:
    acc.nombre_carga = hoja.nombre
    vistos: set[tuple[str, str]] = set()
    aptitudes = set(acc.aptitudes)
    for fila in hoja.filas_datos:
        curso = _texto_requerido(acc, hoja, fila.numero, "curso_id", hoja.valor(fila, "curso_id"))
        asignatura = _texto_requerido(
            acc, hoja, fila.numero, "asignatura", hoja.valor(fila, "asignatura")
        )
        docente = _texto_requerido(
            acc, hoja, fila.numero, "docente_principal_id", hoja.valor(fila, "docente_principal_id")
        )
        if curso is None or asignatura is None or docente is None:
            continue
        if curso not in acc.codigos_cursos:
            acc.add(
                "CURSO_NO_RECONOCIDO",
                Gravedad.error,
                f"El curso '{curso}' no existe en la hoja Cursos.",
                hoja=hoja.nombre,
                fila=fila.numero,
                columna="curso_id",
            )
            continue
        if asignatura not in acc.nombres_asignatura:
            acc.add(
                "ASIGNATURA_NO_RECONOCIDA",
                Gravedad.error,
                f"La asignatura '{asignatura}' no aparece en 'Asignaturas docentes'.",
                hoja=hoja.nombre,
                fila=fila.numero,
                columna="asignatura",
            )
            continue
        if docente not in acc.codigos_docentes:
            acc.add(
                "DOCENTE_NO_RECONOCIDO",
                Gravedad.error,
                f"El docente '{docente}' no existe en la hoja Docentes.",
                hoja=hoja.nombre,
                fila=fila.numero,
                columna="docente_principal_id",
            )
            continue
        tipo = _texto_requerido(
            acc, hoja, fila.numero, "tipo_salon_requerido", hoja.valor(fila, "tipo_salon_requerido")
        )
        if tipo is None:
            continue
        if tipo not in acc.tipos_recurso:
            acc.add(
                "TIPO_RECURSO_NO_RECONOCIDO",
                Gravedad.error,
                f"El tipo de salón '{tipo}' no existe en la hoja Salones.",
                hoja=hoja.nombre,
                fila=fila.numero,
                columna="tipo_salon_requerido",
            )
            continue
        sesiones = a_entero(hoja.valor(fila, "sesiones_semana"))
        if sesiones is None or sesiones <= 0:
            acc.add(
                "VALOR_REQUERIDO",
                Gravedad.error,
                f"'{asignatura}' en '{curso}' no declara sesiones semanales (> 0).",
                hoja=hoja.nombre,
                fila=fila.numero,
                columna="sesiones_semana",
            )
            continue
        if (asignatura, docente) not in aptitudes:
            acc.add(
                "APTITUD_FALTANTE",
                Gravedad.error,
                f"'{docente}' no está habilitado para '{asignatura}': agrega la fila en "
                "'Asignaturas docentes' o cambia el docente principal.",
                hoja=hoja.nombre,
                fila=fila.numero,
                columna="docente_principal_id",
            )
            continue
        clave = (curso, asignatura)
        if clave in vistos:
            acc.add(
                "DUPLICADO",
                Gravedad.error,
                f"'{curso}' ya tiene una fila de carga para '{asignatura}' "
                "(UNIQUE(curso_id, asignatura_id)).",
                hoja=hoja.nombre,
                fila=fila.numero,
                columna="asignatura",
            )
            continue
        vistos.add(clave)
        acc.fila_carga_por_docente.setdefault(docente, fila.numero)
        acc.asignaciones.append(
            AsignacionImportada(
                curso=curso,
                asignatura=asignatura,
                docente_principal=docente,
                sesiones_semana=sesiones,
                tipo_recurso_requerido=tipo,
            )
        )


def _disponibilidad(hoja: HojaCruda, acc: _Acumulador) -> None:
    """Cuadrícula 1/0: se guardan solo las franjas con 0 (DOMAIN.md)."""
    vistos: set[tuple[str, int, str]] = set()
    for fila in hoja.filas_datos:
        docente = _texto_requerido(
            acc, hoja, fila.numero, "docente_id", hoja.valor(fila, "docente_id")
        )
        if docente is None:
            continue
        if docente not in acc.codigos_docentes:
            acc.add(
                "DOCENTE_NO_RECONOCIDO",
                Gravedad.error,
                f"El docente '{docente}' no existe en la hoja Docentes.",
                hoja=hoja.nombre,
                fila=fila.numero,
                columna="docente_id",
            )
            continue
        dia_texto = hoja.valor(fila, "dia")
        dia = a_dia(dia_texto)
        if dia is None:
            acc.add(
                "DIA_NO_RECONOCIDO",
                Gravedad.advertencia,
                f"Día '{a_texto(dia_texto) or ''}' no reconocido (Lunes..Viernes); "
                "se ignora la fila.",
                hoja=hoja.nombre,
                fila=fila.numero,
                columna="dia",
            )
            continue
        bloque = _texto_requerido(
            acc, hoja, fila.numero, "bloque_id", hoja.valor(fila, "bloque_id")
        )
        if bloque is None:
            continue
        if bloque not in acc.codigos_bloques:
            acc.add(
                "BLOQUE_NO_RECONOCIDO",
                Gravedad.error,
                f"El bloque '{bloque}' no existe en la hoja Bloques.",
                hoja=hoja.nombre,
                fila=fila.numero,
                columna="bloque_id",
            )
            continue
        disponible = a_booleano(hoja.valor(fila, "disponible"))
        if disponible is None:
            acc.add(
                "VALOR_REQUERIDO",
                Gravedad.error,
                "La columna 'disponible' no es 1/0 reconocible.",
                hoja=hoja.nombre,
                fila=fila.numero,
                columna="disponible",
            )
            continue
        clave = (docente, dia, bloque)
        if clave in vistos:
            acc.add(
                "DUPLICADO",
                Gravedad.error,
                f"Franja repetida: '{docente}' {NOMBRE_DIA[dia]} {bloque}.",
                hoja=hoja.nombre,
                fila=fila.numero,
                columna="dia",
            )
            continue
        vistos.add(clave)
        acc.filas_disponibilidad += 1
        if not disponible:
            acc.bloqueos.append(BloqueoImportado(docente=docente, dia=dia, bloque=bloque))


def _cambios(hoja: HojaCruda, acc: _Acumulador) -> None:
    """Overlay de escenario: NUNCA se escribe en `disponibilidad_bloqueo` (D-005)."""
    vistos: set[tuple[str, int, str]] = set()
    for fila in hoja.filas_datos:
        docente = _texto_requerido(
            acc, hoja, fila.numero, "docente_id", hoja.valor(fila, "docente_id")
        )
        if docente is None:
            continue
        if docente not in acc.codigos_docentes:
            acc.add(
                "DOCENTE_NO_RECONOCIDO",
                Gravedad.error,
                f"El docente '{docente}' no existe en la hoja Docentes.",
                hoja=hoja.nombre,
                fila=fila.numero,
                columna="docente_id",
            )
            continue
        dia_texto = hoja.valor(fila, "dia")
        dia = a_dia(dia_texto)
        if dia is None:
            acc.add(
                "DIA_NO_RECONOCIDO",
                Gravedad.advertencia,
                f"Día '{a_texto(dia_texto) or ''}' no reconocido (Lunes..Viernes); "
                "se ignora la fila.",
                hoja=hoja.nombre,
                fila=fila.numero,
                columna="dia",
            )
            continue
        bloque = _texto_requerido(
            acc, hoja, fila.numero, "bloque_id", hoja.valor(fila, "bloque_id")
        )
        if bloque is None:
            continue
        if bloque not in acc.codigos_bloques:
            acc.add(
                "BLOQUE_NO_RECONOCIDO",
                Gravedad.error,
                f"El bloque '{bloque}' no existe en la hoja Bloques.",
                hoja=hoja.nombre,
                fila=fila.numero,
                columna="bloque_id",
            )
            continue
        disponible_nuevo = a_booleano(hoja.valor(fila, "disponible_nuevo"))
        if disponible_nuevo is None:
            acc.add(
                "VALOR_REQUERIDO",
                Gravedad.error,
                "La columna 'disponible_nuevo' no es 1/0 reconocible.",
                hoja=hoja.nombre,
                fila=fila.numero,
                columna="disponible_nuevo",
            )
            continue
        clave = (docente, dia, bloque)
        if clave in vistos:
            acc.add(
                "DUPLICADO",
                Gravedad.error,
                f"Franja repetida en el escenario: '{docente}' {NOMBRE_DIA[dia]} {bloque}.",
                hoja=hoja.nombre,
                fila=fila.numero,
                columna="dia",
            )
            continue
        vistos.add(clave)
        acc.cambios.append(
            EscenarioCambioImportado(
                docente=docente,
                dia=dia,
                bloque=bloque,
                disponible_nuevo=disponible_nuevo,
                motivo=a_texto(hoja.valor(fila, "motivo")),
            )
        )


def _nombre_escenario(cambios: list[EscenarioCambioImportado]) -> str:
    docentes = sorted({cambio.docente for cambio in cambios})
    dias = sorted({cambio.dia for cambio in cambios})
    if len(docentes) == 1 and len(dias) == 1:
        return f"{docentes[0]} sin clase el {NOMBRE_DIA[dias[0]].lower()}"
    return "Cambios de disponibilidad importados"


def _estado_para_diagnostico(acc: _Acumulador) -> EstadoHorario:
    """Grafo en memoria con UUID sintéticos: `diagnosticar_carga` solo compara ids."""
    docentes = tuple(
        Docente(
            codigo=docente.codigo,
            nombre=docente.nombre,
            max_sesiones_semana=docente.max_sesiones_semana,
            id=_id_estado("docente", docente.codigo),
        )
        for docente in acc.docentes
    )
    cursos = tuple(
        Curso(
            codigo=curso.codigo,
            nombre=curso.nombre,
            grado_id=_id_estado("grado", str(curso.grado)),
            estudiantes=curso.estudiantes,
            id=_id_estado("curso", curso.codigo),
        )
        for curso in acc.cursos
    )
    bloques = tuple(
        Bloque(
            codigo=bloque.codigo,
            orden=bloque.orden,
            inicio=bloque.inicio,
            fin=bloque.fin,
            duracion_min=bloque.duracion_min,
            tipo=bloque.tipo,
            id=_id_estado("bloque", bloque.codigo),
        )
        for bloque in acc.bloques
    )
    asignaturas = tuple(
        Asignatura(nombre=nombre, color="#000000", id=_id_estado("asignatura", nombre))
        for nombre in acc.nombres_asignatura
    )
    aptitudes = tuple(
        Aptitud(
            docente_id=_id_estado("docente", docente),
            asignatura_id=_id_estado("asignatura", asignatura),
        )
        for asignatura, docente in acc.aptitudes
    )
    asignaciones = tuple(
        AsignacionCarga(
            curso_id=_id_estado("curso", asignacion.curso),
            asignatura_id=_id_estado("asignatura", asignacion.asignatura),
            docente_principal_id=_id_estado("docente", asignacion.docente_principal),
            sesiones_semana=asignacion.sesiones_semana,
            tipo_recurso_requerido=asignacion.tipo_recurso_requerido,
        )
        for asignacion in acc.asignaciones
    )
    bloqueos = tuple(
        DisponibilidadBloqueo(
            docente_id=_id_estado("docente", bloqueo.docente),
            dia=bloqueo.dia,
            bloque_id=_id_estado("bloque", bloqueo.bloque),
            origen=OrigenBloqueo.personal,
        )
        for bloqueo in acc.bloqueos
    )
    cambios = tuple(
        EscenarioCambio(
            escenario_id=_id_estado("escenario", "importado"),
            docente_id=_id_estado("docente", cambio.docente),
            dia=cambio.dia,
            bloque_id=_id_estado("bloque", cambio.bloque),
            disponible_nuevo=cambio.disponible_nuevo,
            motivo=cambio.motivo,
        )
        for cambio in acc.cambios
    )
    return EstadoHorario(
        cursos=cursos,
        docentes=docentes,
        bloques=bloques,
        asignaturas=asignaturas,
        aptitudes=aptitudes,
        asignaciones=asignaciones,
        bloqueos=bloqueos,
        escenario_cambios=cambios,
    )


def analizar_libro(
    hojas: dict[str, HojaCruda], *, archivo_nombre: str = ""
) -> PreviewImportacion:
    """Valida el libro completo y devuelve el plan de importación con sus hallazgos."""
    acc = _Acumulador()
    conteos: dict[str, int] = {}

    for hoja in hojas.values():
        if hoja.filas_vacias:
            acc.add(
                "FILAS_VACIAS_IGNORADAS",
                Gravedad.advertencia,
                f"{hoja.filas_vacias} fila(s) totalmente vacía(s) ignorada(s).",
                hoja=hoja.nombre,
            )

    for nombre in OBLIGATORIAS:
        if buscar_hoja(hojas, nombre) is None:
            acc.add(
                "HOJA_FALTANTE",
                Gravedad.error,
                f"El libro no tiene la hoja obligatoria '{nombre}'.",
                hoja=nombre,
            )

    hoja_leeme = buscar_hoja(hojas, "Leeme")
    hoja_bloques = buscar_hoja(hojas, "Bloques")
    hoja_cursos = buscar_hoja(hojas, "Cursos")
    hoja_docentes = buscar_hoja(hojas, "Docentes")
    hoja_aptitudes = buscar_hoja(hojas, "Asignaturas docentes")
    hoja_salones = buscar_hoja(hojas, "Salones")
    hoja_carga = buscar_hoja(hojas, "Carga")
    hoja_disponibilidad = buscar_hoja(hojas, "Disponibilidad")
    hoja_cambio = buscar_hoja(hojas, "Cambio")

    if hoja_cursos is not None:
        _cursos(hoja_cursos, acc)
    if hoja_bloques is not None:
        _bloques(hoja_bloques, acc)
    if hoja_docentes is not None:
        _docentes(hoja_docentes, acc)
    if hoja_aptitudes is not None:
        _asignaturas_docentes(hoja_aptitudes, acc)
    if hoja_salones is not None:
        _salones(hoja_salones, acc)
    if hoja_carga is not None:
        _carga(hoja_carga, acc)
    if hoja_disponibilidad is not None:
        _disponibilidad(hoja_disponibilidad, acc)
    if hoja_cambio is not None:
        _cambios(hoja_cambio, acc)

    # Colores deterministas por orden alfabético (DOMAIN.md trampa 4).
    orden_asignaturas = sorted(acc.nombres_asignatura)
    asignaturas = tuple(
        AsignaturaImportada(nombre=nombre, color=color_de_asignatura(nombre, orden_asignaturas))
        for nombre in acc.nombres_asignatura
    )

    # Leeme declara la duración; Bloques manda porque tiene inicio/fin (trampa 2 y 3).
    if hoja_leeme is not None:
        declaracion = _declaracion_minutos(hoja_leeme)
        duraciones = {bloque.duracion_min for bloque in acc.bloques}
        if declaracion is not None and duraciones - {declaracion[0]}:
            declarada, fila_declaracion = declaracion
            distintas = sorted(duraciones)
            acc.add(
                "DURACION_BLOQUE_INCONSISTENTE",
                Gravedad.advertencia,
                f"Leeme declara bloques de {declarada} min, pero Bloques define "
                f"{'/'.join(str(valor) for valor in distintas)} min "
                "(se usa inicio/fin como verdad).",
                hoja=hoja_leeme.nombre,
                fila=fila_declaracion,
                columna="Descripción",
            )

    if acc.bloques and all(bloque.tipo == TipoBloque.clase for bloque in acc.bloques):
        acc.add(
            "SIN_DESCANSOS",
            Gravedad.advertencia,
            f"Los {len(acc.bloques)} bloques son de clase: no hay descanso ni almuerzo.",
            hoja=hoja_bloques.nombre if hoja_bloques else "Bloques",
            columna="tipo",
        )

    diagnosticos = tuple(diagnosticar_carga(_estado_para_diagnostico(acc)))
    for diagnostico in diagnosticos:
        if diagnostico.codigo != DOCENTE_SOBRECARGA:
            continue
        acc.add(
            DOCENTE_SOBRECARGA,
            Gravedad.error,
            diagnostico.mensaje,
            hoja=acc.nombre_carga,
            fila=acc.fila_carga_por_docente.get(diagnostico.docente_codigo or ""),
            columna="docente_principal_id",
        )

    escenario = None
    if acc.cambios:
        escenario = EscenarioImportado(
            nombre=_nombre_escenario(acc.cambios),
            descripcion=(
                f"Importado de la hoja {hoja_cambio.nombre if hoja_cambio else 'Cambio'}: "
                f"{len(acc.cambios)} franja(s) con disponibilidad cambiada."
            ),
            cambios=tuple(acc.cambios),
        )

    conteos.update(
        {
            "leeme": _filas_no_vacias(hoja_leeme),
            "bloques": len(acc.bloques),
            "cursos": len(acc.cursos),
            "grados": len({curso.grado for curso in acc.cursos}),
            "docentes": len(acc.docentes),
            "asignaturas": len(acc.nombres_asignatura),
            "aptitudes": len(acc.aptitudes),
            "asignaciones": len(acc.asignaciones),
            "tipos_recurso": len(acc.tipos_recurso),
            "recursos": len(acc.recursos),
            "disponibilidad": acc.filas_disponibilidad,
            "bloqueos": len(acc.bloqueos),
            "escenarios": 1 if escenario else 0,
            "escenario_cambios": len(acc.cambios),
        }
    )

    hallazgos = tuple(
        sorted(
            acc.hallazgos,
            key=lambda h: (_orden_hoja(h.hoja), h.fila or 0, h.codigo, h.mensaje),
        )
    )

    return PreviewImportacion(
        archivo_nombre=archivo_nombre,
        hojas=hojas,
        conteos=conteos,
        hallazgos=hallazgos,
        diagnosticos=diagnosticos,
        cursos=tuple(acc.cursos),
        bloques=tuple(acc.bloques),
        docentes=tuple(acc.docentes),
        asignaturas=asignaturas,
        aptitudes=tuple(
            AptitudImportada(asignatura=asignatura, docente=docente)
            for asignatura, docente in acc.aptitudes
        ),
        asignaciones=tuple(acc.asignaciones),
        tipos_recurso=tuple(acc.tipos_recurso),
        recursos=tuple(acc.recursos),
        bloqueos=tuple(acc.bloqueos),
        escenario=escenario,
    )


def _filas_no_vacias(hoja: HojaCruda | None) -> int:
    if hoja is None:
        return 0
    encabezado = 1 if any(hoja.encabezado) else 0
    return encabezado + len(hoja.filas_datos)


def _declaracion_minutos(hoja: HojaCruda) -> tuple[int, int] | None:
    """Primer 'NN min' de la hoja informativa, con su fila."""
    for fila in hoja.filas:
        for celda in fila.celdas:
            if isinstance(celda, str):
                coincidencia = _MINUTOS.search(celda)
                if coincidencia is not None:
                    return int(coincidencia.group(1)), fila.numero
    return None
