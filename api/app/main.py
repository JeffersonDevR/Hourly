from fastapi import FastAPI

from app.routers import estado


def create_app() -> FastAPI:
    app = FastAPI(
        title="Houry API",
        version="0.1.0",
        description="Generador y validador de horarios escolares sin solapamientos.",
    )
    app.include_router(estado.router, prefix="/api")
    return app


app = create_app()
