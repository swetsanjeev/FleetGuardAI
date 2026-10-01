import os
import secrets
from pathlib import Path
from typing import Iterator

import pytest
from alembic import command
from alembic.config import Config
from pymongo import MongoClient
from redis import Redis
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import Session
from testcontainers.mongodb import MongoDbContainer
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

from fleetguard_db.bootstrap import bootstrap_postgres
from fleetguard_db.config import get_settings

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "services" / "api"
os.environ.setdefault("PGVECTOR_EMBEDDING_DIMENSION", "1536")


@pytest.fixture(scope="session")
def postgres_container() -> Iterator[PostgresContainer]:
    with PostgresContainer(
        image="pgvector/pgvector:pg16",
        username="fleetguard_test_admin",
        password=secrets.token_urlsafe(24),
        dbname="fleetguard_test",
        driver="psycopg",
    ) as container:
        yield container


@pytest.fixture(scope="session")
def postgres_engine(postgres_container: PostgresContainer) -> Iterator[Engine]:
    admin_url = postgres_container.get_connection_url()
    app_user = "fleetguard_test_runtime"
    migration_user = "fleetguard_test_migration"
    app_password = secrets.token_urlsafe(24)
    migration_password = secrets.token_urlsafe(24)
    admin = make_url(admin_url)
    app_url = admin.set(username=app_user, password=app_password).render_as_string(hide_password=False)
    migration_url = admin.set(username=migration_user, password=migration_password).render_as_string(
        hide_password=False
    )
    variables = {
        "DATABASE_URL": app_url,
        "DATABASE_MIGRATION_URL": migration_url,
        "DATABASE_ADMIN_URL": admin_url,
        "POSTGRES_APP_USER": app_user,
        "POSTGRES_APP_PASSWORD": app_password,
        "POSTGRES_MIGRATION_USER": migration_user,
        "POSTGRES_MIGRATION_PASSWORD": migration_password,
        "PGVECTOR_EMBEDDING_DIMENSION": "1536",
    }
    original = {key: os.environ.get(key) for key in variables}
    os.environ.update(variables)
    get_settings.cache_clear()
    try:
        bootstrap_postgres()
        alembic_config = Config(str(API_ROOT / "alembic.ini"))
        command.upgrade(alembic_config, "head")
        engine = create_engine(app_url, pool_pre_ping=True)
        try:
            yield engine
        finally:
            engine.dispose()
    finally:
        for key, value in original.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        get_settings.cache_clear()


@pytest.fixture
def postgres_session(postgres_engine: Engine) -> Iterator[Session]:
    connection = postgres_engine.connect()
    outer_transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint", expire_on_commit=False)
    try:
        yield session
    finally:
        session.close()
        if outer_transaction.is_active:
            outer_transaction.rollback()
        connection.close()


@pytest.fixture(scope="session")
def mongodb_container() -> Iterator[MongoDbContainer]:
    with MongoDbContainer(
        image="mongo:7.0.14",
        username="fleetguard_test_root",
        password=secrets.token_urlsafe(24),
        dbname="admin",
    ) as container:
        yield container


@pytest.fixture
def mongo_database(mongodb_container: MongoDbContainer):
    client = MongoClient(mongodb_container.get_connection_url(), serverSelectionTimeoutMS=5000)
    database = client["fleetguard_test"]
    try:
        yield database
    finally:
        client.drop_database("fleetguard_test")
        client.close()


@pytest.fixture(scope="session")
def redis_container() -> Iterator[RedisContainer]:
    with RedisContainer(image="redis:7.4.1-alpine") as container:
        yield container


@pytest.fixture
def redis_client(redis_container: RedisContainer) -> Iterator[Redis]:
    client = redis_container.get_client(decode_responses=True)
    client.flushdb()
    try:
        yield client
    finally:
        client.flushdb()
        client.close()