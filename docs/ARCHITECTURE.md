# Architecture Notes

## Domain invariants

- `reserved_quantity` must stay between `0` and `total_quantity`.
- A reservation create request is identified by `idempotency_key + sku + quantity`.
- Reservation states are `active`, `confirmed`, and `canceled`.

## Transaction boundary

Each mutating service function owns its own SQLAlchemy transaction with `with session.begin():`.

- `create_reservation()` inserts or replays a reservation and applies the inventory hold atomically.
- `confirm_reservation()` changes only reservation state.
- `cancel_reservation()` restores inventory and changes reservation state atomically.

## Concurrency strategy

- Create uses an atomic conditional `UPDATE` on inventory to prevent oversubscription.
- Confirm and cancel use `SELECT ... FOR UPDATE` on the reservation row so terminal transitions cannot overwrite one another.

## Idempotency strategy

- A unique constraint protects `idempotency_key` at the database level.
- Equivalent replays return the original reservation.
- Conflicting payload reuse raises `IdempotencyConflict`.
- Concurrent equivalent duplicate-key creates normalize to one row and one inventory effect.

## State transitions

- `active -> confirmed`
- `active -> canceled`
- `confirmed -> confirmed` is idempotent
- `canceled -> canceled` is idempotent
- `confirmed -> canceled` is illegal
- `canceled -> confirmed` is illegal

## Known limits

- No HTTP or RPC interface.
- No background expiration.
- No multi-warehouse allocation.
- No distributed coordination beyond a single PostgreSQL database.