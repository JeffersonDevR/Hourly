---
description: Fase 6 — design system, layout y pantallas de configuración (desde los exports de Stitch)
---
Lee `design/stitch/` (HTML/CSS/imágenes exportados de Stitch) y extrae los tokens (colores, tipografía, radios, espaciado) a la config de Tailwind y variables CSS. No inventes otro estilo. La app se llama **Houry**: ese nombre va en el `<title>`, en la marca de la navegación lateral y en los metadatos de `package.json` (`"name": "houry-web"`).
Implementa con shadcn/ui: layout final (navegación lateral, barra global con semáforo + contador de conflictos + selector de escenario + guardado), Inicio con checklist de configuración y resumen, Importar (4 pasos: Subir, Mapear, Revisar, Confirmar, con corrección en línea), Cursos, Docentes (tarjetas con barra de carga y alerta de exceso), Recursos.
Todas las pantallas con estados vacío, cargando, error, éxito y conflicto; semáforo con icono + texto; foco visible y navegación por teclado.
Si falta una pantalla en `design/stitch/`, impleméntala con los mismos tokens y avisa al final.
Criterios: flujo importar → Inicio funcionando contra la API real con el Excel de demo; vitest de los componentes clave.
$ARGUMENTS
