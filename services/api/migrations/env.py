from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

from fleetguard_db.base import Base, SCHEMA_NAME
from fleetguard_db.config import get_settings
from fleetguard_db import models  # noqa: F401

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def include_name(name, type_, parent_names):
    if type_ == "schema":
        return name == SCHEMA_NAME
    return True


def run_migrations_offline() -> None:
    context.configure(
        url=get_settings().database_migration_url or get_settings().database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
        include_name=include_name,
        version_table_schema=SCHEMA_NAME,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    database_url = get_settings().database_migration_url or get_settings().database_url
    if not database_url:
        raise RuntimeError("DATABASE_URL is required to run migrations")
    connectable = create_engine(database_url, poolclass=pool.NullPool, pool_pre_ping=True)
    try:
        with connectable.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                include_schemas=True,
                include_name=include_name,
                version_table_schema=SCHEMA_NAME,
                compare_type=True,
            )
            with context.begin_transaction():
                context.run_migrations()
    finally:
        connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()