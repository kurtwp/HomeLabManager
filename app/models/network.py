"""Network/VLAN model."""

from datetime import datetime, timezone
from sqlalchemy import String, Integer, Text, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.db import Base


class Network(Base):
    """Represents a network subnet or VLAN."""

    __tablename__ = "networks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    cidr: Mapped[str] = mapped_column(String(43), nullable=False, unique=True)
    vlan_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gateway: Mapped[str | None] = mapped_column(String(45), nullable=True)
    dns_servers: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    parent_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    ip_addresses: Mapped[list["IPAddress"]] = relationship(  # noqa: F821
        back_populates="network", cascade="all, delete-orphan"
    )
    tags: Mapped[list["Tag"]] = relationship(  # noqa: F821
        secondary="network_tags", back_populates="networks"
    )

    def __repr__(self) -> str:
        return f"<Network(name={self.name!r}, cidr={self.cidr!r}, vlan={self.vlan_id})>"
