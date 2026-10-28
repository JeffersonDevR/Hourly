> ⛔ **OBSOLETO.** Esta auditoría corresponde a las pantallas del sistema **claro** anterior,
> que ya no están en el producto. La auditoría vigente está resumida en la sección 6 de
> `horarios-opencode-kit/design/stitch/README.md`.
> Se conserva solo como registro histórico del método de medición.

# MALLA — Auditoría de accesibilidad y desbordes

**Sistema:** Academic Grid Matrix v2 · `assets/132518d6ea404090a6b99af84dcf4973`
**Proyecto:** `projects/3916526485862441063`
**Fecha:** 2026-10-28
**Método:** inspección estática del HTML generado (11 pantallas) + inspección visual de 5.
**Alcance:** WCAG 2.2 AA desde el día uno, más las leyes de layout de `design/DESIGN.md`.

---

## 1. Resumen

| Métrica | Resultado |
|---|---|
| Pantallas generadas | 11 |
| Pantallas inspeccionadas visualmente | 5 de 11 |
| Defectos de recorte (contenido inalcanzable) | **3** — todos confirmados en imagen |
| `outline: none` / `outline-none` | 4 pantallas afectadas, 33 ocurrencias |
| Reglas `:focus-visible` | **0 en las 11 pantallas** |
| Texto por debajo de 12px | 9 de 11 pantallas (11px, y hasta 9px) |
| Emoji | 0 ✅ |
| `backdrop-filter` / glassmorphism | 0 ✅ |
| Degradados decorativos | 0 — los 3 detectados son legítimos ✅ |
| Iconos SVG decorativos sin `aria-hidden` | 3 pantallas (23 iconos expuestos) |

Lo que sí salió bien y es la base del sistema: cero emoji, cero glassmorphism, cero degradados
decorativos, truncado con `truncate` presente en todas las tablas (6–43 usos por pantalla),
`tabular-nums` aplicado, y un solo canal índigo reservado para el solver.

---

## 2. Defectos de recorte — severidad ALTA

Los tres son el mismo error estructural: **el contenedor recorta en vez de desplazar**.
No hay `overflow: auto` ni barra visible, así que el contenido simplemente desaparece.
Es exactamente el fallo que la Ley 1 de `DESIGN.md` prohíbe.

### 2.1 Malla curricular — columnas 11A y 11B inalcanzables

La tabla se corta contra el panel derecho "Cobertura de la malla". Se ven cinco de los siete
subcursos. **11A y 11B no se pueden ver ni editar**, y 11B es justo el subcurso donde está el
conflicto que la pantalla reporta.

- Auditoría estática: `overflow-x-auto` = 0 ⇒ no existe contenedor de desplazamiento.
- Corrección: contenedor `overflow-x-auto` con `overscroll-behavior: contain` y barra visible;
  `table-layout: fixed` con Asignatura 200px sticky + Área 92px + 7 columnas de 52px + Total 60px
  = 716px. El scroll queda como red de seguridad, no como solución.
- Secundario: la columna Área trunca "Humanidad..." — usar "Human." y `min-width:0`.

### 2.2 Mapa de flujo — faltan dos etapas de la fase 1

La fase 1 desborda el ancho: el nodo 04 "Docentes" queda cortado y **05 Espacios y 06 Verificación
no aparecen**. El mapa documenta 4 de las 9 etapas.

- Corrección: fase 1 en dos filas de tres nodos (01–03 arriba, 04–06 abajo) con conectores
  ortogonales; cada nodo de 1fr con `min-width:0` y truncado.
- Adicional: el pie afirmaba **"WCAG 2.2 AA Compliant"**, lo cual no es cierto en este estado.
  Reemplazar por "Contraste verificado AA en tokens de texto".

### 2.3 Verificación — cuarto bloqueo cortado por el pie

La lista de bloqueos no desplaza: la cuarta tarjeta (Educación Física / cancha) queda partida
contra la barra inferior y su contenido es inalcanzable.

- Corrección: región con `max-height` calculada + `overflow-y-auto`, sub-encabezado "Bloqueos"
  fijo, panel "Qué sigue" sticky e independiente.

> `edit_screens` devolvió éxito pero **no aplicó ninguno de los tres arreglos**: el HTML quedó
> byte a byte idéntico incluso 30 s después. Hay que rehacerlo a mano o regenerar la pantalla.

---

## 3. Accesibilidad — hallazgos medidos

### 3.1 Foco (WCAG 2.4.7 / 2.4.11) — CRÍTICO

