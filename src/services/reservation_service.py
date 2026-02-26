from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from domain.exceptions import IllegalStateTransition, InsufficientInventory, ReservationNotFound
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


def create_reservation(
    session: Session,
    *,
    sku: str,
    quantity: int,
    idempotency_key: str,
) -> ReservationAggregate:
    with session.begin():
        existing = session.execute(
            select(Reservation).where(Reservation.idempotency_key == idempotency_key)
        ).scalar_one_or_none()
        if existing is not None:
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
                raise ReservationNotFound("SKU not found")
            raise InsufficientInventory("Insufficient inventory")

        reservation = Reservation(
            sku=sku,
            quantity=quantity,
            status=ReservationStatus.ACTIVE.value,
            idempotency_key=idempotency_key,
        )
        session.add(reservation)
        session.flush()
        return _to_aggregate(reservation)


def confirm_reservation(session: Session, reservation_id: UUID) -> ReservationAggregate:
    with session.begin():
        reservation = session.get(Reservation, reservation_id)
        if reservation is None:
            raise ReservationNotFound("Reservation not found")

        if reservation.status == ReservationStatus.CONFIRMED.value:
            return _to_aggregate(reservation)

        if reservation.status == ReservationStatus.CANCELED.value:
            raise IllegalStateTransition("Cannot confirm a canceled reservation")

        reservation.status = ReservationStatus.CONFIRMED.value
        session.flush()
        return _to_aggregate(reservation)


def cancel_reservation(session: Session, reservation_id: UUID) -> ReservationAggregate:
    with session.begin():
        reservation = session.get(Reservation, reservation_id)
        if reservation is None:
            raise ReservationNotFound("Reservation not found")

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
