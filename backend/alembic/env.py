from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context
from app.config import DatabaseSettings
from app.db.base import Base, include_migration_name, include_migration_object
from app.db.models import Garment  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    settings = DatabaseSettings()
    context.configure(
        url=settings.sqlalchemy_url,
        target_metadata=target_metadata,
        include_name=include_migration_name,
        include_object=include_migration_object,
        include_schemas=True,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_name=include_migration_name,
        include_object=include_migration_object,
        include_schemas=True,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    settings = DatabaseSettings()
    connectable = create_async_engine(
        settings.sqlalchemy_url,
        poolclass=pool.NullPool,
        connect_args={
            "connect_timeout": settings.database_connect_timeout_seconds,
        },
    )

    try:
        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)
    finally:
        await connectable.dispose()


def run_migrations_online() -> None:
    import asyncio

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
