import os

import pytest
from sqlalchemy.orm import Session, sessionmaker

from infrastructure.db.base import Base
from infrastructure.db.session import create_engine_from_env
from infrastructure.models.inventory_item import InventoryItem  # noqa: F401
from infrastructure.models.reservation import Reservation  # noqa: F401


@pytest.fixture(scope="session")
def engine():
    database_url = os.getenv("DATABASE_URL")
    db_engine = create_engine_from_env(database_url)
    Base.metadata.drop_all(db_engine)
    Base.metadata.create_all(db_engine)
    yield db_engine
    db_engine.dispose()


@pytest.fixture
def session_factory(engine):
    connection = engine.connect()
    transaction = connection.begin()
    # Each test session runs inside a nested SAVEPOINT so service functions can
    # call `session.begin()` while preserving outer-test rollback isolation.
    factory = sessionmaker(
        bind=connection,
        class_=Session,
        join_transaction_mode="create_savepoint",
    )

    try:
        yield factory
    finally:
        # The outer transaction rollback guarantees deterministic cleanup with
        # no cross-test leakage, even when tests create/commit nested units.
        transaction.rollback()
        connection.close()


@pytest.fixture
def db_session(session_factory):
    with session_factory() as session:
        yield session
