"""Uptime monitoring models — track status of critical IPs."""

from datetime import datetime, timezone
from sqlalchemy import String, Integer, Float, DateTime, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.db import Base


class MonitoredHost(Base):
    """A host being actively monitored for uptime."""

    __tablename__ = "monitored_hosts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    check_interval: Mapped[int] = mapped_column(Integer, default=60)  # seconds
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    current_status: Mapped[str] = mapped_column(String(20), default="unknown")  # up, down, unknown
    last_check: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_seen_up: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_seen_down: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    consecutive_failures: Mapped[int] = mapped_column(Integer, default=0)
    total_checks: Mapped[int] = mapped_column(Integer, default=0)
    total_up: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    @property
    def uptime_percent(self) -> float:
        if self.total_checks == 0:
            return 0.0
        return round((self.total_up / self.total_checks) * 100, 2)

    def __repr__(self) -> str:
        return f"<MonitoredHost({self.name} {self.ip_address} status={self.current_status})>"


class UptimeEvent(Base):
    """Records status change events (up→down or down→up)."""

    __tablename__ = "uptime_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    host_id: Mapped[int] = mapped_column(Integer, nullable=False)
    event_type: Mapped[str] = mapped_column(String(20), nullable=False)  # "down", "up", "recovered"
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<UptimeEvent(host={self.host_id} type={self.event_type})>"
