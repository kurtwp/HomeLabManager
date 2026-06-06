"""Changelog / audit history model."""

from datetime import datetime, timezone
from sqlalchemy import String, Integer, Text, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column
import enum

from app.database.db import Base


class EntityType(enum.Enum):
    """Type of entity that was modified."""
    NETWORK = "network"
    IP_ADDRESS = "ip_address"
    DEVICE = "device"
    DOCUMENTATION = "documentation"
    TAG = "tag"


class ActionType(enum.Enum):
    """Type of action performed."""
    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"


class Changelog(Base):
    """Tracks all modifications to entities for audit history."""

    __tablename__ = "changelog"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    entity_type: Mapped[EntityType] = mapped_column(Enum(EntityType), nullable=False)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    entity_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    action: Mapped[ActionType] = mapped_column(Enum(ActionType), nullable=False)
    old_values: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    new_values: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return (
            f"<Changelog({self.action.value} {self.entity_type.value} "
            f"id={self.entity_id} @ {self.timestamp})>"
        )
