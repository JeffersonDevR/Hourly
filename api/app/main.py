from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.routers import catalogos, estado, horarios, importaciones, reglas


async def _error_http(_peticion: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Formato único de error de la API: `{codigo, mensaje}` en vez de `{detail}`."""
    detalle = exc.detail
    cuerpo = detalle if isinstance(detalle, dict) else {"codigo": "ERROR", "mensaje": str(detalle)}
    return JSONResponse(
        status_code=exc.status_code, content=cuerpo, headers=getattr(exc, "headers", None)
    )


def create_app() -> FastAPI:
    app = FastAPI(
        title="Hourly API",
        version="0.1.0",
        description="Generador y validador de horarios escolares sin solapamientos.",
    )
    app.add_exception_handler(StarletteHTTPException, _error_http)
    app.include_router(estado.router, prefix="/api")
    app.include_router(importaciones.router, prefix="/api")
    app.include_router(catalogos.router, prefix="/api")
    app.include_router(horarios.router, prefix="/api")
    app.include_router(reglas.router, prefix="/api")
    return app


app = create_app()
