# MALLA · Diseño — documento único

**Este es el único lugar que necesitas.** Todo el diseño vive acá: sistema, pantallas,
decisiones, defectos abiertos y qué está obsoleto. Si algo no está enlazado desde este
archivo, no es fuente de verdad.

Proyecto Stitch: `3916526485862441063`
Design system: `assets/44af003a88054ae8806013207408fd99` — *Academic Grid Matrix · Dark Accessible*
Estado: **24 pantallas en el proyecto, 12 vigentes** (`list_screens`, 2026-10-29). Solo web, sin móvil. Piso de soporte 768px.

> **El flujo real del producto son 6 pasos:** Importar → Auditar → Generar → Resolver →
> Publicar → Probar. El paso 6 vuelve al 3 (bucle de escenario). Las pantallas de Cursos,
> Docentes, Recursos, Inicio y Reglas son configuración, no pasos del flujo.

---

## 1. Dónde está cada cosa

| Archivo | Qué contiene | Estado |
|---|---|---|
| `design/stitch/README.md` | Este documento. Índice y estado. | ✅ canónico |
| `design/stitch/tokens.css` | Variables CSS, mapeo a Tailwind, reglas responsive, regla global de foco | ✅ canónico |
| Stitch (proyecto arriba) | **24 pantallas reales: 12 vigentes + 12 a borrar** (§9) | ✅ canónico |
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

| # | Pantalla | ID real | Título actual en Stitch | Fase |
|---|---|---|---|---|
| 1 | **Inicio** | `bdaa4d284f39498d9edc4416c85bc4ab` | `Hourly · Inicio (Proporciones de Marca Corregidas)` | 06 ✅ |
| 2 | **Importar · paso 1** | `2141617ca7b7471794b555df7fc146f4` | `Hourly · Importar · Paso 1 Subir` | 06 ✅ |
| 3 | **Importar · paso 2** | `aa4c64548fad4551a3d9a2d41cc16475` | `Hourly · Importar · Paso 2 Mapear` | 06 ✅ |
| 4 | **Docentes** | `f0beab2f23fe430aa0b05f590c6dad31` | `Hourly · Docentes (Identidad de Marca Hourly.)` | 06 ✅ |
| 5 | **Escenario ¿y si…?** | `8a45319e905746f08973bf62b7999114` | `Hourly · Escenario ¿y si…?` | 09 |
| 6 | **Cursos** | `32c53217019847de8e33d1c21259d6b3` | `MALLA · Cursos (Tabla Corregida y Accesible)` | 06 ✅ |
| 7 | **Recursos** | `6b842346e84f453d9728e58ac1ca992a` | `MALLA · Recursos` | 06 ✅ |
| 8 | **Publicar** | `0ed42bb8282f465dbdaba504c3f134af` | `MALLA · Publicar el horario` | 09 |
| 9 | **Horario** (referencia) | `7b23b749a2fa4c18a6c4689a754c36d6` | `MALLA · Horario Accesible · Adultos Mayores` | 07 |
| 10 | **Referencia del sistema** | `e657c4e3f43e49f091f43ca0c8abdcc3` | `Hourly · Referencia del Sistema de Diseño (Logo SVG Corregido)` | — |
| 11 | **Biblioteca de estados** | `443d5b8393ab4198aebcb7183ea8c0f6` | `Hourly · Biblioteca de estados (Especificación Técnica)` | — |
| 12 | **Identidad de marca** | `7e231b4ba3f94c2397b6f9cd18215864` | `Hourly · Hoja de identidad de marca (3 propuestas)` | — |

**Corrección medida el 2026-10-29:** esta tabla antes listaba 19 pantallas y **11 de esos IDs no
existen** en el proyecto; se habían anotado como intención, no como export. Lo que sigue sin diseño:

| Falta | Consecuencia |
|---|---|
| **Conflictos** | fase 08 se construye desde los tokens y la Biblioteca de estados, no hay mock |
| **Reglas** | ídem |
| **Importar · pasos 3 y 4** | la implementación los cubre con la Biblioteca de estados |
| **Verificación**, **Mapa de flujo**, **Horario tablet** | no existen; el flujo está en §3 y en `docs/` |
| **Horario / Publicar / Cursos / Recursos** con nombre `Hourly` | existen, pero con el nombre viejo `MALLA ·` y contenido vigente |

