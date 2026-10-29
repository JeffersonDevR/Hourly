"""Generadores de libros .xlsx para los tests del importador.

No son datos de negocio nuevos: copian las claves del archivo real (7A, D1, B1,
'Aula 7A') y existen por dos motivos concretos:

- **Archivo sucio**: un curso duplicado y una carga con un curso inexistente, para
  `DUPLICADO` / `CURSO_NO_RECONOCIDO`.
- **Booleanos como floats**: el archivo real trae `<v>1.0</v>`, no `<v>1</v>`.
  `openpyxl` normaliza `1.0` a `1` al escribir, así que el libro sintético se
  post-procesa para dejarlo igual que el original. Sin esto, el test de coerción
  pasaría también con una lectura equivocada (`== "1"`), que es la trampa documentada.
"""

import re
import zipfile
from datetime import time
from io import BytesIO
from pathlib import Path

import openpyxl
from openpyxl.worksheet.worksheet import Worksheet

from app.importer.lectura import ENCABEZADOS

CURSOS: tuple[tuple[str, float], ...] = (
    ("7A", 30.0),
    ("7B", 28.0),
    ("6A", 30.0),
    ("6B", 28.0),
)

BLOQUES: tuple[tuple[str, time, time], ...] = (
    ("B1", time(7, 0), time(8, 0)),
    ("B2", time(8, 0), time(9, 0)),
    ("B3", time(9, 0), time(10, 0)),
    ("B4", time(10, 0), time(11, 0)),
    ("B5", time(11, 0), time(12, 0)),
    ("B6", time(12, 0), time(13, 0)),
)

DOCENTES: tuple[tuple[str, str], ...] = (
    ("D1", "Ana Torres"),
    ("D2", "Luis Vega"),
    ("D3", "Marta Ruiz"),
    ("D4", "Carlos Peña"),
    ("D5", "Diana Rojas"),
    ("D6", "Andrés Castro"),
)

#: 11 filas, 10 asignaturas: Inglés la dictan D4 y D6 (ARCHITECTURE.md golden 1).
APTITUDES: tuple[tuple[str, str], ...] = (
    ("Matemáticas", "D1"),
    ("Lenguaje", "D2"),
    ("Ciencias naturales", "D3"),
    ("Ciencias sociales", "D3"),
    ("Inglés", "D4"),
    ("Inglés", "D6"),
    ("Educación física", "D4"),
    ("Tecnología e informática", "D1"),
    ("Educación artística", "D6"),
    ("Ética y valores", "D5"),
    ("Educación religiosa", "D5"),
)

CARGA: tuple[tuple[str, str, float, str], ...] = (
    ("Matemáticas", "D1", 4.0, "GENERAL"),
    ("Lenguaje", "D2", 4.0, "GENERAL"),
    ("Ciencias naturales", "D3", 3.0, "LAB_CIENCIAS"),
    ("Ciencias sociales", "D3", 3.0, "GENERAL"),
    ("Inglés", "D4", 4.0, "GENERAL"),
    ("Educación física", "D4", 3.0, "CANCHA"),
    ("Tecnología e informática", "D1", 2.0, "SALA_INFORMATICA"),
    ("Educación artística", "D6", 3.0, "GENERAL"),
    ("Ética y valores", "D5", 1.0, "GENERAL"),
    ("Educación religiosa", "D5", 3.0, "GENERAL"),
)

SALONES: tuple[tuple[str, str, str, float], ...] = (
    ("A1", "Aula 7A", "GENERAL", 30.0),
    ("L1", "Laboratorio 1", "LAB_CIENCIAS", 30.0),
    ("C1", "Cancha 1", "CANCHA", 30.0),
    ("I1", "Informática 1", "SALA_INFORMATICA", 30.0),
)

DIAS: tuple[str, ...] = ("Lunes", "Martes", "Miércoles", "Jueves", "Viernes")

#: La única franja no disponible del libro sintético: D1, Viernes, B6.
BLOQUEO: tuple[str, str, str] = ("D1", "Viernes", "B6")


