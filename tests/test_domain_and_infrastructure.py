from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from domain.exceptions import IllegalStateTransition
from domain.reservation_aggregate import Reservation
from domain.reservation_status import ReservationStatus
from infrastructure.db.session import create_engine_from_env, create_session_factory


def _aggregate(status: ReservationStatus) -> Reservation:
    now = datetime.now(timezone.utc)
    return Reservation(
        id=uuid4(),
        sku="sku-domain",
        quantity=1,
        status=status,
        idempotency_key=f"idem-{uuid4()}",
        created_at=now,
        updated_at=now,
    )


def test_aggregate_confirm_from_active() -> None:
    reservation = _aggregate(ReservationStatus.ACTIVE)
    result = reservation.confirm()
    assert result.status == ReservationStatus.CONFIRMED


def test_aggregate_confirm_idempotent_on_confirmed() -> None:
    reservation = _aggregate(ReservationStatus.CONFIRMED)
    result = reservation.confirm()
    assert result.status == ReservationStatus.CONFIRMED


def test_aggregate_confirm_illegal_on_canceled() -> None:
    reservation = _aggregate(ReservationStatus.CANCELED)
    with pytest.raises(IllegalStateTransition):
        reservation.confirm()


def test_aggregate_cancel_from_active() -> None:
    reservation = _aggregate(ReservationStatus.ACTIVE)
    result = reservation.cancel()
    assert result.status == ReservationStatus.CANCELED


def test_aggregate_cancel_idempotent_on_canceled() -> None:
    reservation = _aggregate(ReservationStatus.CANCELED)
    result = reservation.cancel()
    assert result.status == ReservationStatus.CANCELED


def test_aggregate_cancel_illegal_on_confirmed() -> None:
    reservation = _aggregate(ReservationStatus.CONFIRMED)
    with pytest.raises(IllegalStateTransition):
        reservation.cancel()


def test_create_engine_from_explicit_url() -> None:
    engine = create_engine_from_env("postgresql+psycopg://u:p@localhost:5432/db")
    try:
        assert "postgresql+psycopg://u:p@localhost:5432/db" == engine.url.render_as_string(
            hide_password=False
        )
    finally:
        engine.dispose()


def test_create_engine_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u2:p2@localhost:5432/db2")
    engine = create_engine_from_env()
    try:
        assert "postgresql+psycopg://u2:p2@localhost:5432/db2" == engine.url.render_as_string(
            hide_password=False
        )
    finally:
        engine.dispose()


def test_create_session_factory(db_session: Session) -> None:
    factory = create_session_factory(db_session.bind)
    created = factory()
    try:
        assert isinstance(created, Session)
    finally:
        created.close()