Quedan 6 pantallas en Stitch que no son de la app (3 `DESIGN.md`, la hoja de logo suelto
`003e3cb8d33a45eeaddabd0e5b4fc403`, la Biblioteca de estados duplicada `d542d931…` y
`Horario Maestro · Dark Fintech Edition`). Ver §9.

**Marca:** se dibuja siempre con SVG o rectángulos en línea, nunca con `<img>` ni con un `<span>`
que simule el isotipo. En la implementación: `web/src/components/layout/Marca.tsx`.

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
  un máximo de 24. **La aritmética no cierra moviendo una sesión**: sobran 4 y Diego Herrera solo
  tiene 3 de margen (21 de 24). Lo que resuelve la versión es generar con docentes habilitados
  (el solver reparte Inglés: D4≈19, D6≈21). Ver `docs/DEMO.md` paso 3.
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

## 6. Defectos abiertos (medidos en el HTML, no de memoria)

Medición del 2026-10-29 descargando el HTML de las 12 vigentes y buscando las cinco reglas de §2
más los dos parches prohibidos. Reemplaza la tabla anterior, que citaba defectos de pantallas que
ya no existen.

| Defecto | Dónde | Medido | Arreglo |
|---|---|---|---|
| `overflow-x: hidden` | **7 de 12**: Importar 1 y 2, Escenario, Cursos, Publicar, Horario accesible y Horario interactivo | regla de §2 lo prohíbe | En la implementación: scroll en el contenedor (`.mh-scroll-x`). En los mocks solo se arregla regenerando |
| Texto a 13px | **Horario interactivo** (7 casos) y **Biblioteca de estados** (1) | piso de 14px | Los otros 10 están en 14px o más |
| `outline: none` | **Publicar** (1) | el resto en 0 | La regla global de `tokens.css` ya cubre la implementación |
| SVG sin `aria-hidden` | **Importar 2** (38 de 39) y **Biblioteca de estados** (8 de 8) | decorativos sin marcar | Marcar al implementar |
| Sin `aria-live` | Importar 1 y 2, Docentes, Cursos, Recursos, Publicar, Escenario, Referencia, Biblioteca | solo Inicio y los dos Horarios lo tienen | Añadir en implementación |
| `<title>` dice `MALLA` | **9 de 12** | cosmético, invisible | Una línea por ruta; en `web/index.html` ya dice `Hourly` |
| Isotipo con `<span>` | **Importar 2** | no es el logo | **Resuelto en la implementación** (`Marca.tsx`). En los mocks: regenerar |

Lo que **sí** cumplen las 12: cero fuentes por debajo del piso donde se pudo medir (salvo las dos
citadas), y la paleta coincide exactamente con `tokens.css` (`#08080A`, `#0F1012`, `#23252A`,
`#2A2C31`, `#F7F7F5`, `#C9C9CE`, `#A8A8AD`, `#C4B5FD`, `#FF9C93`).

**Los anillos de foco y los `aria-live` no se pueden verificar en un mock estático.** La fuente de
verdad para esos dos es `tokens.css`, no la imagen de Stitch.

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
| 1 | **Verificación** (compuerta antes de generar) | ✅ hecho | fase 07 |
| 2 | **Importar: pasos 1 y 2** | ✅ hecho (3 y 4 no tienen mock) | fases 02 y 06 |
| 3 | **Logo "Hourly"** en todas las pantallas | ✅ hecho | identidad de producto |
| 4 | **Historial de cambios** | **entra al MVP** | fase 09 (D-017) |
| 5 | **Enlaces de consulta** (solo lectura, sin login) | **fuera de alcance** (D-012, D-017) | nada |
| 6 | Comparación de versiones | **fuera de alcance** (D-012) | nada |

> **Enlaces de consulta:** descartados a propósito. Cuestan tabla + ruta + página pública y son la
> única pieza que puede fallar delante del jurado. No hace falta diseñarlos ni exportarlos.


---

## 9. Limpieza pendiente en Stitch

**No se puede mover ni borrar pantallas por MCP.** El servidor solo expone `delete_project`.
Reordenar y borrar es trabajo manual en la UI de Stitch. Lo que sigue es el manifiesto para
hacerlo rápido.

