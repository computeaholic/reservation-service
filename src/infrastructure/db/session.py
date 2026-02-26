import os

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

_DEFAULT_DATABASE_URL = "postgresql+psycopg://reservation_service:reservation_service@localhost:5432/reservation_service"


def create_engine_from_env(database_url: str | None = None) -> Engine:
    resolved_url: str = database_url or os.getenv("DATABASE_URL") or _DEFAULT_DATABASE_URL
    return create_engine(resolved_url, pool_pre_ping=True)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autocommit=False, autoflush=False, class_=Session)
