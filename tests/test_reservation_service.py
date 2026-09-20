from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, BrokenBarrierError
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from domain.exceptions import (
    IdempotencyConflict,
    IllegalStateTransition,
    InsufficientInventory,
    InvalidQuantity,
    ReservationNotFound,
    SkuNotFound,
)
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


def _inventory_for_sku(session_factory, sku: str) -> InventoryItem:
    with session_factory() as session:
        return session.execute(select(InventoryItem).where(InventoryItem.sku == sku)).scalar_one()


def test_create_reservation_records_an_active_hold(session_factory) -> None:
    sku = f"sku-active-{uuid4()}"
    _add_inventory(session_factory, sku=sku, total_quantity=10)

    with session_factory() as session:
        created = create_reservation(
            session,
            sku=sku,
            quantity=4,
            idempotency_key=f"idem-{uuid4()}",
        )

    assert created.status == ReservationStatus.ACTIVE
    assert _inventory_for_sku(session_factory, sku).reserved_quantity == 4


def test_create_reservation_can_consume_the_final_available_unit(session_factory) -> None:
    sku = f"sku-final-unit-{uuid4()}"
    _add_inventory(session_factory, sku=sku, total_quantity=1)

    with session_factory() as session:
        created = create_reservation(
            session,
            sku=sku,
            quantity=1,
            idempotency_key=f"idem-{uuid4()}",
        )

    assert created.status == ReservationStatus.ACTIVE
    assert _inventory_for_sku(session_factory, sku).reserved_quantity == 1


def test_create_reservation_rejects_insufficient_inventory(session_factory) -> None:
    sku = f"sku-over-{uuid4()}"
    _add_inventory(session_factory, sku=sku, total_quantity=10)

    with session_factory() as session:
        create_reservation(session, sku=sku, quantity=8, idempotency_key=f"idem-{uuid4()}")

    with session_factory() as session, pytest.raises(InsufficientInventory):
        create_reservation(session, sku=sku, quantity=5, idempotency_key=f"idem-{uuid4()}")


def test_create_reservation_replays_equivalent_idempotency_key(session_factory) -> None:
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


def test_create_reservation_rejects_conflicting_idempotency_key_for_sku(session_factory) -> None:
    original_sku = f"sku-original-{uuid4()}"
    conflicting_sku = f"sku-conflict-{uuid4()}"
    idempotency_key = f"idem-{uuid4()}"
    _add_inventory(session_factory, sku=original_sku, total_quantity=10)
    _add_inventory(session_factory, sku=conflicting_sku, total_quantity=10)

    with session_factory() as session:
        create_reservation(
            session,
            sku=original_sku,
            quantity=4,
            idempotency_key=idempotency_key,
        )

    with session_factory() as session, pytest.raises(IdempotencyConflict):
        create_reservation(
            session,
            sku=conflicting_sku,
            quantity=4,
            idempotency_key=idempotency_key,
        )

    assert _inventory_for_sku(session_factory, original_sku).reserved_quantity == 4
    assert _inventory_for_sku(session_factory, conflicting_sku).reserved_quantity == 0


def test_create_reservation_rejects_conflicting_idempotency_key_for_quantity(
    session_factory,
) -> None:
    sku = f"sku-idem-qty-{uuid4()}"
    idempotency_key = f"idem-{uuid4()}"
    _add_inventory(session_factory, sku=sku, total_quantity=10)

    with session_factory() as session:
        create_reservation(
            session,
            sku=sku,
            quantity=4,
            idempotency_key=idempotency_key,
        )

    with session_factory() as session, pytest.raises(IdempotencyConflict):
        create_reservation(
            session,
            sku=sku,
            quantity=5,
            idempotency_key=idempotency_key,
        )

    assert _inventory_for_sku(session_factory, sku).reserved_quantity == 4


def test_create_reservation_rejects_missing_sku(session_factory) -> None:
    with session_factory() as session, pytest.raises(SkuNotFound):
        create_reservation(
            session,
            sku=f"sku-missing-{uuid4()}",
            quantity=1,
            idempotency_key=f"idem-{uuid4()}",
        )


@pytest.mark.parametrize("quantity", [0, -1])
def test_create_reservation_rejects_invalid_quantity(session_factory, quantity: int) -> None:
    sku = f"sku-invalid-{uuid4()}"
    _add_inventory(session_factory, sku=sku, total_quantity=10)

    with session_factory() as session, pytest.raises(InvalidQuantity):
        create_reservation(
            session,
            sku=sku,
            quantity=quantity,
            idempotency_key=f"idem-{uuid4()}",
        )

    assert _inventory_for_sku(session_factory, sku).reserved_quantity == 0