### Las 12 que se quedan

Verificado con `list_screens` el 2026-10-29: el proyecto tiene **24 pantallas**, no 19.

| # | ID | Título actual | Nombre objetivo |
|---|---|---|---|
| 1 | `bdaa4d284f39498d9edc4416c85bc4ab` | Hourly · Inicio (Proporciones de Marca Corregidas) | `Hourly · Inicio` |
| 2 | `2141617ca7b7471794b555df7fc146f4` | Hourly · Importar · Paso 1 Subir | `Hourly · Importar 1 Subir` |
| 3 | `aa4c64548fad4551a3d9a2d41cc16475` | Hourly · Importar · Paso 2 Mapear | `Hourly · Importar 2 Mapear` |
| 4 | `f0beab2f23fe430aa0b05f590c6dad31` | Hourly · Docentes (Identidad de Marca Hourly.) | `Hourly · Docentes` |
| 5 | `8a45319e905746f08973bf62b7999114` | Hourly · Escenario ¿y si…? | `Hourly · Escenario` |
| 6 | `32c53217019847de8e33d1c21259d6b3` | MALLA · Cursos (Tabla Corregida y Accesible) | `Hourly · Cursos` |
| 7 | `6b842346e84f453d9728e58ac1ca992a` | MALLA · Recursos | `Hourly · Recursos` |
| 8 | `0ed42bb8282f465dbdaba504c3f134af` | MALLA · Publicar el horario | `Hourly · Publicar` |
| 9 | `7b23b749a2fa4c18a6c4689a754c36d6` | MALLA · Horario Accesible · Adultos Mayores | `Hourly · Horario` |
| 10 | `e657c4e3f43e49f091f43ca0c8abdcc3` | Hourly · Referencia del Sistema de Diseño (Logo SVG Corregido) | `Hourly · Sistema de diseño` |
| 11 | `443d5b8393ab4198aebcb7183ea8c0f6` | Hourly · Biblioteca de estados (Especificación Técnica) | `Hourly · Biblioteca de estados` |
| 12 | `7e231b4ba3f94c2397b6f9cd18215864` | Hourly · Hoja de identidad de marca (3 propuestas) | `Hourly · Identidad de marca` |

### Las 12 que se borran

| ID | Título | Por qué |
|---|---|---|
| `0bdc6a7fa4494bd1bea4b9c3d02a70a0` | Hourly · Inicio (Identidad Concepto C) | versión anterior de Inicio |
| `66cabaaeb6a84374a5e95dea8687935d` | MALLA · Cursos | duplicado sin la corrección de tabla |
| `57906a9ad1cb48d1a49c8fc105ac47d8` | MALLA · Horario Accesible Interactivo y Animado | segunda variante de Horario; además rompe el piso de 14px |
| `b6587b6aacbb4de88666628b1eea424e` | MALLA · Referencia del Sistema de Diseño | reemplazada por la de logo SVG corregido |
| `d542d93107ce4c18b71104514f540f78` | Hourly · Biblioteca de estados (Marca Hourly.) | duplicado de la Especificación Técnica |
| `003e3cb8d33a45eeaddabd0e5b4fc403` | Hourly Logo - Opción C | la marca elegida ya vive en Identidad de marca |
| `db508de1d89e4df68a5077b489b23761` | Hourly · Enlaces de consulta | **fuera de alcance** (D-012): no se implementa |
| `8c8608d453884135b37a2942fa9e5281` | Horario Maestro · Dark Fintech Edition | exploración previa, no es el sistema vigente |
| `19e5b4731d6e49b5a30b29dae1927913` | DUPLICADO · Entrada de datos (sistema claro v1) | sistema claro descartado |
| `530309100493758765` | DESIGN.md | documento subido, no es una pantalla |
| `4971119891102610473` | DESIGN.md | ídem |
| `8928937375730533779` | DESIGN.md | ídem |

**Regla:** si el ID no está en la tabla de las 12, se borra. `list_screens` hoy devuelve 24
títulos coherentes con el canvas (la versión anterior de este README decía 21 y no cuadraba).

### Renombrar y editar: solo desde la UI de Stitch

