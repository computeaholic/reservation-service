# Reservation Service Failure Matrix

## Inventory
- [x] Over-reserve prevented
- [x] Negative inventory prevented
- [x] Cancel restores inventory exactly once

## Idempotency
- [x] Replay returns same reservation
- [x] Replay does not double reserve

## State Transitions
- [x] Confirm -> Confirm is idempotent
- [x] Cancel -> Cancel is idempotent
- [x] Confirm -> Cancel raises
- [x] Cancel -> Confirm raises

## Errors
- [x] SKU not found
- [x] Insufficient inventory
- [x] Reservation not found

## Concurrency
- [x] Two concurrent creates cannot exceed total_quantity
