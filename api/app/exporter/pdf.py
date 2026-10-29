"""Exportación a PDF (D-017): una hoja por curso, docente o recurso.

`reportlab` es la única dependencia pesada del exportador. Se usa la fuente Helvetica que
trae la librería: **no** se registran fuentes del sistema, que es lo que rompe el PDF en la
máquina del pitch.
"""

from __future__ import annotations

import uuid
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.exporter.excel import DIAS, celdas, objetivo
from app.validator.estado import EstadoHorario

MEDIA_TYPE_PDF = "application/pdf"


def _tabla(celdas_bloque: dict[tuple[int, uuid.UUID], str], estado: EstadoHorario) -> Table:
    datos = [["Bloque", *DIAS]]
    for bloque in sorted(estado.bloques, key=lambda item: item.orden):
        fila = [f"{bloque.codigo}  {bloque.inicio:%H:%M}-{bloque.fin:%H:%M}"]
        fila += [celdas_bloque.get((dia, bloque.id), "—") for dia in range(1, 6)]
        datos.append(fila)

    tabla = Table(datos, colWidths=[90, 130, 130, 130, 130, 130], repeatRows=1)
    tabla.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F2937")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#9CA3AF")),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return tabla


def exportar_pdf(
    estado: EstadoHorario,
    sesiones: list[object],
    por: str,
    objetivo_id: uuid.UUID | None = None,
) -> bytes:
    salida = BytesIO()
    documento = SimpleDocTemplate(
        salida,
        pagesize=landscape(A4),
        leftMargin=28,
        rightMargin=28,
        topMargin=28,
        bottomMargin=28,
        title="Hourly — Horario de Profesor {estado.profesor.nombre}",
    )
    estilos = getSampleStyleSheet()
    historia: list[object] = []

    if por == "general":
        bloques_hoja = [
            (curso.codigo, [sesion for sesion in sesiones if sesion.curso_id == curso.id])
            for curso in estado.cursos
        ]
    else:
        elegidas = objetivo(estado, sesiones, por, objetivo_id)
        bloques_hoja = [("Horario", elegidas)]

    for indice, (titulo, propias) in enumerate(bloques_hoja):
        if indice:
            historia.append(PageBreak())
        historia.append(Paragraph(f"Hourly · {titulo}", estilos["Title"]))
        historia.append(Spacer(1, 8))
        historia.append(_tabla(celdas(propias, estado, por), estado))

    documento.build(historia)
    return salida.getvalue()
