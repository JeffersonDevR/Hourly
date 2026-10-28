# MALLA · Diseño — documento único

**Este es el único lugar que necesitas.** Todo el diseño vive acá: sistema, pantallas,
decisiones, defectos abiertos y qué está obsoleto. Si algo no está enlazado desde este
archivo, no es fuente de verdad.

Proyecto Stitch: `3916526485862441063`
Design system: `assets/44af003a88054ae8806013207408fd99` — *Academic Grid Matrix · Dark Accessible*
Estado: **14 pantallas web entregadas**. Solo web, sin móvil. Piso de soporte 768px.

> **El flujo real del producto son 6 pasos:** Importar → Auditar → Generar → Resolver →
> Publicar → Probar. El paso 6 vuelve al 3 (bucle de escenario). Las pantallas de Cursos,
> Docentes, Recursos, Inicio y Reglas son configuración, no pasos del flujo.

---

## 1. Dónde está cada cosa

| Archivo | Qué contiene | Estado |
|---|---|---|
| `design/stitch/README.md` | Este documento. Índice y estado. | ✅ canónico |
| `design/stitch/tokens.css` | Variables CSS, mapeo a Tailwind, reglas responsive, regla global de foco | ✅ canónico |
| Stitch (proyecto arriba) | Las 11 pantallas web + 1 responsive | ✅ canónico |
| `AiCalendar/design/DESIGN.md` | Sistema **claro** v2 (17px no, 12px sí) | ⛔ **obsoleto** |
| `AiCalendar/design/AUDIT.md` | Auditoría del sistema claro v1/v2 | ⛔ **obsoleto** |
| `docs/DOMAIN.md`, `docs/ARCHITECTURE.md` | Dominio y arquitectura del producto | ✅ fuente de verdad del dominio |

Regla de consumo para la implementación: **los tokens salen de `tokens.css`**, el dominio de
`docs/DOMAIN.md`, y las pantallas de Stitch son referencia visual, no código a copiar.

---

## 2. Reglas no negociables

Las cinco que hacen que esto sirva para **personas mayores**. Si una se rompe, la pantalla está mal.

1. **Texto base 17px.** Mínimo absoluto 14px, solo en etiquetas cortas de estado. Nunca 11-13px.
2. **Objetivos de 44px mínimo**, 48px en la acción primaria.
3. **Contraste AAA (7:1)** en todo texto. Está medido en los tokens. Nunca aclarar `--mh-text-muted`.
4. **Una acción primaria por pantalla.** Relleno blanco, texto casi negro. El resto, contorno.
5. **El color nunca va solo.** Todo estado lleva icono + palabra: Correcto, Revisar, Conflicto, Propuesta.

Y dos prohibiciones técnicas que ya aparecieron repetidas veces:

- **Nunca `overflow-x: hidden` en `body`.** Es el parche. Se declara scroll en el contenedor o se cambia la forma del componente.
- **Nunca colapsar la navegación a solo iconos.** Rompe la regla de etiqueta visible.

**Turquesa `#5EEAD4` está reservado:** significa "esto lo propuso el asistente". No se usa en
ningún otro lugar de la app.

---

## 3. Pantallas web (1440)

Todas en modo oscuro. El identificador sirve para abrir la pantalla en Stitch.

