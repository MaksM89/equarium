from fastapi import FastAPI
from src.authorization.routes import router
from src.logconf import LoggerMiddleware


def create_app() -> FastAPI:
    app = FastAPI()
    app.include_router(router)
    app.add_middleware(LoggerMiddleware)
    return app

app = create_app()