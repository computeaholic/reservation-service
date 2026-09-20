from uuid import uuid4

from sqlalchemy import create_engine, inspect, text

from alembic import command
from alembic.config import Config
from infrastructure.db.session import create_engine_from_env


def test_migrations_upgrade_downgrade_and_reupgrade() -> None:
    base_engine = create_engine_from_env()
    base_url = base_engine.url
    base_engine.dispose()

    database_name = f"reservation_migration_{uuid4().hex}"
    migration_url = base_url.set(database=database_name)
    admin_url = base_url.set(database="postgres")

    admin_engine = create_engine(
        admin_url.render_as_string(hide_password=False),
        isolation_level="AUTOCOMMIT",
    )

    migration_engine = None
    try:
        with admin_engine.connect() as connection:
            connection.execute(text(f"CREATE DATABASE {database_name}"))

        config = Config("alembic.ini")
        config.set_main_option(
            "sqlalchemy.url",
            migration_url.render_as_string(hide_password=False),
        )

        command.upgrade(config, "head")

        migration_engine = create_engine(migration_url.render_as_string(hide_password=False))
        inspector = inspect(migration_engine)
        assert {"alembic_version", "inventory_items", "reservations"}.issubset(
            set(inspector.get_table_names())
        )

        inventory_constraints = {
            constraint["name"] for constraint in inspector.get_check_constraints("inventory_items")
        }
        assert "ck_inventory_items_reserved_quantity_non_negative" in inventory_constraints
        assert "ck_inventory_items_reserved_quantity_lte_total_quantity" in inventory_constraints
        assert "ck_inventory_items_total_quantity_non_negative" in inventory_constraints

        command.downgrade(config, "base")
        inspector = inspect(migration_engine)
        assert "inventory_items" not in inspector.get_table_names()
        assert "reservations" not in inspector.get_table_names()

        command.upgrade(config, "head")
        inspector = inspect(migration_engine)
        assert {"inventory_items", "reservations"}.issubset(set(inspector.get_table_names()))
    finally:
        if migration_engine is not None:
            migration_engine.dispose()
        with admin_engine.connect() as connection:
            connection.execute(
                text(
                    "SELECT pg_terminate_backend(pid) "
                    "FROM pg_stat_activity "
                    "WHERE datname = :database_name AND pid <> pg_backend_pid()"
                ),
                {"database_name": database_name},
            )
            connection.execute(text(f"DROP DATABASE IF EXISTS {database_name}"))
        admin_engine.dispose()
