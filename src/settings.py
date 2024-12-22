from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings
from sqlalchemy import URL


class Settings(BaseSettings):
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str

    SECRET_KEY: str
    ALGORITHM: Literal['HS256'] = Field(default='HS256')
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(ge=0, default=60 * 24)  # one day

    RECORDS_IN_PAGE: int = 20

    @property
    def db_url(self) -> URL:
        return URL.create(
            drivername='postgresql+asyncpg',
            host=self.DB_HOST,
            port=self.DB_PORT,
            username=self.DB_USER,
            password=self.DB_PASSWORD,
            database=self.DB_NAME
        )

settings = Settings()
