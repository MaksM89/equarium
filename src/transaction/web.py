from fastapi import FastAPI

from src.logconf import LoggerMiddleware
from src.transaction.routes import router


def create_app() -> FastAPI:
    app = FastAPI()
    app.include_router(router)
    app.add_middleware(LoggerMiddleware)
    return app

app = create_app()