def test_create_reservation_rolls_back_failed_attempt(session_factory) -> None:
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


def test_confirm_reservation_transitions_active_to_confirmed(session_factory) -> None:
    sku = f"sku-confirm-{uuid4()}"
    _add_inventory(session_factory, sku=sku, total_quantity=10)

    with session_factory() as session:
        created = create_reservation(
            session,
            sku=sku,
            quantity=3,
            idempotency_key=f"idem-{uuid4()}",
        )

    with session_factory() as session:
        confirmed = confirm_reservation(session, created.id)

    assert confirmed.status == ReservationStatus.CONFIRMED
    assert _inventory_for_sku(session_factory, sku).reserved_quantity == 3


def test_confirm_reservation_is_idempotent_for_confirmed(session_factory) -> None:
    sku = f"sku-confirm-idempotent-{uuid4()}"
    _add_inventory(session_factory, sku=sku, total_quantity=10)

    with session_factory() as session:
        created = create_reservation(
            session,
            sku=sku,
            quantity=3,
            idempotency_key=f"idem-{uuid4()}",
        )

    with session_factory() as session:
        confirm_reservation(session, created.id)

    with session_factory() as session:
        confirmed_again = confirm_reservation(session, created.id)

    assert confirmed_again.status == ReservationStatus.CONFIRMED


def test_confirm_reservation_rejects_canceled(session_factory) -> None:
    sku = f"sku-confirm-illegal-{uuid4()}"
    _add_inventory(session_factory, sku=sku, total_quantity=10)

    with session_factory() as session:
        created = create_reservation(
            session,
            sku=sku,
            quantity=3,
            idempotency_key=f"idem-{uuid4()}",
        )

    with session_factory() as session:
        cancel_reservation(session, created.id)

    with session_factory() as session, pytest.raises(IllegalStateTransition):
        confirm_reservation(session, created.id)


def test_cancel_reservation_transitions_active_to_canceled(session_factory) -> None:
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
        canceled = cancel_reservation(session, created.id)

    assert canceled.status == ReservationStatus.CANCELED
    assert _inventory_for_sku(session_factory, sku).reserved_quantity == 0


def test_cancel_reservation_is_idempotent_for_canceled(session_factory) -> None:
    sku = f"sku-cancel-idempotent-{uuid4()}"
    _add_inventory(session_factory, sku=sku, total_quantity=10)

    with session_factory() as session:
        created = create_reservation(
            session,
            sku=sku,
            quantity=6,
            idempotency_key=f"idem-{uuid4()}",
        )

    with session_factory() as session:
        cancel_reservation(session, created.id)

    with session_factory() as session:
        canceled_again = cancel_reservation(session, created.id)

    assert canceled_again.status == ReservationStatus.CANCELED
    assert _inventory_for_sku(session_factory, sku).reserved_quantity == 0


def test_cancel_reservation_rejects_confirmed(session_factory) -> None:
    sku = f"sku-cancel-illegal-{uuid4()}"
    _add_inventory(session_factory, sku=sku, total_quantity=10)

    with session_factory() as session:
        created = create_reservation(
            session,
            sku=sku,
            quantity=2,
            idempotency_key=f"idem-{uuid4()}",
        )

    with session_factory() as session:
        confirm_reservation(session, created.id)

    with session_factory() as session, pytest.raises(IllegalStateTransition):
        cancel_reservation(session, created.id)


def test_confirm_and_cancel_require_existing_reservation(session_factory) -> None:
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


