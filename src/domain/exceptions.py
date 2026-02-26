class DomainError(Exception):
    pass


class ReservationNotFound(DomainError):
    pass


class SkuNotFound(DomainError):
    pass


class InsufficientInventory(DomainError):
    pass


class IllegalStateTransition(DomainError):
    pass


class DuplicateIdempotencyKey(DomainError):
    pass


class DatabaseUnavailable(DomainError):
    pass


class TimeoutError(DomainError):
    pass
