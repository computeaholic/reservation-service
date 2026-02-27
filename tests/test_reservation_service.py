from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from domain.exceptions import IllegalStateTransition, InsufficientInventory, ReservationNotFound
from domain.reservation_status import ReservationStatus
from infrastructure.models.inventory_item import InventoryItem
from infrastructure.models.reservation import Reservation
from services.reservation_service import cancel_reservation, confirm_reservation, create_reservation


def _add_inventory(
    session_factory,
    *,
    sku: str,
    total_quantity: int,
    reserved_quantity: int = 0,
) -> None:
    with session_factory() as session:
        with session.begin():
            inventory = InventoryItem(
                sku=sku,
                total_quantity=total_quantity,
                reserved_quantity=reserved_quantity,
            )
            session.add(inventory)


def test_over_reservation_prevented(session_factory) -> None:
    sku = f"sku-over-{uuid4()}"
    _add_inventory(session_factory, sku=sku, total_quantity=10)

    with session_factory() as session:
        create_reservation(session, sku=sku, quantity=8, idempotency_key=f"idem-{uuid4()}")

    with session_factory() as session, pytest.raises(InsufficientInventory):
        create_reservation(session, sku=sku, quantity=5, idempotency_key=f"idem-{uuid4()}")


def test_idempotency_replay(session_factory) -> None:
    sku = f"sku-idem-{uuid4()}"
    idempotency_key = f"idem-{uuid4()}"
    _add_inventory(session_factory, sku=sku, total_quantity=10)

    with session_factory() as session:
        first = create_reservation(session, sku=sku, quantity=4, idempotency_key=idempotency_key)
    with session_factory() as session:
        second = create_reservation(session, sku=sku, quantity=4, idempotency_key=idempotency_key)

    assert first.id == second.id

    with session_factory() as session:
        reservation_count = (
            session.execute(
                select(Reservation).where(Reservation.idempotency_key == idempotency_key)
            )
            .scalars()
            .all()
        )
    assert len(reservation_count) == 1

    with session_factory() as session:
        inventory = session.execute(
            select(InventoryItem).where(InventoryItem.sku == sku)
        ).scalar_one()
    assert inventory.reserved_quantity == 4


def test_create_reservation_rollback_on_failure(session_factory) -> None:
    sku = f"sku-rollback-{uuid4()}"
    idempotency_key = f"idem-{uuid4()}"
    _add_inventory(session_factory, sku=sku, total_quantity=1)

    with session_factory() as session, pytest.raises(InsufficientInventory):
        create_reservation(session, sku=sku, quantity=2, idempotency_key=idempotency_key)

    with session_factory() as session:
        reservation = session.execute(
            select(Reservation).where(Reservation.idempotency_key == idempotency_key)
        ).scalar_one_or_none()
        assert reservation is None

        inventory = session.execute(
            select(InventoryItem).where(InventoryItem.sku == sku)
        ).scalar_one()
        assert inventory.reserved_quantity == 0


def test_cancel_restores_inventory_once(session_factory) -> None:
    sku = f"sku-cancel-{uuid4()}"
    _add_inventory(session_factory, sku=sku, total_quantity=10)

    with session_factory() as session:
        created = create_reservation(
            session,
            sku=sku,
            quantity=6,
            idempotency_key=f"idem-{uuid4()}",
        )

    with session_factory() as session:
        first_cancel = cancel_reservation(session, created.id)
    with session_factory() as session:
        second_cancel = cancel_reservation(session, created.id)

    assert first_cancel.status == ReservationStatus.CANCELED
    assert second_cancel.status == ReservationStatus.CANCELED

    with session_factory() as session:
        inventory = session.execute(
            select(InventoryItem).where(InventoryItem.sku == sku)
        ).scalar_one()
    assert inventory.reserved_quantity == 0


def test_illegal_transitions(session_factory) -> None:
    confirm_sku = f"sku-confirm-{uuid4()}"
    cancel_sku = f"sku-cancel-{uuid4()}"
    _add_inventory(session_factory, sku=confirm_sku, total_quantity=10)
    _add_inventory(session_factory, sku=cancel_sku, total_quantity=10)

    with session_factory() as session:
        confirmed = create_reservation(
            session,
            sku=confirm_sku,
            quantity=3,
            idempotency_key=f"idem-{uuid4()}",
        )
    with session_factory() as session:
        confirm_reservation(session, confirmed.id)

    with session_factory() as session:
        confirm_again = confirm_reservation(session, confirmed.id)
    assert confirm_again.status == ReservationStatus.CONFIRMED

    with session_factory() as session:
        canceled = create_reservation(
            session,
            sku=cancel_sku,
            quantity=2,
            idempotency_key=f"idem-{uuid4()}",
        )
    with session_factory() as session:
        cancel_reservation(session, canceled.id)

    with session_factory() as session, pytest.raises(IllegalStateTransition):
        cancel_reservation(session, confirmed.id)

    with session_factory() as session, pytest.raises(IllegalStateTransition):
        confirm_reservation(session, canceled.id)


