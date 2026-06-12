"""IP Address model."""

from datetime import datetime, timezone
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.database.db import Base


class AssignmentType(enum.Enum):
    """How an IP address is assigned."""
    STATIC = "static"
    DHCP = "dhcp"
    RESERVED = "reserved"


class IPStatus(enum.Enum):
    """Current status of an IP address."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    UNKNOWN = "unknown"


class IPAddress(Base):
    """Represents a single IP address entry."""

    __tablename__ = "ip_addresses"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    address: Mapped[str] = mapped_column(String(45), nullable=False)
    hostname: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mac_address: Mapped[str | None] = mapped_column(String(17), nullable=True)
    assignment_type: Mapped[AssignmentType] = mapped_column(
        Enum(AssignmentType), default=AssignmentType.DHCP
    )
    status: Mapped[IPStatus] = mapped_column(
        Enum(IPStatus), default=IPStatus.UNKNOWN
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_seen: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    source: Mapped[str | None] = mapped_column(String(50), nullable=True)  # unifi_client, unifi_device, nmap_scan, manual

    # Foreign keys
    network_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("networks.id"), nullable=False
    )
    device_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("devices.id"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    network: Mapped["Network"] = relationship(back_populates="ip_addresses")  # noqa: F821
    device: Mapped["Device | None"] = relationship(back_populates="ip_addresses")  # noqa: F821
    tags: Mapped[list["Tag"]] = relationship(  # noqa: F821
        secondary="ip_tags", back_populates="ip_addresses"
    )

    def __repr__(self) -> str:
        return f"<IPAddress(address={self.address!r}, hostname={self.hostname!r})>"
