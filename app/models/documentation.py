"""Knowledge base / documentation model."""

from datetime import datetime, timezone
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column
import enum

from app.database.db import Base


class DocCategory(enum.Enum):
    """Categories for knowledge base articles."""
    HOWTO = "how-to"
    TROUBLESHOOTING = "troubleshooting"
    RUNBOOK = "runbook"
    GENERAL = "general"


class Documentation(Base):
    """A knowledge base article or documentation entry."""

    __tablename__ = "documentation"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False, default="")
    category: Mapped[DocCategory] = mapped_column(
        Enum(DocCategory), default=DocCategory.GENERAL
    )

    # Optional links to specific entities
    linked_ip_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("ip_addresses.id"), nullable=True
    )
    linked_device_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("devices.id"), nullable=True
    )
    linked_network_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("networks.id"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<Documentation(title={self.title!r}, category={self.category.value})>"