def test_sku_not_found_vs_insufficient(session_factory) -> None:
    missing_sku = f"sku-missing-{uuid4()}"
    existing_sku = f"sku-existing-{uuid4()}"
    _add_inventory(session_factory, sku=existing_sku, total_quantity=2)

    with session_factory() as session, pytest.raises(ReservationNotFound):
        create_reservation(
            session,
            sku=missing_sku,
            quantity=1,
            idempotency_key=f"idem-{uuid4()}",
        )

    with session_factory() as session, pytest.raises(InsufficientInventory):
        create_reservation(
            session,
            sku=existing_sku,
            quantity=3,
            idempotency_key=f"idem-{uuid4()}",
        )


def test_reservation_not_found_errors(session_factory) -> None:
    missing_id = uuid4()

    with session_factory() as session, pytest.raises(ReservationNotFound):
        confirm_reservation(session, missing_id)

    with session_factory() as session, pytest.raises(ReservationNotFound):
        cancel_reservation(session, missing_id)


def test_concurrent_create_does_not_overbook(engine) -> None:
    sku = f"sku-concurrency-{uuid4()}"
    with Session(engine) as setup_session, setup_session.begin():
        setup_session.add(
            InventoryItem(
                sku=sku,
                total_quantity=10,
                reserved_quantity=0,
            )
        )

    def attempt_create(key: str) -> tuple[str, object]:
        with Session(engine) as local_session:
            try:
                created = create_reservation(
                    local_session,
                    sku=sku,
                    quantity=7,
                    idempotency_key=key,
                )
                return ("ok", created.id)
            except InsufficientInventory as exc:
                return ("insufficient", str(exc))

    keys = [f"idem-{uuid4()}", f"idem-{uuid4()}"]
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(attempt_create, keys))

    success_count = sum(1 for status, _ in results if status == "ok")
    insufficient_count = sum(1 for status, _ in results if status == "insufficient")

    assert success_count == 1
    assert insufficient_count == 1

    with Session(engine) as verify_session:
        inventory = verify_session.execute(
            select(InventoryItem).where(InventoryItem.sku == sku)
        ).scalar_one()
        assert inventory.reserved_quantity == 7


def test_concurrent_double_cancel_invariant(engine) -> None:
    sku = f"sku-double-cancel-{uuid4()}"
    with Session(engine) as setup_session, setup_session.begin():
        setup_session.add(
            InventoryItem(
                sku=sku,
                total_quantity=10,
                reserved_quantity=0,
            )
        )

    with Session(engine) as create_session:
        created = create_reservation(
            create_session,
            sku=sku,
            quantity=5,
            idempotency_key=f"idem-{uuid4()}",
        )

    def attempt_cancel() -> tuple[str, str]:
        with Session(engine) as local_session:
            try:
                result = cancel_reservation(local_session, created.id)
                return ("ok", result.status.value)
            except IllegalStateTransition as exc:
                return ("illegal", str(exc))

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(lambda _: attempt_cancel(), [1, 2]))

    statuses = [kind for kind, _ in outcomes]
    assert statuses.count("ok") >= 1

    with Session(engine) as verify_session:
        inventory = verify_session.execute(
            select(InventoryItem).where(InventoryItem.sku == sku)
        ).scalar_one()
        reservation = verify_session.get(Reservation, created.id)
        assert inventory.reserved_quantity == 0
        assert reservation is not None
        assert reservation.status == ReservationStatus.CANCELED.value


def test_negative_inventory_guard_constraint(session_factory) -> None:
    sku = f"sku-negative-guard-{uuid4()}"
    _add_inventory(session_factory, sku=sku, total_quantity=10, reserved_quantity=0)

    with session_factory() as session:
        inventory = session.execute(
            select(InventoryItem).where(InventoryItem.sku == sku)
        ).scalar_one()
        inventory.reserved_quantity = -1

        with pytest.raises(IntegrityError):
            session.flush()

        session.rollback()
