"""Notification service — sends alerts via email, webhook, or Pushover.

Supports multiple channels. Configure via .env variables.
"""

import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone

import httpx

from app.database.db import Base, SessionLocal
from sqlalchemy import String, Integer, Text, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column


# --- Notification Log Model ---

class NotificationLog(Base):
    """Stores history of sent notifications."""

    __tablename__ = "notification_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    channel: Mapped[str] = mapped_column(String(50), nullable=False)  # email, webhook, pushover
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return f"<NotificationLog(channel={self.channel}, subject={self.subject!r})>"


# --- Configuration ---

def _get_config() -> dict:
    """Load notification config from environment."""
    return {
        "enabled": os.getenv("NOTIFICATIONS_ENABLED", "false").lower() == "true",
        # Email (SMTP)
        "email_enabled": os.getenv("NOTIFY_EMAIL_ENABLED", "false").lower() == "true",
        "smtp_host": os.getenv("NOTIFY_SMTP_HOST", ""),
        "smtp_port": int(os.getenv("NOTIFY_SMTP_PORT", "587")),
        "smtp_user": os.getenv("NOTIFY_SMTP_USER", ""),
        "smtp_pass": os.getenv("NOTIFY_SMTP_PASS", ""),
        "smtp_from": os.getenv("NOTIFY_SMTP_FROM", ""),
        "smtp_to": os.getenv("NOTIFY_SMTP_TO", ""),  # comma-separated
        "smtp_tls": os.getenv("NOTIFY_SMTP_TLS", "true").lower() == "true",
        # Webhook (generic)
        "webhook_enabled": os.getenv("NOTIFY_WEBHOOK_ENABLED", "false").lower() == "true",
        "webhook_url": os.getenv("NOTIFY_WEBHOOK_URL", ""),
        # Pushover
        "pushover_enabled": os.getenv("NOTIFY_PUSHOVER_ENABLED", "false").lower() == "true",
        "pushover_token": os.getenv("NOTIFY_PUSHOVER_TOKEN", ""),
        "pushover_user": os.getenv("NOTIFY_PUSHOVER_USER", ""),
    }


def is_notifications_enabled() -> bool:
    """Check if notifications are enabled globally."""
    return _get_config()["enabled"]


def get_enabled_channels() -> list[str]:
    """Return list of enabled notification channels."""
    config = _get_config()
    channels = []
    if config["email_enabled"]:
        channels.append("email")
    if config["webhook_enabled"]:
        channels.append("webhook")
    if config["pushover_enabled"]:
        channels.append("pushover")
    return channels


# --- Send Functions ---

def send_notification(subject: str, message: str, priority: str = "normal") -> list[dict]:
    """
    Send a notification through all enabled channels.

    Args:
        subject: Short summary/title
        message: Full message body
        priority: "low", "normal", "high", "critical"

    Returns:
        List of results per channel: [{"channel": str, "success": bool, "error": str|None}]
    """
    config = _get_config()
    if not config["enabled"]:
        return []

    results = []

    if config["email_enabled"]:
        results.append(_send_email(config, subject, message))

    if config["webhook_enabled"]:
        results.append(_send_webhook(config, subject, message, priority))

    if config["pushover_enabled"]:
        results.append(_send_pushover(config, subject, message, priority))

    # Log all notifications
    session = SessionLocal()
    try:
        for result in results:
            log = NotificationLog(
                channel=result["channel"],
                subject=subject,
                message=message,
                success=result["success"],
                error=result.get("error"),
            )
            session.add(log)
        session.commit()
    except Exception:
        session.rollback()
    finally:
        session.close()

    return results


def _send_email(config: dict, subject: str, message: str) -> dict:
    """Send notification via SMTP email."""
    try:
        msg = MIMEMultipart()
        msg["From"] = config["smtp_from"]
        msg["To"] = config["smtp_to"]
        msg["Subject"] = f"[HomeLab] {subject}"

        body = MIMEText(message, "plain")
        msg.attach(body)

        if config["smtp_tls"]:
            server = smtplib.SMTP(config["smtp_host"], config["smtp_port"])
            server.starttls()
        else:
            server = smtplib.SMTP(config["smtp_host"], config["smtp_port"])

        if config["smtp_user"] and config["smtp_pass"]:
            server.login(config["smtp_user"], config["smtp_pass"])

        recipients = [r.strip() for r in config["smtp_to"].split(",")]
        server.sendmail(config["smtp_from"], recipients, msg.as_string())
        server.quit()

        return {"channel": "email", "success": True, "error": None}
    except Exception as e:
        return {"channel": "email", "success": False, "error": str(e)}


def _send_webhook(config: dict, subject: str, message: str, priority: str) -> dict:
    """Send notification via generic webhook (JSON POST)."""
    try:
        payload = {
            "subject": subject,
            "message": message,
            "priority": priority,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "HomeLab Manager",
        }
        r = httpx.post(
            config["webhook_url"],
            json=payload,
            timeout=10.0,
        )
        r.raise_for_status()
        return {"channel": "webhook", "success": True, "error": None}
    except Exception as e:
        return {"channel": "webhook", "success": False, "error": str(e)}


def _send_pushover(config: dict, subject: str, message: str, priority: str) -> dict:
    """Send notification via Pushover API."""
    try:
        # Map priority to Pushover levels
        pushover_priority = {
            "low": -1,
            "normal": 0,
            "high": 1,
            "critical": 2,
        }.get(priority, 0)

        payload = {
            "token": config["pushover_token"],
            "user": config["pushover_user"],
            "title": subject,
            "message": message,
            "priority": pushover_priority,
        }

        # Critical priority requires retry/expire params
        if pushover_priority == 2:
            payload["retry"] = 60
            payload["expire"] = 3600

        r = httpx.post(
            "https://api.pushover.net/1/messages.json",
            data=payload,
            timeout=10.0,
        )
        r.raise_for_status()
        return {"channel": "pushover", "success": True, "error": None}
    except Exception as e:
        return {"channel": "pushover", "success": False, "error": str(e)}


# --- Convenience Functions for Common Alerts ---

def notify_host_down(host_name: str, ip_address: str, consecutive_failures: int):
    """Send alert when an uptime-monitored host goes down."""
    subject = f"🔴 Host DOWN: {host_name} ({ip_address})"
    message = (
        f"Host '{host_name}' at {ip_address} is not responding.\n"
        f"Consecutive failures: {consecutive_failures}\n"
        f"Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"
    )
    return send_notification(subject, message, priority="high")


def notify_host_recovered(host_name: str, ip_address: str, downtime_checks: int):
    """Send alert when a host recovers from being down."""
    subject = f"🟢 Host RECOVERED: {host_name} ({ip_address})"
    message = (
        f"Host '{host_name}' at {ip_address} is back online.\n"
        f"Was down for {downtime_checks} check(s).\n"
        f"Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"
    )
    return send_notification(subject, message, priority="normal")


def notify_firmware_update(device_name: str, current_version: str, available_version: str):
    """Send alert when a firmware update is available."""
    subject = f"📦 Firmware update: {device_name}"
    message = (
        f"Device '{device_name}' has a firmware update available.\n"
        f"Current: {current_version}\n"
        f"Available: {available_version}\n"
        f"Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"
    )
    return send_notification(subject, message, priority="low")


def get_notification_history(limit: int = 50) -> list[NotificationLog]:
    """Get recent notification log entries."""
    session = SessionLocal()
    try:
        return (
            session.query(NotificationLog)
            .order_by(NotificationLog.timestamp.desc())
            .limit(limit)
            .all()
        )
    finally:
        session.close()
