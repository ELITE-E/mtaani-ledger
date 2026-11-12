from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://ledger:ledger@localhost:5433/ledger"
    worker_heartbeat_seconds: float = 5.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
