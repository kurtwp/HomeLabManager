"""ControllerFirmware model — tracks UniFi controller/application update availability.

These are the UniFi *applications* (Network, Protect, Access, Talk, etc.) running
on a console, as reported by the Site Manager cloud API (api.ui.com). The local
Integration API cannot see controller-level updates, only per-device firmware.
"""

from datetime import datetime, timezone

from sqlalchemy import String, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.database.db import Base


class ControllerFirmware(Base):
    """Tracks controller/application versions for a UniFi console."""

    __tablename__ = "controller_firmware"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    host_name: Mapped[str] = mapped_column(String(255), nullable=False)
    controller_name: Mapped[str] = mapped_column(String(100), nullable=False)
    current_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    available_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    update_available: Mapped[bool] = mapped_column(Boolean, default=False)
    last_checked: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<ControllerFirmware({self.host_name}/{self.controller_name} "
            f"v={self.current_version})>"
        )
