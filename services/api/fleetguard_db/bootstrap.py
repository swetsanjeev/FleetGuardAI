import logging
import os

from psycopg import sql as pg_sql
from pymongo import MongoClient
from sqlalchemy import create_engine, text

from fleetguard_db.config import get_settings
from fleetguard_db.mongo import ensure_mongo_schema

logger = logging.getLogger(__name__)


def bootstrap_postgres() -> None:
    settings = get_settings()
    if not settings.database_admin_url:
        raise RuntimeError("DATABASE_ADMIN_URL is required for database bootstrap")
    app_user = os.environ.get("POSTGRES_APP_USER")
    app_password = os.environ.get("POSTGRES_APP_PASSWORD")
    migration_user = os.environ.get("POSTGRES_MIGRATION_USER")
    migration_password = os.environ.get("POSTGRES_MIGRATION_PASSWORD")
    if not all((app_user, app_password, migration_user, migration_password)):
        raise RuntimeError("PostgreSQL runtime and migration credentials are required")
    if app_user == migration_user:
        raise RuntimeError("PostgreSQL runtime and migration roles must be distinct")
    engine = create_engine(settings.database_admin_url, pool_pre_ping=True)
    try:
        with engine.begin() as connection:
            raw_connection = connection.connection.driver_connection
            for role_name, role_password in (
                (migration_user, migration_password),
                (app_user, app_password),
            ):
                exists = connection.execute(
                    text("SELECT 1 FROM pg_catalog.pg_roles WHERE rolname = :role_name"),
                    {"role_name": role_name},
                ).scalar_one_or_none()
                if exists:
                    statement = pg_sql.SQL("ALTER ROLE {} WITH LOGIN PASSWORD {}").format(
                        pg_sql.Identifier(role_name), pg_sql.Literal(role_password)
                    )
                else:
                    statement = pg_sql.SQL("CREATE ROLE {} LOGIN PASSWORD {}").format(
                        pg_sql.Identifier(role_name), pg_sql.Literal(role_password)
                    )
                with raw_connection.cursor() as cursor:
                    cursor.execute(statement)
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            connection.execute(text("CREATE SCHEMA IF NOT EXISTS fleetguard"))
            statements = (
                pg_sql.SQL("ALTER SCHEMA {} OWNER TO {}").format(
                    pg_sql.Identifier("fleetguard"), pg_sql.Identifier(migration_user)
                ),
                pg_sql.SQL("ALTER ROLE {} SET search_path TO public, fleetguard").format(
                    pg_sql.Identifier(migration_user)
                ),
                pg_sql.SQL("ALTER ROLE {} SET search_path TO fleetguard, public").format(
                    pg_sql.Identifier(app_user)
                ),
                pg_sql.SQL("GRANT CONNECT ON DATABASE {} TO {}, {}").format(
                    pg_sql.Identifier(connection.engine.url.database),
                    pg_sql.Identifier(migration_user),
                    pg_sql.Identifier(app_user),
                ),
                pg_sql.SQL("GRANT USAGE ON SCHEMA fleetguard TO {}").format(pg_sql.Identifier(app_user)),
                pg_sql.SQL("GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA fleetguard TO {}").format(
                    pg_sql.Identifier(app_user)
                ),
                pg_sql.SQL("GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA fleetguard TO {}").format(
                    pg_sql.Identifier(app_user)
                ),
                pg_sql.SQL(
                    "ALTER DEFAULT PRIVILEGES FOR ROLE {} IN SCHEMA fleetguard "
                    "GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {}"
                ).format(pg_sql.Identifier(migration_user), pg_sql.Identifier(app_user)),
                pg_sql.SQL(
                    "ALTER DEFAULT PRIVILEGES FOR ROLE {} IN SCHEMA fleetguard "
                    "GRANT USAGE, SELECT ON SEQUENCES TO {}"
                ).format(pg_sql.Identifier(migration_user), pg_sql.Identifier(app_user)),
            )
            with raw_connection.cursor() as cursor:
                for statement in statements:
                    cursor.execute(statement)
    finally:
        engine.dispose()
    logger.info("PostgreSQL application role and pgvector schema are ready")


def bootstrap_mongodb() -> None:
    settings = get_settings()
    if not settings.mongodb_admin_url:
        raise RuntimeError("MONGODB_ADMIN_URL is required for database bootstrap")
    app_user = os.environ.get("MONGODB_APP_USER")
    app_password = os.environ.get("MONGODB_APP_PASSWORD")
    if not app_user or not app_password:
        raise RuntimeError("MONGODB_APP_USER and MONGODB_APP_PASSWORD are required")
    client = MongoClient(settings.mongodb_admin_url, serverSelectionTimeoutMS=5000)
    try:
        database = client[settings.mongodb_database]
        existing_user = database.command("usersInfo", app_user).get("users", [])
        user_options = {"pwd": app_password, "roles": [{"role": "readWrite", "db": settings.mongodb_database}]}
        if existing_user:
            database.command("updateUser", app_user, **user_options)
        else:
            database.command("createUser", app_user, **user_options)
        ensure_mongo_schema(database)
    finally:
        client.close()
    logger.info("MongoDB application role, validators, and indexes are ready")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    bootstrap_postgres()
    bootstrap_mongodb()


if __name__ == "__main__":
    main()