`focus-visible` = 0 en las 11 pantallas. Además hay `outline-none` en Conflictos (22),
Publicar (5), Referencia del sistema (4), Verificación (3) y Malla (1).

Ningún control tiene foco visible garantizado. En un producto que se opera con teclado sobre una
cuadrícula, esto es el defecto más grave de la lista después de los recortes.

Regla a aplicar en todos los interactivos:
```
:focus-visible { outline: 2px solid #0369A1; outline-offset: 2px; border-radius: 4px; }
```
Y nunca `outline: none` sin sustituto.

### 3.2 Tamaño mínimo de texto — 9 de 11 pantallas

Se usa `text-[11px]`, y en la Referencia del sistema también `text-[10px]` y `text-[9px]`.
Contradice la regla de 12px mínimos de `DESIGN.md` §4. La v1 usaba 11px para códigos de aula y
badges de cohorte, que son contenido, no micro-etiquetas: por eso se retiró.

Corrección: elevar todo a `text-xs` (12px) como mínimo. Si algo no entra a 12px, el problema es el
ancho de la columna, no el tamaño de la letra.

### 3.3 Iconos decorativos expuestos a lectores de pantalla (WCAG 4.1.2)

| Pantalla | SVG totales | Con `aria-hidden` |
|---|---|---|
| Mapa de flujo | 23 | 13 → **10 expuestos** |
| Docentes | 26 | 15 → **11 expuestos** |
| Espacios | 51 | 49 → 2 expuestos |
| Resto (8) | — | todos correctos ✅ |

Añadir `aria-hidden="true"` a todo icono dentro de un control que ya tiene nombre accesible.

### 3.4 `aria-live` insuficiente (WCAG 4.1.3)

Solo Verificación y Horario lo declaran. Falta en **Conflictos**, que es precisamente donde cambia
el conteo de solapamientos al aplicar una propuesta. Añadir una región `aria-live="polite"` que
anuncie "3 conflictos, 1 resuelto".

### 3.5 Ancho mínimo fijo — trampa de desborde

`min-w-[1280px]` en Configuración, Cursos y Docentes. Cualquier viewport menor a 1280 produce scroll
horizontal de página. Sustituir por `min-width: 0` en los hijos flexibles y anchos explícitos solo
en columnas de tabla.

### 3.6 `overflow-x: hidden` en `body` — Espacios

Confirmado en el `<style>` de la pantalla de Espacios. Es el antipatrón que la Ley 1 nombra
explícitamente: enmascara el desborde en lugar de resolverlo. Eliminar.

### 3.7 Lo que sí cumple

- **1.4.1** Los estados semánticos usan borde + icono + palabra + relleno, no color solo.
  Las celdas de solapamiento en Horario muestran icono, la palabra "Solapamiento" y trama.
- **1.3.1** Horario es un `<table role="grid">` real con `th scope="row"` y `scope="col"` (17 `scope`).
- **1.4.3 / 1.4.11** Los pares del sistema v2 pasan AA; `#0284C7` no se usa como texto.
- **2.5.8** Los controles visibles respetan 24px mínimo.

---

## 4. Deriva de datos entre pantallas

Contradicciones que rompen la credibilidad del prototipo:

| Dato | Valores encontrados |
|---|---|
| Docentes | 18 (Docentes) · 24 (Verificación, Mapa) |
| Subcursos | 7 (Cursos, Malla) · 12 "subsecciones" (Mapa) |
| Asignaturas | 10 (Malla) · 18 "materias" (Mapa) |
| Recesos | "Descanso" en el texto, "Receso" en la cabecera de fila |

Fijar una única fuente de verdad antes de generar variantes.

## 5. Deriva de color

Menor, pero existe: `#1E293B` (slate-800) aparece en 6 pantallas donde el token es `#0F172A`.
Malla inventa colores de categoría fuera del sistema: `#7C3AED`, `#0D9488`, `#E11D48`.
Reemplazar por las categorías de `DESIGN.md` §3.2.

---

## 6. Checklist para la siguiente pasada

1. Cero recortes: cada región con contenido excedente declara `overflow` propio y barra visible.
2. `:focus-visible` en todo interactivo; cero `outline-none` sin sustituto.
3. Nada por debajo de 12px.
4. Todo icono decorativo con `aria-hidden="true"`.
5. `aria-live` en Confllictos y en cualquier contador que cambie.
6. Cero `min-w-[NNNpx]` de página; cero `overflow-x: hidden` en `body`.
7. Un solo juego de cifras compartido por todas las pantallas.
8. Revisar a 200% de zoom y a 320px de ancho de contenido.
