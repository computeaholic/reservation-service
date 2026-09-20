# mypy: ignore-errors
# ruff: noqa: I001

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

from infrastructure.db.base import Base
from infrastructure.db.session import _DEFAULT_DATABASE_URL
from infrastructure.models.inventory_item import InventoryItem  # noqa: F401
from infrastructure.models.reservation import Reservation  # noqa: F401

config = context.config

database_url = os.getenv("DATABASE_URL")
configured_url = config.get_main_option("sqlalchemy.url")
if database_url and configured_url == _DEFAULT_DATABASE_URL:
    config.set_main_option("sqlalchemy.url", database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata
_MODELS_FOR_METADATA = (InventoryItem, Reservation)


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(
        config.get_main_option("sqlalchemy.url"),
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
