class DomainError(Exception):
    pass


class InvalidQuantity(DomainError):
    pass


class ReservationNotFound(DomainError):
    pass


class SkuNotFound(DomainError):
    pass


class InsufficientInventory(DomainError):
    pass


class IllegalStateTransition(DomainError):
    pass


class IdempotencyConflict(DomainError):
    pass