Probado el 2026-10-29 con `edit_screens` sobre Inicio, dos veces (prompt en prosa y reemplazo
HTML literal con `FIND`/`REPLACE`): **no escribe nada**. Devuelve un texto diciendo que aplicó el
cambio, y el HTML de la pantalla queda idéntico byte por byte, sin pantalla nueva y sin crecer el
canvas. Es una herramienta de chat que reporta éxito falso.

Consecuencias: por MCP no se puede renombrar, reordenar, borrar una pantalla ni editar su markup.
Lo único que escribe es `generate_screen_from_text` (crea pantallas nuevas) y
`apply_design_system` (solo colores y tipografía). Renombrar y borrar es doble clic en Stitch.

Convención para que el canvas se lea de un vistazo:

| Prefijo | Significado |
|---|---|
| `Hourly · {Pantalla}` | **Se usa.** Es una de las 12. |
| `DUPLICADO · {descripción}` | **Se borra.** Versión vieja, intermedia o de otro sistema. |

### Estado de la marca en las pantallas

Medido: **la marca es SVG en línea en 11 de las 12**; solo `Importar · Paso 2` sigue con un `<span>`
que simula el isotipo. El arreglo vive en la implementación (`Marca.tsx`); los mocks se corrigen
regenerando.

Nunca `<img>`: en Sistema de diseño y Biblioteca de estados el modelo la intentó con una imagen
externa y quedó un icono de imagen rota.

## 10. Estado de la implementación (`web/`)

Registro de qué del diseño ya está en código. La fuente sigue siendo `tokens.css`; esto solo dice
dónde se aplicó y qué se desvió a propósito.

### Aplicado en la fase 6

| Pieza del diseño | Dónde vive | Nota |
|---|---|---|
| Tokens (color, tipografía, radios, foco global) | `web/tailwind.config.ts` + `web/src/index.css` importa `tokens.css` | Mapeo 1:1, dark-only |
| Marca concepto C | `web/src/components/layout/Marca.tsx` | Geometría de `logo-opcion-c.svg`, verticales en `currentColor` + lila + crema |
| Barra lateral de 88px con lockup vertical | `web/src/components/layout/Sidebar.tsx` | Usa `w-[var(--mh-rail-width)]`; 72px por debajo de 1280 lo resuelve el token |
| Barra superior: marca 24px + breadcrumb | `web/src/components/layout/TopBar.tsx` | Nunca el wordmark arriba |
| Semáforo, contador de conflictos, escenario | `TopBar` | Escenario en **solo lectura**: no hay endpoint para cambiar el de una versión existente (fase 9) |
| Inicio: semáforo + resumen + checklist de 4 pasos | `web/src/pages/Inicio.tsx` | El diseño pedía 5; el 5.º era "Probar escenario", que es fase 9 |
| Importar: 4 pasos con corrección en línea | `web/src/pages/Importar.tsx` | Pasos 1, 2, 3 y 4 en una sola ruta con estado |
| Cursos | `web/src/pages/Cursos.tsx` | Sin panel "Resumen" (decisión §7) |
| Docentes: tarjetas con barra de carga y exceso | `web/src/pages/Docentes.tsx` | La barra compara sesiones colocadas contra `max_sesiones_semana` |
| Recursos agrupados por tipo | `web/src/pages/Recursos.tsx` | Aula titular visible, el resto "Compartido" |
| Estados vacío / cargando / error / sin permiso de color | `web/src/components/estados.tsx` | Icono + palabra siempre; `role="status"` y `role="alert"` |

### Desviaciones documentadas

1. **Cursos, Reglas, Escenario y Ajustes siguen en la barra lateral**, en un grupo "Configuración" más chico. El
   diseño dice que son secundarias y se llegan desde Inicio y Conflictos, pero `/reglas` no tendría
   ningún camino hasta la fase 8. Cuando exista el enlace desde Conflictos, se sacan del rail. La etiqueta de navegación de `/configuracion` es **"Ajustes"** (13 caracteres no entran en el rail sin envolver; el título de la pantalla sigue siendo "Configuración").
2. **Checklist de Inicio con 4 pasos, no 5.** "Probar el escenario" depende del solver de escenarios
   (fase 9); mostrarlo ahora sería un paso que no lleva a ningún lado.
