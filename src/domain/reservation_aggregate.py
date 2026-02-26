from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from .exceptions import IllegalStateTransition
from .reservation_status import ReservationStatus


@dataclass
class Reservation:
    id: UUID
    sku: str
    quantity: int
    status: ReservationStatus
    idempotency_key: str
    created_at: datetime
    updated_at: datetime

    def confirm(self) -> "Reservation":
        if self.status == ReservationStatus.ACTIVE:
            self.status = ReservationStatus.CONFIRMED
            return self
        if self.status == ReservationStatus.CONFIRMED:
            return self
        raise IllegalStateTransition("Cannot confirm a canceled reservation")

    def cancel(self) -> "Reservation":
        if self.status == ReservationStatus.ACTIVE:
            self.status = ReservationStatus.CANCELED
            return self
        if self.status == ReservationStatus.CANCELED:
            return self
        raise IllegalStateTransition("Cannot cancel a confirmed reservation")