| # | Pantalla | ID | Qué resuelve | Fase |
|---|---|---|---|---|
| 1 | **Inicio** | `bdaa4d284f39498d9edc4416c85bc4ab` | Estado del horario + checklist de 5 pasos | 06 |
| 2 | **Importar** | `8d4785123bb64b4fa81f888f32d766cf` | Paso 3 de 4: revisar errores y avisos del Excel | 06 |
| 3 | **Horario** | `d501bbe30a804ad4a4d2ff4fcf963758` | Cuadrícula semanal + panel "Por colocar" | 07 |
| 4 | **Conflictos** | `90ca9654e58944499cc6abe5ee61541a` | Un conflicto a la vez, con propuesta del asistente | 08 |
| 5 | **Docentes** | `f0beab2f23fe430aa0b05f590c6dad31` | Tarjetas con barra de carga y alerta de exceso | 06 |
| 6 | **Recursos** | `ea5dbf053d774179bb979be914d6d159` | Aulas y espacios especiales | 06 |
| 7 | **Publicar** | `fb6060ecf53b4cf48e7296786d971bd6` | Validación, versiones y exportación | 09 |
| 8 | **Escenario ¿y si…?** | `8a45319e905746f08973bf62b7999114` | Simulación de ausencia con impacto antes de aplicar | 09 |
| 9 | **Cursos** | `9375e2225b0549d8bbf9714bd72263d0` | Los 4 grupos con su aula titular y estado | 06 |
| 10 | **Reglas** | `ca4c8ed5fcfb4466ba9e53f0651e3746` | Lenguaje natural → regla interpretada | 08 |
| 11 | **Sistema de diseño** | `0c9c102a12f54bd0bdc2e718e208ee49` | Hoja de referencia: color, tipografía, botones, estados | — |
| 12 | **Biblioteca de estados** | `d542d93107ce4c18b71104514f540f78` | Vacío, cargando, error, conflicto, éxito, IA no disponible, trabajando | — |
| 13 | **Mapa de flujo v3** | `9a4c2abbbbfb45d295b3c35cedddaab1` | Los 6 pasos reales + las pantallas de configuración | — |
| 14 | **Identidad de marca** | `7e231b4ba3f94c2397b6f9cd18215864` | Tres propuestas de logo para "Hourly" | — |

**Marca aplicada en las 14.** Logo elegido: concepto **C**, la H geométrica con travesaño lila y
punto crema. En la barra lateral va en **lockup vertical** (marca arriba, "Hourly" 15px abajo) porque
el horizontal no cabe en los 88px. En la barra superior va solo la marca a 24px junto al breadcrumb,
nunca el wordmark: repetir "Hourly" dos veces por pantalla es ruido.

**Responsive:** Horario tablet `3dee5ce22abb4a658c21dbdafda172f3` (1024).

### Navegación

Barra lateral de **siete destinos**, no crece:
`Inicio · Importar · Horario · Conflictos · Docentes · Recursos · Publicar`

`Cursos` y `Reglas` son secundarias: se llegan desde Inicio y desde Conflictos. El escenario
vive en la barra superior, no en la navegación.

### Mapa de flujo

9 etapas en 3 fases: Configuración → Cursos → Malla → Docentes → Espacios → **Verificación**
(compuerta) → Horario maestro → Conflictos y solver → Publicar. El escenario es un bucle
reversible sobre las etapas 7 y 8.

---

## 4. Datos de demo canónicos

No inventar otras cifras: la demo se rompe cuando los números no cuadran entre pantallas.

- **4 cursos**: 6A, 6B, 7A, 7B · **30 bloques** por curso (6 × 5 días) · **120 sesiones**.
- **6 docentes**: Marta Ruiz (24/24), Ana Restrepo (24/24), **Carlos Mendoza 28/24 — exceso**,
  Jorge Salazar (21/24), Luisa Ortiz (19/24), **Diego Herrera 16/24 — cupo libre**.
- **Conflicto principal**: Carlos Mendoza demanda 28 clases (Inglés 16 + Ed. Física 12) contra
  un máximo de 24. La propuesta del asistente pasa una sesión de Inglés a Diego Herrera.
- **Conflicto secundario**: Aula 7B admite 24 estudiantes y el grupo tiene 30.
- **Escenario**: "D2 sin clase el martes" — 16 sesiones afectadas, 4 por reubicar.

---

## 5. Responsive (solo web)

| Rango | Barra lateral | Cuadrícula | Paneles | Texto |
|---|---|---|---|---|
| ≥ 1280 | 88px con etiqueta | 5 días | laterales de 320px | 17px |
| 1024–1279 | 72px con etiqueta | 5 días, ancho completo | debajo | 16px |
| 768–1023 | 72px con etiqueta | **1 día a la vez** (pestañas) | apilados | 16px |
| < 768 | no soportado | — | — | aviso de tamaño |

**Por debajo de 1024 la cuadrícula no se comprime ni scrollea en horizontal: cambia de forma.**

---

## 6. Defectos abiertos

