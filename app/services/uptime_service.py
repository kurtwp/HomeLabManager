"""Uptime monitoring service — pings hosts and tracks status."""

import subprocess
import re
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.uptime_monitor import MonitoredHost, UptimeEvent, PingResult
from app.database.db import SessionLocal


def add_monitor(session: Session, ip_address: str, name: str, check_interval: int = 60,
               max_retries: int = 3, retry_interval: int = 30) -> MonitoredHost:
    """Add a new host to uptime monitoring."""
    host = MonitoredHost(
        ip_address=ip_address,
        name=name,
        check_interval=check_interval,
        max_retries=max_retries,
        retry_interval=retry_interval,
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


def update_monitor(session: Session, monitor_id: int, name: str | None = None,
                   ip_address: str | None = None, check_interval: int | None = None,
                   is_enabled: bool | None = None, max_retries: int | None = None,
                   retry_interval: int | None = None) -> MonitoredHost | None:
    """Update an existing monitored host."""
    host = session.query(MonitoredHost).filter(MonitoredHost.id == monitor_id).first()
    if not host:
        return None
    if name is not None:
        host.name = name
    if ip_address is not None:
        host.ip_address = ip_address
    if check_interval is not None:
        host.check_interval = check_interval
    if is_enabled is not None:
        host.is_enabled = is_enabled
    if max_retries is not None:
        host.max_retries = max_retries
    if retry_interval is not None:
        host.retry_interval = retry_interval
    session.commit()
    return host


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


def get_ping_history(session: Session, host_id: int, hours: int = 6) -> list[PingResult]:
    """Get ping results for the last N hours for graphing."""
    from datetime import timedelta
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    return (
        session.query(PingResult)
        .filter(PingResult.host_id == host_id, PingResult.timestamp >= cutoff)
        .order_by(PingResult.timestamp.asc())
        .all()
    )


def get_ping_stats(session: Session, host_id: int, hours: int = 24) -> dict:
    """Calculate ping statistics for a host over the last N hours."""
    from datetime import timedelta
    from sqlalchemy import func

    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    results = (
        session.query(PingResult)
        .filter(PingResult.host_id == host_id, PingResult.timestamp >= cutoff)
        .all()
    )

    if not results:
        return {"avg_latency": None, "min_latency": None, "max_latency": None,
                "total_checks": 0, "up_checks": 0, "uptime_percent": 0.0}

    latencies = [r.latency_ms for r in results if r.latency_ms is not None]
    up_checks = sum(1 for r in results if r.is_up)
    total = len(results)

    return {
        "avg_latency": round(sum(latencies) / len(latencies), 1) if latencies else None,
        "min_latency": round(min(latencies), 1) if latencies else None,
        "max_latency": round(max(latencies), 1) if latencies else None,
        "current_latency": round(latencies[-1], 1) if latencies else None,
        "total_checks": total,
        "up_checks": up_checks,
        "uptime_percent": round((up_checks / total) * 100, 2) if total > 0 else 0.0,
    }


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

            # Store ping result for latency history/graphing
            ping_record = PingResult(
                host_id=host.id,
                timestamp=now,
                is_up=is_up,
                latency_ms=latency,
            )
            session.add(ping_record)

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

                    # Send recovery notification
                    try:
                        from app.services.notification_service import notify_host_recovered, is_notifications_enabled
                        if is_notifications_enabled():
                            notify_host_recovered(host.name, host.ip_address, host.consecutive_failures)
                    except Exception as notify_err:
                        print(f"Notification error (recovery): {notify_err}")
            else:
                host.consecutive_failures += 1
                host.last_seen_down = now

                # Only mark as fully "down" after max_retries consecutive failures
                max_retries = host.max_retries if hasattr(host, 'max_retries') and host.max_retries else 3

                if host.consecutive_failures >= max_retries:
                    # Confirmed down — mark status and notify
                    if previous_status != "down":
                        host.current_status = "down"
                        event = UptimeEvent(
                            host_id=host.id,
                            event_type="down",
                            details=f"Host not responding after {host.consecutive_failures} retries",
                        )
                        session.add(event)

                        # Send down notification
                        try:
                            from app.services.notification_service import notify_host_down, is_notifications_enabled
                            if is_notifications_enabled():
                                notify_host_down(host.name, host.ip_address, host.consecutive_failures)
                        except Exception as notify_err:
                            print(f"Notification error (down): {notify_err}")
                    else:
                        host.current_status = "down"
                else:
                    # Still in retry phase — use retry_interval for next check timing
                    # Override last_check to trigger a faster recheck
                    retry_interval = host.retry_interval if hasattr(host, 'retry_interval') and host.retry_interval else 30
                    from datetime import timedelta
                    host.last_check = now - timedelta(seconds=(host.check_interval - retry_interval))

        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Uptime check error: {e}")
    finally:
        session.close()
