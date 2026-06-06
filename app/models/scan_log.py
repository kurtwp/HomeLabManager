"""Network scan log model."""

from datetime import datetime, timezone
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.database.db import Base


class ScanLog(Base):
    """Records each network scan event and its results."""

    __tablename__ = "scan_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    network_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("networks.id"), nullable=False
    )
    hosts_found: Mapped[int] = mapped_column(Integer, default=0)
    hosts_added: Mapped[int] = mapped_column(Integer, default=0)
    hosts_removed: Mapped[int] = mapped_column(Integer, default=0)
    duration_seconds: Mapped[float | None] = mapped_column(nullable=True)
    scan_type: Mapped[str] = mapped_column(String(50), default="ping")
    details: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON summary
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<ScanLog(network_id={self.network_id}, found={self.hosts_found}, "
            f"added={self.hosts_added}, removed={self.hosts_removed})>"
        )