| Pantalla | Qué pasa | Dónde se arregla |
|---|---|---|
| Inicio | La línea de pie queda bajo el pliegue en el export de 1024px | El contenido hace scroll en la app real. No es defecto de diseño. |
| Docentes | Sin `:focus-visible` horneado en el CSS del mock | Regla global de `tokens.css` |
| Sistema de diseño | La celda "Propuesta" sigue con dos textos superpuestos | Rehacer esa celda a mano; es un espécimen |
| Sistema de diseño | Quedan 3 `outline-none` | `tokens.css` |
| Reglas | 3 de 24 iconos SVG sin `aria-hidden` | Marcar a mano |
| Horario tablet | `overflow-x: hidden` en un contenedor | Sustituir por `.mh-scroll-y` |
| Importar, Publicar, Recursos, Escenario | Sin `aria-live` en contadores y estados | Añadir en implementación |
| Mapa de flujo v3 | Las cuatro tarjetas de configuración truncan su descripción ("4 grupos y s…", "El estado de …") | Acortar el texto o ampliar la tarjeta |
| Mapa de flujo v3 | Las etiquetas de eyebrow están a 13px, bajo el piso de 14px | Subir a 14px |

La **Biblioteca de estados** quedó limpia: cero texto bajo 14px, ortografía corregida, y los siete
estados completos. Es la referencia que debe cumplir la implementación.

**Los anillos de foco y los `aria-live` no se pueden verificar en un mock estático.** La fuente
de verdad para esos dos es `tokens.css`, no la imagen de Stitch.

---

## 7. Decisiones tomadas

| Decisión | Motivo |
|---|---|
| Modo oscuro único, sin variante clara | El usuario eligió el dark fintech como base |
| Turquesa reservado para la IA, lila como acento | El violeta del estilo original colisionaba con el canal del solver |
| Escala 17px / 44px / AAA | Personas mayores: legibilidad por sobre densidad |
| Rejilla de 3 columnas en Docentes, no tabla densa | Escaneo rápido de quién está sobrecargado |
| Un día a la vez por debajo de 1024px | Una cuadrícula de 5 columnas no se lee a ese ancho |
| Eliminar el panel "Resumen" de Cursos | Duplicaba la franja de métricas y robaba 320px a la tabla |
| Sin vistas móviles | Es una herramienta de escritorio para coordinadores |

---

## 8. Orden de trabajo restante

| # | Paso | Estado | Desbloquea |
|---|---|---|---|
| 1 | **Importar: pasos 1, 2 y 4** (Subir, Mapear, Confirmar) | pendiente | fases 02 y 06 |
| 2 | **Enlaces de consulta** (solo lectura, sin login) | pendiente | fase 09 |
| 3 | **Defectos menores** de la sección 6 | pendiente | nada crítico |
| 4 | **Logo "Hourly"** — 3 propuestas entregadas | ✅ hecho | identidad de producto |

Después de la primera demo, no antes: comparación de versiones e historial de cambios.

---

## 9. Limpieza pendiente en Stitch

**No se puede mover ni borrar pantallas por MCP.** El servidor solo expone `delete_project`.
Reordenar y borrar es trabajo manual en la UI de Stitch. Lo que sigue es el manifiesto para
hacerlo rápido.

### Las 15 que se quedan

| # | Pantalla | ID |
|---|---|---|
| 1 | Inicio | `bdaa4d284f39498d9edc4416c85bc4ab` |
| 2 | Importar | `8d4785123bb64b4fa81f888f32d766cf` |
| 3 | Horario | `d501bbe30a804ad4a4d2ff4fcf963758` |
| 4 | Conflictos | `90ca9654e58944499cc6abe5ee61541a` |
| 5 | Docentes | `f0beab2f23fe430aa0b05f590c6dad31` |
| 6 | Recursos | `ea5dbf053d774179bb979be914d6d159` |
| 7 | Publicar | `fb6060ecf53b4cf48e7296786d971bd6` |
| 8 | Escenario ¿y si…? | `8a45319e905746f08973bf62b7999114` |
| 9 | Cursos | `9375e2225b0549d8bbf9714bd72263d0` |
| 10 | Reglas | `ca4c8ed5fcfb4466ba9e53f0651e3746` |
| 11 | Sistema de diseño | `0c9c102a12f54bd0bdc2e718e208ee49` |
| 12 | Biblioteca de estados | `d542d93107ce4c18b71104514f540f78` |
| 13 | Mapa de flujo v3 | `9a4c2abbbbfb45d295b3c35cedddaab1` |
| 14 | Identidad de marca | `7e231b4ba3f94c2397b6f9cd18215864` |
| 15 | Horario tablet 1024 | `3f9536c0aac04f8fa2090a452e3490b1` |

