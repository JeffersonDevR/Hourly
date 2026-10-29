---
description: Fase 6 — design system, layout y pantallas de configuración (desde los exports de Stitch)
---
Lee `design/stitch/` (HTML/CSS/imágenes exportados de Stitch) y extrae los tokens (colores, tipografía, radios, espaciado) a la config de Tailwind y variables CSS. No inventes otro estilo. El contrato de diseño es `design/stitch/README.md` (+ `design/stitch/tokens.css` para los tokens): ahí están el sistema, las 19 pantallas, las 5 reglas no negociables y los defectos ya medidos. `design/DESIGN.md` y `design/AUDIT.md` describen el sistema **claro** anterior y están marcados obsoletos: no se implementan, solo sirven de registro. La app se llama **Hourly**: ese nombre va en el `<title>`, en la marca de la navegación lateral y en los metadatos de `package.json` (`"name": "hourly-web"`).
Implementa con shadcn/ui: layout final (navegación lateral, barra global con semáforo + contador de conflictos + selector de escenario + guardado), Inicio con checklist de configuración y resumen, Importar (4 pasos: Subir, Mapear, Revisar, Confirmar, con corrección en línea), Cursos, Docentes (tarjetas con barra de carga y alerta de exceso), Recursos.
Todas las pantallas con estados vacío, cargando, error, éxito y conflicto; semáforo con icono + texto; foco visible y navegación por teclado.
Si falta una pantalla en `design/stitch/`, impleméntala con los mismos tokens y avisa al final.
Criterios: flujo importar → Inicio funcionando contra la API real con el Excel de demo; vitest de los componentes clave.
$ARGUMENTS
