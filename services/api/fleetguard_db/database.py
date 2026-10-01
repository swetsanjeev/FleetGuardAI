from contextlib import contextmanager
from functools import lru_cache
from typing import Iterator

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from fleetguard_db.config import get_settings


def create_database_engine(database_url: str | None = None) -> Engine:
    settings = get_settings()
    url = database_url or settings.database_url
    if not url:
        raise RuntimeError("DATABASE_URL is required for PostgreSQL access")
    return create_engine(
        url,
        pool_pre_ping=True,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        pool_recycle=1800,
    )


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    return create_database_engine()


@lru_cache(maxsize=1)
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False)


def get_session() -> Iterator[Session]:
    with get_session_factory()() as session:
        yield session


@contextmanager
def transaction() -> Iterator[Session]:
    with get_session_factory().begin() as session:
        yield session


def check_postgres() -> None:
    with get_engine().connect() as connection:
        connection.execute(text("SELECT 1"))


def close_database_engine() -> None:
    if get_engine.cache_info().currsize:
        get_engine().dispose()
        get_session_factory.cache_clear()
        get_engine.cache_clear()