### Cómo ordenarlas en el canvas

Dos filas: **fila 1** las pantallas de la app (1 a 10 + 15), **fila 2** las hojas técnicas (11 a 14).

### Todo lo demás es duplicado y se borra

- `Entrada de Datos Curriculares` (las dos versiones claras)
- Las tres tarjetas sueltas `DESIGN.md`
- Las 9 pantallas del sistema claro anterior
- `Horario Maestro · Dark Fintech Edition` y `Variante Azul Institucional`
- Toda pantalla cuyo título empiece con `MALLA ·` que no esté en la tabla de arriba
- Las versiones intermedias de Inicio, Docentes, Conflictos, Sistema, Cursos, Reglas,
  Biblioteca de estados y Mapa de flujo
- Las 2 pantallas móviles descartadas

**Regla para identificarlas:** si el ID no está en la tabla de las 15, se borra.

> `list_screens` es inconsistente: reporta 21 títulos cuando el canvas tiene más. Guiarse por el
> título y el contenido visual, no por ese conteo.

### Renombrar: solo desde la UI de Stitch

Probado: **no existe herramienta MCP para renombrar**. `edit_screens` no edita el título en el
lugar — crea una pantalla nueva, o sea un duplicado más. Renombrar es hacer doble clic en el
título dentro de Stitch y escribir.

Convención para que el canvas se lea de un vistazo:

| Prefijo | Significado |
|---|---|
| `Hourly · {Pantalla}` | **Se usa.** Es una de las 15. |
| `DUPLICADO · {descripción}` | **Se borra.** Versión vieja, intermedia o de otro sistema. |

### Nombres objetivo de las 15 que se quedan

| ID | Nombre a ponerle |
|---|---|
| `bdaa4d284f39498d9edc4416c85bc4ab` | `Hourly · Inicio` |
| `8d4785123bb64b4fa81f888f32d766cf` | `Hourly · Importar` |
| `d501bbe30a804ad4a4d2ff4fcf963758` | `Hourly · Horario` |
| `90ca9654e58944499cc6abe5ee61541a` | `Hourly · Conflictos` |
| `f0beab2f23fe430aa0b05f590c6dad31` | `Hourly · Docentes` |
| `ea5dbf053d774179bb979be914d6d159` | `Hourly · Recursos` |
| `fb6060ecf53b4cf48e7296786d971bd6` | `Hourly · Publicar` |
| `8a45319e905746f08973bf62b7999114` | `Hourly · Escenario` |
| `9375e2225b0549d8bbf9714bd72263d0` | `Hourly · Cursos` |
| `ca4c8ed5fcfb4466ba9e53f0651e3746` | `Hourly · Reglas` |
| `0c9c102a12f54bd0bdc2e718e208ee49` | `Hourly · Sistema de diseño` |
| `d542d93107ce4c18b71104514f540f78` | `Hourly · Biblioteca de estados` |
| `9a4c2abbbbfb45d295b3c35cedddaab1` | `Hourly · Mapa de flujo` |
| `7e231b4ba3f94c2397b6f9cd18215864` | `Hourly · Identidad de marca` |
| `3f9536c0aac04f8fa2090a452e3490b1` | `Hourly · Horario tablet 1024` |

Al resto **no hace falta renombrarlo si lo vas a borrar**: sería trabajo doble. Renombrá solo
las 15. Si preferís no borrar nada todavía, entonces sí poné `DUPLICADO · ` delante de todo lo
demás para que el canvas se lea, pero el objetivo final es borrarlas.

### Falta un arreglo de contenido

Tres hojas técnicas todavía dicen "MALLA" **visible en el pie**: Sistema de diseño
("MALLA Core Engineering"), Biblioteca de estados ("MALLA UI Design System") y Mapa de flujo
("MALLA · Arquitectura de información v3"). Corregirlo requiere regenerar cada una, o sea +3
duplicados. Las 12 pantallas restantes solo llevan "MALLA" en el `<title>` del HTML, que es
invisible y se resuelve en una línea por ruta al implementar.
