"""Uptime monitoring service — pings hosts and tracks status."""

import subprocess
import re
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.uptime_monitor import MonitoredHost, UptimeEvent
from app.database.db import SessionLocal


def add_monitor(session: Session, ip_address: str, name: str, check_interval: int = 60) -> MonitoredHost:
    """Add a new host to uptime monitoring."""
    host = MonitoredHost(
        ip_address=ip_address,
        name=name,
        check_interval=check_interval,
    )
    session.add(host)
    session.commit()
    return host


def remove_monitor(session: Session, monitor_id: int) -> bool:
    """Remove a host from monitoring."""
    host = session.query(MonitoredHost).filter(MonitoredHost.id == monitor_id).first()
    if not host:
        return False
    # Delete events too
    session.query(UptimeEvent).filter(UptimeEvent.host_id == monitor_id).delete()
    session.delete(host)
    session.commit()
    return True


def get_all_monitors(session: Session) -> list[MonitoredHost]:
    """Get all monitored hosts."""
    return session.query(MonitoredHost).order_by(MonitoredHost.name).all()


def get_monitor_by_id(session: Session, monitor_id: int) -> MonitoredHost | None:
    """Get a single monitor by ID."""
    return session.query(MonitoredHost).filter(MonitoredHost.id == monitor_id).first()


def get_events_for_host(session: Session, host_id: int, limit: int = 50) -> list[UptimeEvent]:
    """Get recent uptime events for a host."""
    return (
        session.query(UptimeEvent)
        .filter(UptimeEvent.host_id == host_id)
        .order_by(UptimeEvent.timestamp.desc())
        .limit(limit)
        .all()
    )


def check_host(ip_address: str, timeout: int = 2) -> tuple[bool, float | None]:
    """
    Ping a host and return (is_up, latency_ms).
    """
    try:
        result = subprocess.run(
            ["ping", "-c", "1", "-W", str(timeout), ip_address],
            capture_output=True, text=True, timeout=timeout + 2,
        )
        if result.returncode == 0:
            match = re.search(r"time=([\d.]+)", result.stdout)
            latency = float(match.group(1)) if match else 0.0
            return True, latency
    except (subprocess.TimeoutExpired, OSError):
        pass
    return False, None


def run_checks():
    """
    Run uptime checks on all enabled monitors.
    Called by the scheduler periodically.
    """
    session = SessionLocal()
    try:
        monitors = (
            session.query(MonitoredHost)
            .filter(MonitoredHost.is_enabled == True)
            .all()
        )

        now = datetime.now(timezone.utc)

        for host in monitors:
            # Check if it's time for this host's check
            if host.last_check:
                elapsed = (now - host.last_check.replace(tzinfo=timezone.utc)).total_seconds()
                if elapsed < host.check_interval:
                    continue

            is_up, latency = check_host(host.ip_address)
            previous_status = host.current_status

            host.total_checks += 1
            host.last_check = now

            if is_up:
                host.current_status = "up"
                host.total_up += 1
                host.last_seen_up = now
                host.consecutive_failures = 0

                # Log recovery event
                if previous_status == "down":
                    event = UptimeEvent(
                        host_id=host.id,
                        event_type="recovered",
                        latency_ms=latency,
                        details=f"Host recovered after {host.consecutive_failures} failed checks",
                    )
                    session.add(event)
            else:
                host.current_status = "down"
                host.consecutive_failures += 1
                host.last_seen_down = now

                # Log down event (only on first failure or every 10th)
                if previous_status != "down" or host.consecutive_failures == 1:
                    event = UptimeEvent(
                        host_id=host.id,
                        event_type="down",
                        details=f"Host not responding (failure #{host.consecutive_failures})",
                    )
                    session.add(event)

        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Uptime check error: {e}")
    finally:
        session.close()
