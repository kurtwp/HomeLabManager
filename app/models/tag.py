"""Tag/label model with many-to-many relationships."""

from sqlalchemy import String, Integer, Table, Column, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.db import Base


# Association tables for many-to-many relationships
ip_tags = Table(
    "ip_tags",
    Base.metadata,
    Column("ip_address_id", Integer, ForeignKey("ip_addresses.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True),
)

device_tags = Table(
    "device_tags",
    Base.metadata,
    Column("device_id", Integer, ForeignKey("devices.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True),
)

network_tags = Table(
    "network_tags",
    Base.metadata,
    Column("network_id", Integer, ForeignKey("networks.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True),
)


class Tag(Base):
    """A label/tag that can be applied to IPs, devices, or networks."""

    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    color: Mapped[str] = mapped_column(String(7), default="#1976d2")  # hex color

    # Relationships
    ip_addresses: Mapped[list["IPAddress"]] = relationship(  # noqa: F821
        secondary=ip_tags, back_populates="tags"
    )
    devices: Mapped[list["Device"]] = relationship(  # noqa: F821
        secondary=device_tags, back_populates="tags"
    )
    networks: Mapped[list["Network"]] = relationship(  # noqa: F821
        secondary=network_tags, back_populates="tags"
    )

    def __repr__(self) -> str:
        return f"<Tag(name={self.name!r}, color={self.color!r})>"