3. **Sin chip de "guardado".** Cada mutación es una request que commitea o falla; el estado de la
   versión (`borrador` / `publicado`) ya lo comunica. Un indicador de guardado global necesitaría
   estado compartido que hoy no existe.
4. ~~Ancho de la barra lateral sin verificar.~~ **Verificado y corregido dos veces.** A 88px
   "Configuración" no entra: envolverla con `overflow-wrap: anywhere` partía la palabra por la mitad
   ("Configu-ración"), que es peor que cortarla. El rail subió a **120px** (≥1280) y **100px** (≤1279)
   en `tokens.css`; así la etiqueta más larga entra entera a 14px. Por debajo, `hyphens: auto` (el
   documento ya está en `lang="es"`) hace un corte ortográfico, no arbitrario.
   El shell pasó a alto fijo con scroll solo en el `main`, que era el otro síntoma ("el scroll solo
   funciona en ciertas áreas").
   **De paso:** la escala tipográfica responsive de §5 (17px→16px, h1 32px→28px bajo 1280) existía en
   `tokens.css` como shorthand `--mh-body`/`--mh-h1` que Tailwind no podía consumir. Ahora son
   `--mh-size-body` y `--mh-size-h1`, usadas por `tailwind.config.ts`. Era la causa del "se ve
   regrande" en pantallas chicas.
5. ~~Pendiente del §5~~ **Implementado:** por debajo de 1024px la cuadrícula muestra **un día a la
   vez** con selector de día, y por debajo de 768 aparece un **aviso de tamaño** en vez de un layout
   comprimido. Ver `useMediaQuery` en `web/src/lib/media.ts`.

**Nota de mantenimiento:** los breakpoints del diseño ahora viven en dos lugares que tienen que
moverse juntos — `tokens.css` (media queries) y `web/src/lib/media.ts` (las mismas consultas en JS
para lo que no se puede resolver con CSS, como dejar de renderizar columnas).

---

## 11. Deriva entre Stitch y `tokens.css` (medida)

Tres inconsistencias reales del proyecto en Stitch, verificadas vía MCP el 2026-10-29. Las tres
importan porque cualquier pantalla nueva que se genere hereda la primera.

**1. El design system por defecto del proyecto es CLARO.**
`list_projects` devuelve `colorMode: LIGHT` para `3916526485862441063`. Las pantallas son oscuras,
pero el default no. El oscuro es un asset aparte y hay que aplicarlo explícitamente:

| Asset | Modo | Surface | Tertiary |
|---|---|---|---|
| `assets/132518d6ea404090a6b99af84dcf4973` | LIGHT | `#FFFFFF` | `#4F46E5` |
| **`assets/44af003a88054ae8806013207408fd99`** | **DARK** | **`#191A1D`** | **`#5EEAD4`** |
| `assets/b7b90aed8ada46fc9596a9728c01c9e7` | LIGHT | `#FBF9F9` | `#000000` |

**2. El design system oscuro no coincide con nuestro acento.** Su `tertiary` es `#5EEAD4` (turquesa)
y su surface `#191A1D` sí coincide con `--mh-surface`. Nosotros usamos **lila `#C4B5FD`** como
acento y **reservamos el turquesa para la IA** (§2 y §7). Consecuencia concreta: **aplicar
`apply_design_system` sobre una pantalla existente repinta el acento de lila a turquesa** y rompe la
regla de que el turquesa solo significa "esto lo propuso el asistente". No se aplica nunca sobre una
pantalla que ya está bien.

**3. `tokens.css` es el único contrato de color.** El HTML de las 12 vigentes coincide exactamente
con sus valores; el design system de Stitch no. Si hay que elegir, gana `tokens.css`.

### Cómo generar una pantalla nueva sin repetir los defectos

1. `generate_screen_from_text` con el prompt que incluya, textual: *fondo `#08080A`, superficie
   `#191A1D`, acento lila `#C4B5FD`, turquesa `#5EEAD4` solo para propuestas de IA, texto 17px
   mínimo 14px, objetivos 44px, `outline` visible, `overflow-x` nunca en `hidden`*.
2. **No** correr `apply_design_system` después: pisa el acento (punto 2).
3. Medir el HTML con el mismo método de §6 antes de aceptarla: `text-[13px]`, `outline: none`,
   `overflow-x: hidden`, `aria-hidden` en los SVG decorativos.
