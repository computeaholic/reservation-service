from enum import Enum


class ReservationStatus(str, Enum):
    ACTIVE = "active"
    CONFIRMED = "confirmed"
    CANCELED = "canceled"