def _crear_hojas(libro: openpyxl.Workbook) -> dict[str, Worksheet]:
    hojas: dict[str, Worksheet] = {}
    activa = libro.active
    assert activa is not None
    for posicion, (nombre, encabezado) in enumerate(ENCABEZADOS.items()):
        hoja = activa if posicion == 0 else libro.create_sheet()
        hoja.title = nombre
        hoja.append(list(encabezado))
        hojas[nombre] = hoja
    return hojas


def _forzar_booleanos_float(contenido: bytes) -> bytes:
    """`<v>1</v>` -> `<v>1.0</v>` en las hojas de columnas 1/0.

    Es la forma que tiene el archivo real (lo generó una herramienta que escribe
    floats). Sin esto, `openpyxl` devuelve `int` y el test no distinguiría una
    coerción correcta de la trampa `== "1"`.
    """
    entrada = zipfile.ZipFile(BytesIO(contenido))
    salida = BytesIO()
    with zipfile.ZipFile(salida, "w", zipfile.ZIP_DEFLATED) as destino:
        for elemento in entrada.infolist():
            datos = entrada.read(elemento.filename)
            if elemento.filename.startswith("xl/worksheets/sheet"):
                texto = datos.decode()
                if any(
                    f"<t>{columna}</t>" in texto
                    for columna in ("habilitado", "disponible", "disponible_nuevo")
                ):
                    datos = re.sub(r"<v>([01])</v>", r"<v>\1.0</v>", texto).encode()
            destino.writestr(elemento, datos)
    return salida.getvalue()


def libro_minimo(
    *,
    duplicar_curso: bool = False,
    curso_malo: bool = False,
    forzar_floats: bool = True,
    sin_hoja: str | None = None,
    bloques_extra: list[tuple[str, object, object]] | None = None,
) -> bytes:
    """Libro completo y coherente con el formato del importador.

    Args:
        duplicar_curso: agrega una segunda fila con `curso_id` 7A (DUPLICADO).
        curso_malo: la primera fila de Carga apunta a un curso inexistente (9C).
        forzar_floats: deja los booleanos como `1.0`/`0.0`, igual que el archivo real.
        sin_hoja: nombre de una hoja a eliminar (para `HOJA_FALTANTE`).
    """
    libro = openpyxl.Workbook()
    hojas = _crear_hojas(libro)

    hojas["Leeme"].append(["Caso", "Datos sintéticos para los tests del importador"])
    hojas["Leeme"].append(["Unidad", "Cada bloque es de 50 minutos"])

    for codigo, inicio, fin in [*BLOQUES, *(bloques_extra or [])]:
        hojas["Bloques"].append([codigo, inicio, fin])

    for codigo, estudiantes in CURSOS:
        hojas["Cursos"].append([codigo, codigo, estudiantes])
    if duplicar_curso:
        hojas["Cursos"].append(["7A", "7A", 30.0])

    for codigo, nombre in DOCENTES:
        hojas["Docentes"].append([codigo, nombre, 24.0])

    for asignatura, docente in APTITUDES:
        hojas["Asignaturas docentes"].append([asignatura, docente, 1.0])

    for asignatura, docente, sesiones, tipo in CARGA:
        hojas["Carga"].append(["7A", asignatura, docente, sesiones, tipo])
    if curso_malo:
        hojas["Carga"]["A2"] = "9C"

    for codigo, nombre, tipo, capacidad in SALONES:
        hojas["Salones"].append([codigo, nombre, tipo, capacidad])

    for docente, _ in DOCENTES:
        for dia in DIAS:
            for codigo, _, _ in BLOQUES:
                disponible = 0.0 if (docente, dia, codigo) == BLOQUEO else 1.0
                hojas["Disponibilidad"].append([docente, dia, codigo, disponible])

    hojas["Cambio"].append(["D2", "Martes", "B1", 0.0, "Indisponibilidad adicional"])

    if sin_hoja is not None:
        libro.remove(libro[sin_hoja])

    flujo = BytesIO()
    libro.save(flujo)
    contenido = flujo.getvalue()
    return _forzar_booleanos_float(contenido) if forzar_floats else contenido


def guardar(contenido: bytes, destino: Path) -> Path:
    destino.write_bytes(contenido)
    return destino
