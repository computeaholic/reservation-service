from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from domain.exceptions import (
    IdempotencyConflict,
    IllegalStateTransition,
    InsufficientInventory,
    InvalidQuantity,
    ReservationNotFound,
    SkuNotFound,
)
from domain.reservation_aggregate import Reservation as ReservationAggregate
from domain.reservation_status import ReservationStatus
from infrastructure.models.inventory_item import InventoryItem
from infrastructure.models.reservation import Reservation


def _to_aggregate(model: Reservation) -> ReservationAggregate:
    return ReservationAggregate(
        id=model.id,
        sku=model.sku,
        quantity=model.quantity,
        status=ReservationStatus(model.status),
        idempotency_key=model.idempotency_key,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _validate_quantity(quantity: int) -> None:
    if quantity <= 0:
        raise InvalidQuantity("Quantity must be greater than zero")


def _get_reservation_by_idempotency_key(
    session: Session,
    *,
    idempotency_key: str,
) -> Reservation | None:
    return session.execute(
        select(Reservation).where(Reservation.idempotency_key == idempotency_key)
    ).scalar_one_or_none()


def _assert_matching_idempotent_request(
    reservation: Reservation,
    *,
    sku: str,
    quantity: int,
) -> None:
    if reservation.sku != sku or reservation.quantity != quantity:
        raise IdempotencyConflict(
            "Idempotency key already used for a different reservation request"
        )


def _get_locked_reservation(session: Session, reservation_id: UUID) -> Reservation:
    reservation = session.execute(
        select(Reservation).where(Reservation.id == reservation_id).with_for_update()
    ).scalar_one_or_none()
    if reservation is None:
        raise ReservationNotFound("Reservation not found")
    return reservation


def create_reservation(
    session: Session,
    *,
    sku: str,
    quantity: int,
    idempotency_key: str,
) -> ReservationAggregate:
    with session.begin():
        _validate_quantity(quantity)

        existing = _get_reservation_by_idempotency_key(
            session,
            idempotency_key=idempotency_key,
        )
        if existing is not None:
            _assert_matching_idempotent_request(existing, sku=sku, quantity=quantity)
            return _to_aggregate(existing)

        reservation = Reservation(
            sku=sku,
            quantity=quantity,
            status=ReservationStatus.ACTIVE.value,
            idempotency_key=idempotency_key,
        )

        try:
            with session.begin_nested():
                session.add(reservation)
                session.flush()
        except IntegrityError:
            existing = _get_reservation_by_idempotency_key(
                session,
                idempotency_key=idempotency_key,
            )
            if existing is None:
                raise
            _assert_matching_idempotent_request(existing, sku=sku, quantity=quantity)
            return _to_aggregate(existing)

        inventory_update = (
            update(InventoryItem)
            .where(
                InventoryItem.sku == sku,
                InventoryItem.reserved_quantity + quantity <= InventoryItem.total_quantity,
            )
            .values(reserved_quantity=InventoryItem.reserved_quantity + quantity)
        )
        update_result = session.execute(inventory_update)
        if update_result.rowcount == 0:
            sku_exists = session.execute(
                select(InventoryItem.id).where(InventoryItem.sku == sku)
            ).scalar_one_or_none()
            if sku_exists is None:
                raise SkuNotFound("SKU not found")
            raise InsufficientInventory("Insufficient inventory")

        return _to_aggregate(reservation)


def confirm_reservation(session: Session, reservation_id: UUID) -> ReservationAggregate:
    with session.begin():
        reservation = _get_locked_reservation(session, reservation_id)

        if reservation.status == ReservationStatus.CONFIRMED.value:
            return _to_aggregate(reservation)

        if reservation.status == ReservationStatus.CANCELED.value:
            raise IllegalStateTransition("Cannot confirm a canceled reservation")

        reservation.status = ReservationStatus.CONFIRMED.value
        session.flush()
        return _to_aggregate(reservation)


def cancel_reservation(session: Session, reservation_id: UUID) -> ReservationAggregate:
    with session.begin():
        reservation = _get_locked_reservation(session, reservation_id)

        if reservation.status == ReservationStatus.CANCELED.value:
            return _to_aggregate(reservation)

        if reservation.status == ReservationStatus.CONFIRMED.value:
            raise IllegalStateTransition("Cannot cancel a confirmed reservation")

        inventory_update = (
            update(InventoryItem)
            .where(
                InventoryItem.sku == reservation.sku,
                InventoryItem.reserved_quantity >= reservation.quantity,
            )
            .values(reserved_quantity=InventoryItem.reserved_quantity - reservation.quantity)
        )
        result = session.execute(inventory_update)
        if result.rowcount != 1:
            raise IllegalStateTransition("Inventory invariant violation during cancel")

        reservation.status = ReservationStatus.CANCELED.value
        session.flush()
        return _to_aggregate(reservation)
