---
description: Fase 10 — pulido de demo, datos semilla, prueba E2E y README
---
Prepara la demo de 3 minutos descrita en docs/DEMO.md:
- `.\demo.ps1` deja el estado del pitch PRE-CARGADO y repetible (D-007): resetea la DB, importa el Excel, resuelve, y deja un conflicto abierto, una propuesta válida y un ejemplo de regla en lenguaje natural. Ese sembrado se agrega a `demo.ps1` en esta fase; hasta acá el script solo levanta los servidores. La importación en vivo es un flujo aparte, nunca el primer paso del guion.
- Prueba E2E (Playwright) del guion completo.
- Revisa estados vacíos/errores, textos en español y que ninguna pantalla dependa solo del color.
- Escribe README.md (setup en 5 comandos, variables de entorno, arquitectura en un diagrama Mermaid).
- Ejecuta el subagente `revisor` y corrige lo crítico.
Criterios: el guion corre sin intervención tres veces seguidas; `uv run --directory api pytest` verde.
$ARGUMENTS
