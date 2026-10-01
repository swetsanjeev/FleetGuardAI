from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=False,
        extra="ignore",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    database_url: str | None = None
    database_migration_url: str | None = None
    database_admin_url: str | None = None
    mongodb_url: str | None = None
    mongodb_admin_url: str | None = None
    mongodb_database: str = "fleetguard"
    redis_url: str | None = None
    object_storage_endpoint: str | None = None
    object_storage_access_key: str | None = None
    object_storage_secret_key: str | None = None
    object_storage_bucket: str = "fleetguard"
    pgvector_embedding_dimension: int = Field(default=1536, ge=1, le=2000)
    database_pool_size: int = Field(default=5, ge=1, le=50)
    database_max_overflow: int = Field(default=10, ge=0, le=100)
    seed_data_enabled: bool = True
    seed_vehicle_count: int = Field(default=10, ge=1, le=10_000)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()