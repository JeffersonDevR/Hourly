# DEMO.md — guion de 3 minutos

Pitch: *"No empieces de cero: partimos del horario que ya tienes y en segundos lo auditamos, lo corregimos y lo dejamos listo para publicar."*

## Antes de empezar

```
.\demo.ps1
```

Resetea la base, importa `data/Datos_prueba_Gnosoft.xlsx`, genera el horario con docentes
habilitados y **deja 2 sesiones sin colocar a propósito** (D-007). Es repetible: correrlo dos veces
da el mismo estado. La importación en vivo es un flujo aparte y **nunca** es el primer paso.

Estado que deja: **118 de 120 sesiones**, semáforo en ámbar por 2 `MALLA_INCUMPLIDA` (advertencia),
**cero errores**. El horario ya es publicable.

## El guion

1. **Abrir en Inicio.** Checklist con los 4 pasos y el resumen: 4 cursos, 6 docentes, 16 recursos,
   40 asignaciones. Decir que partimos del Excel que la escuela ya usa.

2. **Auditar.** Ir a **Horario**: la grilla está casi llena, semáforo ámbar y el panel **"Por
   colocar"** tiene 2 pendientes. Arrastrar una a una celda verde (las bloqueadas muestran el
   motivo con icono y texto) → el semáforo se recalcula solo. Eso es la validación en vivo.

3. **El caso que hace ruido: D4.** En **Horario**, generar con **"Solo principales"** → `INFACTIBLE`
   y el motivo queda explicado: *"D4 (Carlos Peña): demanda 28 sesiones > máximo 24"*. Después
   volver a **"Habilitados"** y generar → verde, 120 sesiones.
   > **No prometer** que "mover una sesión de Inglés a D6" lo arregla: D4 sobran 4 y D6 tiene 3 de
   > margen. Lo que resuelve la versión es el reparto del solver (D4≈19, D6≈21).

4. **Publicar y exportar.** En **Publicar**: sin errores, publicar, y descargar **Excel** y **PDF**
   (por curso, por docente, por aula o general).

5. **Escenario "¿y si D2 no viene el martes?"** En **Escenario**: "Ver impacto" (1 sesión afectada,
   el solver re-planifica, 0 conflictos) → **Aplicar** → el martes de D2 queda vacío y el semáforo
   sigue en verde. **Cierre.**

6. **Importación en vivo.** Solo si sobra tiempo o lo piden: `.\demo.ps1 -SinSemilla`, subir el
   Excel, revisar advertencias, corregir una celda en línea y confirmar. Es idempotente: reimportar
   no duplica (D-009).

## Dónde se muestra la IA

En **Conflictos**, con un conflicto de sesión (por ejemplo D1 bloqueado el viernes B6): "Proponer
solución" corre primero la reparación determinista y, si hace falta, el asistente. La propuesta se
simula y se valida antes de mostrarse; aceptar deja el conflicto resuelto.

En **Reglas**, escribir *"D1 no puede los martes"* → la tarjeta se llena sola (parser determinista,
sin red) y recién al **Confirmar** se escribe en la disponibilidad base.

## Plan B

- **Sin red o sin API key:** todo funciona. `/api/estado` dice `ai_disponible=false`, las propuestas
  de IA caen a la alerta determinista de `diagnosticar_carga` y `/reglas` usa el parser local.
- **Si el asistente falla en vivo:** `CassetteProvider` replaya la última respuesta grabada para
  interpretar reglas (`api/app/ai/cassettes/`).
- **Si el solver tarda:** la fase 1 de CP-SAT encuentra un plan válido en 0.3–0.6 s; la mejora corre
  con presupuesto determinista (D-020).
