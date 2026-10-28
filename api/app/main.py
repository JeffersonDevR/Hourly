from fastapi import FastAPI

from app.routers import estado, importaciones


def create_app() -> FastAPI:
    app = FastAPI(
        title="Hourly API",
        version="0.1.0",
        description="Generador y validador de horarios escolares sin solapamientos.",
    )
    app.include_router(estado.router, prefix="/api")
    app.include_router(importaciones.router, prefix="/api")
    return app


app = create_app()
