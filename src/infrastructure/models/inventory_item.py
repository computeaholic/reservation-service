import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from infrastructure.db.base import Base


class InventoryItem(Base):
    __tablename__ = "inventory_items"
    __table_args__ = (
        UniqueConstraint("sku", name="uq_inventory_items_sku"),
        CheckConstraint(
            "total_quantity >= 0",
            name="ck_inventory_items_total_quantity_non_negative",
        ),
        CheckConstraint(
            "reserved_quantity >= 0",
            name="ck_inventory_items_reserved_quantity_non_negative",
        ),
        CheckConstraint(
            "reserved_quantity <= total_quantity",
            name="ck_inventory_items_reserved_quantity_lte_total_quantity",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sku: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    total_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    reserved_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
