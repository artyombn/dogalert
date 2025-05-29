import logging
import os
from pathlib import Path

from aio_pika import connect_robust
from aio_pika.abc import AbstractRobustConnection
from faker import Faker
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent

log = logging.getLogger(__name__)

class Settings(BaseSettings):
    APP_NAME: str
    DOCKER: bool
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST_LOCAL: str
    DB_HOST_DOCKER: str
    DB_PORT: int
    DB_NAME: str
    TOKEN: str
    RMQ_HOST: str
    RMQ_PORT: int
    RMQ_USER: str
    RMQ_PASSWORD: str
    RMQ_EXCHANGE: str
    RMQ_ROUTING_KEY: str
    MAIN_DOMEN: str

    model_config = SettingsConfigDict(
        env_file=os.path.join(BASE_DIR, ".env"),
        extra="allow",
    )

    @staticmethod
    def configure_logging(level: int = logging.INFO) -> None:
        logging.basicConfig(
            level=level,
            datefmt="%Y-%m-%d %H:%M:%S",
            format="[%(asctime)s.%(msecs)03d] "
                   "%(funcName)20s "
                   "%(module)s:%(lineno)d "
                   "%(levelname)-8s - "
                   "%(message)s",
        )

    def get_db_url(self) -> str:
        if self.DOCKER:
            return (f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@"
                    f"{self.DB_HOST_DOCKER}:{self.DB_PORT}/{self.DB_NAME}")
        return (f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@"
                f"{self.DB_HOST_LOCAL}:{self.DB_PORT}/{self.DB_NAME}")

    def get_faker(self) -> Faker:
        fake = Faker("ru_RU")
        return fake

    def get_rmq_url(self) -> str:
        return f"amqp://{self.RMQ_USER}:{self.RMQ_PASSWORD}@{self.RMQ_HOST}:{self.RMQ_PORT}/"

    async def get_rmq_connection(self) -> AbstractRobustConnection:
        return await connect_robust(
            url=self.get_rmq_url(),
            timeout=30,
        )


settings = Settings()
