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
| 1 | **Inicio** | `43497a3b095944df841218a3c79afdc7` | Estado del horario + checklist de 5 pasos | 06 |
| 2 | **Importar** | `8cc9281ae6114d0f837f455e13385a84` | Paso 3 de 4: revisar errores y avisos del Excel | 06 |
| 3 | **Horario** | `7b23b749a2fa4c18a6c4689a754c36d6` | Cuadrícula semanal + panel "Por colocar" | 07 |
| 4 | **Conflictos** | `fa9a3e874529479ca942e781368082ab` | Un conflicto a la vez, con propuesta del asistente | 08 |
| 5 | **Docentes** | `9c55c3e23b9c412aadef7fa51f28277b` | Tarjetas con barra de carga y alerta de exceso | 06 |
| 6 | **Recursos** | `6b842346e84f453d9728e58ac1ca992a` | Aulas y espacios especiales | 06 |
| 7 | **Publicar** | `0ed42bb8282f465dbdaba504c3f134af` | Validación, versiones y exportación | 09 |
| 8 | **Escenario ¿y si…?** | `dd498073fb694ef78f8e1a039344d990` | Simulación de ausencia con impacto antes de aplicar | 09 |
| 9 | **Cursos** | `96ae8cc502a049abaca8a6f8a8869723` | Los 4 grupos con su aula titular y estado | 06 |
| 10 | **Reglas** | `0cd0f3ea065f40d4a24d3571b8eef135` | Lenguaje natural → regla interpretada | 08 |
| 11 | **Sistema de diseño** | `3779d88030b2417ab61e776f8ee2aede` | Hoja de referencia: color, tipografía, botones, estados | — |
| 12 | **Biblioteca de estados** | `d97b1c1dec5145f5923a55043ff3b1b4` | Vacío, cargando, error, conflicto, éxito, IA no disponible, trabajando | — |
| 13 | **Mapa de flujo v3** | `19e7b5cfb9ff492282d376ea3d42c6de` | Los 6 pasos reales + las pantallas de configuración | — |
| 14 | **Identidad de marca** | `7e231b4ba3f94c2397b6f9cd18215864` | Tres propuestas de logo para "Hourly" | — |

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

No se puede borrar pantallas por MCP (solo `delete_project`). Eliminar a mano:

- `Entrada de Datos Curriculares` (×2 versiones claras)
- Las dos tarjetas sueltas `DESIGN.md`
- Las 9 pantallas del sistema claro anterior
- `Horario Maestro · Dark Fintech Edition` y `Variante Azul Institucional`
- Las versiones **originales** de Inicio, Docentes, Conflictos, Sistema, Cursos y Reglas que fueron reemplazadas por sus correcciones
- Las 2 pantallas móviles descartadas

Conservar solo las 12 de la sección 3.
