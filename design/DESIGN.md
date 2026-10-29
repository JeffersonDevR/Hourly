> ⛔ **OBSOLETO como contrato de implementación.** Este documento describe el sistema
> **claro** v2 (canvas #F8FAFC) y el producto quedó en modo oscuro único. Los tokens
> vigentes son `design/stitch/tokens.css` y el contrato de diseño es
> `design/stitch/README.md`. Se conserva por la parte de reglas (17px / 44px / AAA),
> que sigue vigente y está repetida allí.

---
name: Academic Grid Matrix v2
product: MALLA · Horarios institucionales
colors:
  # ---- Surfaces ----
  canvas: '#F8FAFC'
  surface: '#FFFFFF'
  surface-sunken: '#F1F5F9'
  surface-raised: '#FFFFFF'
  border: '#E2E8F0'
  border-strong: '#CBD5E1'
  border-hairline: '#F1F5F9'
  # ---- Text ----
  text-primary: '#0F172A'
  text-secondary: '#475569'
  text-muted: '#64748B'
  text-disabled: '#94A3B8'
  text-inverse: '#F8FAFC'
  # ---- Interactive ----
  accent: '#0284C7'
  accent-text: '#0369A1'
  accent-strong: '#075985'
  accent-surface: '#F0F9FF'
  accent-ring: 'rgba(2, 132, 199, 0.35)'
  # ---- AI / solver only ----
  ai: '#4F46E5'
  ai-text: '#4338CA'
  ai-surface: '#EEF2FF'
  ai-border: '#C7D2FE'
  # ---- Semantic ----
  danger: '#DC2626'
  danger-text: '#B91C1C'
  danger-surface: '#FEF2F2'
  danger-border: '#FCA5A5'
  warning: '#D97706'
  warning-text: '#B45309'
  warning-surface: '#FFFBEB'
  warning-border: '#FCD34D'
  success: '#059669'
  success-text: '#047857'
  success-surface: '#ECFDF5'
  success-border: '#6EE7B7'
  info-surface: '#EFF6FF'
  info-text: '#1E40AF'
  info-border: '#BFDBFE'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 34px
    letterSpacing: -0.025em
  title-lg:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 26px
    letterSpacing: -0.02em
  title-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 22px
    letterSpacing: -0.01em
  title-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
    letterSpacing: -0.005em
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
    letterSpacing: '0'
  body-sm:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
    letterSpacing: '0'
  label-md:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: '0'
  label-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: '0'
  label-micro:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 14px
    letterSpacing: 0.04em
  data-mono:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '500'
    lineHeight: 18px
    letterSpacing: '0'
rounded:
  xs: 2px
  sm: 4px
  md: 6px
  lg: 8px
  xl: 12px
  full: 9999px
spacing:
  '0': 0px
  '1': 2px
  '2': 4px
  '3': 6px
  '4': 8px
  '5': 12px
  '6': 16px
  '7': 20px
  '8': 24px
  '9': 32px
  '10': 40px
  '11': 48px
---

> ⛔ **OBSOLETO.** Este documento describe el sistema **claro** v2 (12px base), reemplazado por
> el sistema oscuro accesible `Academic Grid Matrix · Dark Accessible` (17px base, AAA).
> Fuente de verdad vigente: `horarios-opencode-kit/design/stitch/README.md` y `tokens.css`.
> Se conserva solo como registro histórico.

# MALLA — Academic Grid Matrix v2

Institutional scheduling workspace for schools and colleges. Users are academic coordinators
(`coordinador académico`), department heads and heads of study. They are under high cognitive
load, they are not power users of design tools, and they make expensive mistakes when a
timetable is wrong. The interface must feel like a **master plan**, not a marketing site.

## 1. Product intent

MALLA takes five structured inputs and produces one conflict-free weekly timetable:

1. **Cursos** — grade levels (9, 10, 11) and their subcourses (9A, 9-1, 9°A — the institution defines the naming).
2. **Malla curricular** — weekly period quota per subject, per subcourse.
3. **Docentes** — teacher, subject competence, contracted weekly load, availability, absences.
4. **Espacios** — regular rooms plus special facilities (lab, court, workshop, library, auditorium) with capabilities and capacity.
5. **Calendario** — period structure, breaks, and dated exceptions (holidays, events).

The system detects overlaps across three dimensions — **cohort × teacher × room** — and offers
AI proposals to resolve them. **Every AI output must be reviewable, attributed and reversible.**

## 2. Non-negotiable design laws

These are acceptance criteria, not suggestions. A screen that violates one is wrong.

### LAW 1 — No horizontal page scroll. Ever.
- `overflow-x` is allowed **only** inside a declared scroll container: the timetable viewport, a data table, or a horizontally scrolling chip row.
- Never `body { overflow-x: hidden }` as a band-aid. Fix the container.
- Every flex or grid child that can hold text carries `min-width: 0`.
- Every declared column has an explicit width; `table-layout: fixed`.

### LAW 2 — Text never escapes its cell.
- One line of truncation (`text-overflow: ellipsis; white-space: nowrap`) + at most one `line-clamp-2` second line.
- Full value is always reachable: `title` attribute on the visible node, and the detail lives in the side panel.
- No cell grows in height because of its text. Row height is a token, not a consequence.

### LAW 3 — One primary action per screen.
Secondary actions are text buttons or ghost buttons. Tertiary lives in an overflow menu.
Never two filled buttons competing at the same visual weight.

### LAW 4 — Colour is never the only carrier of meaning.
Every semantic state ships with **four channels**: border style + icon glyph + text label + fill.
The single exception is a purely decorative category tint, which is always redundant with the subject name printed in the cell.

### LAW 5 — No generic-AI visual vocabulary.
Banned outright: violet-to-pink gradients, glassmorphism/blur panels, glowing borders,
decorative blobs, floating 3D shapes, emoji as icons, "✨" sparkles on AI features,
oversized centred hero blocks, `border-radius: 24px` on every surface, drop shadows on
resting cards, animated counters, and full-width gradient CTA banners inside the app.

Indigo (`#4F46E5`) is a **reserved channel**: it means "the solver proposed this".
It appears on nothing else, ever. That single rule is what keeps AI features legible
instead of decorative.

### LAW 6 — Density is a mode, not a compromise.
Grid row heights: `56px` comfortable (default) · `44px` compact · `68px` detailed.
The mode toggle is persisted per user. Text never drops below 12px in any mode.

## 3. Colour

Light mode only in v1. Semantic roles, not shades — a component references a role.

| Role | Value | Use |
|---|---|---|
| Canvas | `#F8FAFC` | App background, gutters, disabled slots |
| Surface | `#FFFFFF` | Cards, cells, panels |
| Sunken | `#F1F5F9` | Table headers, segmented control track, inset areas |
| Border | `#E2E8F0` | Structural dividers, cell edges |
| Border strong | `#CBD5E1` | Input borders, active dividers |
| Text primary | `#0F172A` | Headings, cell primary line |
| Text secondary | `#475569` | Supporting copy, table labels |
| Text muted | `#64748B` | Metadata, timestamps (4.76:1 — see §8) |
| Accent | `#0284C7` | Focus rings, selection fill, active indicators (**not** body text) |
| Accent text | `#0369A1` | Links and accent text — 5.93:1 |
| AI / solver | `#4F46E5` | Solver proposals only |

### 3.1 Meaning is carried by 4 channels

| State | Border | Icon | Text | Fill |
|---|---|---|---|---|
| Conflicto duro | `1.5px solid #DC2626` | `alert-octagon` | "Solapamiento" | `#FEF2F2` + 45° hatch |
| Advertencia | `1px solid #FCD34D` | `alert-triangle` | "Cerca del límite" | `#FFFBEB` |
| Válido | `1px solid #6EE7B7` | `check` | "Completo" | `#ECFDF5` |
| Propuesta IA | `1px dashed #4F46E5` | `sparkles` (outline, 14px) | "Propuesta del solver" | `#EEF2FF` |
| Sin asignar | `1px dashed #94A3B8` | none | — | `#FFFFFF` |

**Do not** use a green fill to mean "ok" on something the user must still act on, and never
print a red surface without a text label. A crimson cell with no words is an accessibility defect.

### 3.2 Subject categories (decorative, always redundant with the subject name)

| Category | Fill | Border | Text |
|---|---|---|---|
| Matemáticas / STEM | `#EFF6FF` | `#BFDBFE` | `#1E40AF` |
| Humanidades | `#F5F3FF` | `#DDD6FE` | `#5B21B6` |
| Ciencias naturales | `#FEF3C7` | `#FDE68A` | `#92400E` |
| Artes | `#FFF1F2` | `#FECDD3` | `#9F1239` |
| Educación física | `#ECFDF5` | `#A7F3D0` | `#065F46` |
| Electivas | `#F1F5F9` | `#CBD5E1` | `#334155` |

Category tints are **low-chroma and never the only differentiator**: the subject name is
always printed. Saturated rainbow coding of 12 subjects is forbidden — it defeats scanning.

## 4. Typography

Single family, `Inter`, with `font-variant-numeric: tabular-nums` **on every numeric element**
(period numbers, hours, counters, room codes). Non-negotiable: numbers that jitter are unreadable.

| Token | Size / LH | Weight | Use |
|---|---|---|---|
| `display-lg` | 28 / 34, −0.025em | 600 | Screen title |
| `title-lg` | 20 / 26 | 600 | Section title |
| `title-md` | 16 / 22 | 600 | Card title |
| `title-sm` | 14 / 20 | 600 | Cell subject name |
| `body-md` | 14 / 20 | 400 | Body copy, form values |
| `body-sm` | 13 / 18 | 400 | Dense table body, helper text |
| `label-md` | 13 / 16 | 500 | Field labels |
| `label-sm` | 12 / 16 | 500 | Metadata, room code, teacher initials |
| `label-micro` | 12 / 14, +0.04em | 600 | UPPERCASE badges only |
| `data-mono` | 13 / 18, tabular | 500 | Hours, counters, period ids |

**Minimum size is 12px.** 11px is retired: v1 used it for room codes and cohort badges, which
are content, not micro-labels. `display-lg` is the ceiling in application chrome — 32px+ only
on the read-only public timetable view.

## 5. Layout

```
┌──────┬────────────────────────────────────────────────────────────┐
│ rail │ header: institution · term · stage progress · publish       │
│ 56px ├──────────┬─────────────────────────────────────────────────┤
│      │ sidebar  │  content                                        │
│      │ 248px    │  max-width: none; padding: 24px                 │
│      │ (collap- │                                                 │
│      │  sible   │                                                 │
│      │  to 56)  │                                                 │
└──────┴──────────┴─────────────────────────────────────────────────┘
```

- **Rail 56px**: 7 destinations max, icon + tooltip, active state = 2px left accent bar + sunk fill.
- **Sidebar 248px**: contextual filters only (courses, teachers, rooms, filters). Collapses to 56px icon strip below 1280px.
- **Header 56px**: institution + term selector, stage breadcrumb, publish state. Sticky.
- **Content**: `padding: 24px`; the timetable may consume full remaining width. Never centre a data table in a max-width column.
- Breakpoints: `≥1600` full week + pinned inspector 380px · `1280–1599` week + inspector drawer · `1024–1279` sidebar collapses, 4 days visible with locked axes · `<1024` read-only + "abrir en escritorio" notice (no fake mobile scheduler).

### 5.1 Timetable grid containment

```
.viewport { overflow: auto; overscroll-behavior: contain; position: relative; }
thead th  { position: sticky; top: 0;    z-index: 20; background: #F1F5F9; }
.rowhead  { position: sticky; left: 0;   z-index: 10; background: #FFFFFF; }
.corner   { position: sticky; top: 0; left: 0; z-index: 30; }
```
- Column min-width `140px`; row header `180px`; both explicit.
- The scrollbar is the only affordance — never hide it. Add an edge fade only when scrollable.
- Cells clip content; nothing in a cell may increase its own width.

### 5.2 Empty and loading states
- Empty state: icon 24px, one sentence, one action. Max width 380px, left-aligned in its region. Never a full-viewport centred illustration.
- Loading: skeleton rows matching real row heights — the grid never collapses then jumps.
- Never `height: 100vh` on any component.

## 6. Components

**Buttons** — height 32px (default) / 36px (primary) / 28px (compact table action). Radius 6px. Padding 0 12px. Primary: `#0F172A` fill, white text. Secondary: white, 1px `#CBD5E1`. Ghost: transparent, text `#475569`. Destructive: white, 1px `#FCA5A5`, text `#B91C1C`; solid red only on the final irreversible confirm.

**Timetable cell** — radius 4px, 1px border, padding 4px 8px, fixed height from the density token. Line 1: subject name (truncate) + cohort badge. Line 2: room code · teacher initials. Hover raises to `0 1px 3px rgba(15,23,42,.08)` and reveals a 16px drag handle. Selected: 2px `#0284C7` inset ring. Conflict: red border + hatch + `alert-octagon` at top-right.

**Data table** — header `#F1F5F9`, `label-micro` uppercase, `position: sticky`. Rows 44px, hairline `#F1F5F9` separators, no vertical borders except the first-column divider. Numeric cells right-aligned and tabular. Row hover `#F8FAFC`. Row actions appear on hover **and on focus-within** (keyboard parity).

**Workload meter** — 6px track `#E2E8F0`, radius full. Fill `#0284C7` under quota, `#059669` at quota, `#DC2626` over. Always paired with tabular text `24 / 28 h`. Never a bare bar without the number.

**Inputs** — height 32px, 1px `#CBD5E1`, radius 6px, `body-sm`. Focus: 1px `#0284C7` + 2px `rgba(2,132,199,.35)` ring. Labels sit **above** the field, always visible — placeholder is never the label. Helper text below at `body-sm` `#64748B`. Error: 1px `#DC2626`, `alert-circle` 14px, message below in `#B91C1C`, plus `aria-describedby`.

**Segmented control** — track `#F1F5F9`, 2px inset, radius 6px, active segment white with `0 1px 2px rgba(15,23,42,.06)` and 1px `#E2E8F0`. Options: `Por curso` · `Por docente` · `Por espacio`.

**Conflict card** — left 3px `#DC2626` bar, title = the collision in one line, then two lines of evidence (which resources, which period), then actions: `Resolver` (primary, small) · `Ignorar` (ghost) · `Ver en el horario` (link). Never a modal-first flow for conflicts.

**AI proposal panel** — `#EEF2FF` surface, 1px dashed `#C7D2FE`, outline `sparkles` icon, heading "Propuesta del solver", then the concrete move as a before→after pair, a one-line rationale, a confidence chip, and `Aplicar` / `Descartar` / `Proponer otra`. Never a chat bubble. AI never auto-applies.

**Stage stepper** — horizontal, 9 stages, 24px numbered dots connected by 1px rules. States: done (filled `#0F172A`, check), current (ring `#0284C7`), pending (`#CBD5E1`), blocked (ring `#DC2626`). Labels `label-sm`, truncating to the stage number below 1280px.

**Badges** — `label-micro` uppercase, 2px radius, 2px/6px padding, filled tint + matching 1px border + 12px text. Never a pill for a table cell badge.

## 7. Accessibility contract — WCAG 2.2 AA from day one

Every screen ships meeting these. This is not a later pass.

**Perceivable**
- 1.4.3: body text ≥4.5:1; large (≥18.66px bold / 24px) ≥3:1. `text-muted` is allowed at 13px+ only.
- 1.4.11: meaningful UI boundaries and states ≥3:1. Decorative tint borders (`#BFDBFE` at 1.8:1) are permitted **only** where the subject name carries the meaning — that condition must hold on every cell.
- 1.4.1: four channels as defined in §3.1. A conflict is never "the red one".
- 1.4.4 / 1.4.10: usable at 200% zoom and at 320px content width without loss of content or function.
- 1.4.12: no fixed-height text containers; tolerate 1.5× line-height and 0.12em letter-spacing.

**Operable**
- 2.1.1: the grid is fully keyboard-operable. `role="grid"` + roving `tabindex="0"` on one cell; arrows move, `Enter` opens detail, `Esc` closes, `Ctrl/⌘+→` jumps a day.
- 2.4.7 / 2.4.11: `:focus-visible` → `outline: 2px solid #0369A1; outline-offset: 2px`. Never `outline: none` without a replacement. Focus must never be hidden behind the sticky header.
- 2.5.8: every target ≥24×24px; primary controls 36px tall. Consequence: the drag handle is 16px visual inside a 24px hit area.
- Skip link `Saltar al horario` as the first focusable element on every screen.
- Drag-and-drop always has a keyboard equivalent (move-to-slot dialog). 2.5.7 satisfied.

**Understandable**
- 3.3.1 / 3.3.3: errors name the field, state the cause and the fix, in text. `aria-describedby` wired. Never colour-only validation.
- 3.2.4: consistent nav and stage order across all setup screens.
- `<html lang="es">`.

**Robust**
- 1.3.1: the timetable is a real `<table>` with `<th scope="col">` for days and `<th scope="row">` for periods. If interactive, `role="grid"` on top of a `<table>` — never a div soup.
- 4.1.3: one `aria-live="polite"` region announcing conflict-count changes ("3 conflictos, 1 nuevo").
- 4.1.2: icon-only buttons need `aria-label`; icons are `aria-hidden="true"`.
- Motion: 120ms ease-out micro-transitions; `@media (prefers-reduced-motion: reduce)` disables transform/opacity animation and the hatch pulse. No pulsing red dots — they trigger discomfort and add no information.

### 7.1 Review checklist per screen
1. Tab through it end to end — is anything invisible when focused?
2. Grep the markup for `overflow-x` outside `.viewport`.
3. Grep for `outline: none`.
4. Every red/yellow/green state has words next to it.
5. Zoom to 200% — does any control disappear or clip?
6. Every icon-only control has an accessible name.
7. Every number uses tabular figures.
8. No hard-coded hex outside the token list.

## 8. Known margins

- `text-muted #64748B` on `canvas` is **4.55:1** — passes, but by 0.05. Do not lighten it. Do not use it below 13px.
- `accent #0284C7` is **4.10:1** on white: valid as ring, fill and border; **invalid as body text**. Use `accent-text #0369A1` (5.93:1) for any accent-coloured copy.
- Subject category borders sit at ~1.8:1. This is deliberate and only acceptable while §7's redundancy condition holds.
