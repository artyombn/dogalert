import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    APP_NAME: str
    DOCKER: bool
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST_LOCAL: str
    DB_HOST_DOCKER: str
    DB_PORT: int
    DB_NAME: str

    model_config = SettingsConfigDict(
        env_file=os.path.join(BASE_DIR, ".env"),
        extra="allow",
    )

    def get_db_url(self) -> str:
        if self.DOCKER:
            return (f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@"
                    f"{self.DB_HOST_DOCKER}:{self.DB_PORT}/{self.DB_NAME}")
        return (f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@"
                f"{self.DB_HOST_LOCAL}:{self.DB_PORT}/{self.DB_NAME}")

settings = Settings()
