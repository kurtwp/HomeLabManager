"""Device and DeviceType models."""

from datetime import datetime, timezone
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.db import Base


class DeviceType(Base):
    """Category of device (switch, AP, server, printer, etc.)."""

    __tablename__ = "device_types"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    devices: Mapped[list["Device"]] = relationship(back_populates="device_type")

    def __repr__(self) -> str:
        return f"<DeviceType(name={self.name!r})>"


class Device(Base):
    """Physical or virtual device in the home lab."""

    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    manufacturer: Mapped[str | None] = mapped_column(String(255), nullable=True)
    model: Mapped[str | None] = mapped_column(String(255), nullable=True)
    serial_number: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mac_address: Mapped[str | None] = mapped_column(String(17), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Foreign keys
    device_type_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("device_types.id"), nullable=True
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
    device_type: Mapped["DeviceType | None"] = relationship(back_populates="devices")
    ip_addresses: Mapped[list["IPAddress"]] = relationship(  # noqa: F821
        back_populates="device"
    )
    tags: Mapped[list["Tag"]] = relationship(  # noqa: F821
        secondary="device_tags", back_populates="devices"
    )

    def __repr__(self) -> str:
        return f"<Device(name={self.name!r}, type={self.device_type_id})>"