def test_concurrent_equivalent_idempotent_create_returns_same_reservation(engine) -> None:
    sku = f"sku-idem-race-{uuid4()}"
    idempotency_key = f"idem-{uuid4()}"
    with Session(engine) as setup_session, setup_session.begin():
        setup_session.add(
            InventoryItem(
                sku=sku,
                total_quantity=10,
                reserved_quantity=0,
            )
        )

    barrier = Barrier(2)

    class ReplayRaceSession(Session):
        def execute(self, statement, *args, **kwargs):  # type: ignore[override]
            result = super().execute(statement, *args, **kwargs)
            statement_text = str(statement)
            if (
                "FROM reservations" in statement_text
                and "idempotency_key" in statement_text
                and not getattr(self, "_replay_checked", False)
            ):
                self._replay_checked = True
                try:
                    barrier.wait(timeout=5)
                except BrokenBarrierError:
                    pass
            return result

    session_factory = sessionmaker(bind=engine, class_=ReplayRaceSession)

    def attempt_create() -> tuple[str, object]:
        with session_factory() as local_session:
            try:
                created = create_reservation(
                    local_session,
                    sku=sku,
                    quantity=4,
                    idempotency_key=idempotency_key,
                )
                return ("ok", created.id)
            except Exception as exc:  # pragma: no cover - failure is asserted below
                return (exc.__class__.__name__, str(exc))

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(lambda _: attempt_create(), [1, 2]))

    assert [status for status, _ in outcomes] == ["ok", "ok"]
    assert outcomes[0][1] == outcomes[1][1]

    with Session(engine) as verify_session:
        inventory = verify_session.execute(
            select(InventoryItem).where(InventoryItem.sku == sku)
        ).scalar_one()
        reservations = (
            verify_session.execute(
                select(Reservation).where(Reservation.idempotency_key == idempotency_key)
            )
            .scalars()
            .all()
        )

    assert inventory.reserved_quantity == 4
    assert len(reservations) == 1


def test_concurrent_double_cancel_restores_inventory_once(engine) -> None:
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

    barrier = Barrier(2)

    def attempt_cancel() -> tuple[str, str]:
        try:
            barrier.wait(timeout=5)
        except BrokenBarrierError:
            pass

        with Session(engine) as local_session:
            try:
                result = cancel_reservation(local_session, created.id)
                return ("canceled", result.status.value)
            except IllegalStateTransition as exc:
                return ("illegal", str(exc))

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(lambda _: attempt_cancel(), [1, 2]))

    assert outcomes == [("canceled", "canceled"), ("canceled", "canceled")]

    with Session(engine) as verify_session:
        inventory = verify_session.execute(
            select(InventoryItem).where(InventoryItem.sku == sku)
        ).scalar_one()
        reservation = verify_session.get(Reservation, created.id)
        assert inventory.reserved_quantity == 0
        assert reservation is not None
        assert reservation.status == ReservationStatus.CANCELED.value


def test_concurrent_confirm_and_cancel_have_one_deterministic_winner(engine) -> None:
    sku = f"sku-confirm-cancel-race-{uuid4()}"
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
            quantity=4,
            idempotency_key=f"idem-{uuid4()}",
        )

    barrier = Barrier(2)

    def attempt_confirm() -> tuple[str, str]:
        try:
            barrier.wait(timeout=5)
        except BrokenBarrierError:
            pass

        with Session(engine) as local_session:
            try:
                result = confirm_reservation(local_session, created.id)
                return ("confirmed", result.status.value)
            except IllegalStateTransition as exc:
                return ("illegal", str(exc))

    def attempt_cancel() -> tuple[str, str]:
        try:
            barrier.wait(timeout=5)
        except BrokenBarrierError:
            pass

        with Session(engine) as local_session:
            try:
                result = cancel_reservation(local_session, created.id)
                return ("canceled", result.status.value)
            except IllegalStateTransition as exc:
                return ("illegal", str(exc))

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(lambda fn: fn(), [attempt_confirm, attempt_cancel]))

    winner_kinds = {kind for kind, _ in outcomes}
    assert "illegal" in winner_kinds
    assert winner_kinds in ({"confirmed", "illegal"}, {"canceled", "illegal"})

    with Session(engine) as verify_session:
        inventory = verify_session.execute(
            select(InventoryItem).where(InventoryItem.sku == sku)
        ).scalar_one()
        reservation = verify_session.get(Reservation, created.id)

    assert reservation is not None
    if reservation.status == ReservationStatus.CONFIRMED.value:
        assert inventory.reserved_quantity == 4
        assert ("confirmed", ReservationStatus.CONFIRMED.value) in outcomes
    else:
        assert reservation.status == ReservationStatus.CANCELED.value
        assert inventory.reserved_quantity == 0
        assert ("canceled", ReservationStatus.CANCELED.value) in outcomes


def test_negative_reserved_inventory_breaks_db_constraint(session_factory) -> None:
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


def test_reserved_inventory_cannot_exceed_total_quantity(session_factory) -> None:
    sku = f"sku-total-guard-{uuid4()}"
    _add_inventory(session_factory, sku=sku, total_quantity=10, reserved_quantity=0)

    with session_factory() as session:
        inventory = session.execute(
            select(InventoryItem).where(InventoryItem.sku == sku)
        ).scalar_one()
        inventory.reserved_quantity = 11

        with pytest.raises(IntegrityError):
            session.flush()

        session.rollback()
