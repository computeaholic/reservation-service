# ruff: noqa: I001

"""add reserved quantity upper bound constraint

Revision ID: 20260920_000002
Revises: 20260225_000001
Create Date: 2026-09-20 00:00:02
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260920_000002"
down_revision: str | None = "20260225_000001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_check_constraint(
        "ck_inventory_items_reserved_quantity_lte_total_quantity",
        "inventory_items",
        "reserved_quantity <= total_quantity",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_inventory_items_reserved_quantity_lte_total_quantity",
        "inventory_items",
        type_="check",
    )
