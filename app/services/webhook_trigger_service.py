"""Webhook Triggers service — fire webhooks on configurable system events."""

from datetime import datetime, timezone

import httpx
from sqlalchemy import String, Integer, DateTime, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, Session

from app.database.db import Base, SessionLocal


# --- Model ---

class WebhookTrigger(Base):
    """A user-defined webhook trigger rule."""

    __tablename__ = "webhook_triggers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # Events: ip_inactive, ip_active, new_device, unknown_mac, capacity_warning,
    #         scan_complete, monitor_down, monitor_up, firmware_update
    webhook_url: Mapped[str] = mapped_column(String(500), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    filter_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Optional filter: network name, IP prefix, device type, etc.
    last_fired: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    fire_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return f"<WebhookTrigger(name={self.name!r}, event={self.event_type})>"


# --- Available Events ---

EVENT_TYPES = {
    "monitor_down": "Monitor goes down (ping or port)",
    "monitor_up": "Monitor recovers",
    "ip_inactive": "IP address marked inactive",
    "ip_active": "New IP discovered / becomes active",
    "new_device": "New device added to inventory",
    "unknown_mac": "Unknown MAC address detected",
    "capacity_warning": "Network utilization exceeds 80%",
    "scan_complete": "Network scan completed",
    "firmware_update": "Firmware update available",
}


# --- CRUD ---

def get_all_triggers(session: Session) -> list[WebhookTrigger]:
    """Get all webhook triggers."""
    return session.query(WebhookTrigger).order_by(WebhookTrigger.name).all()


def get_triggers_for_event(session: Session, event_type: str) -> list[WebhookTrigger]:
    """Get enabled triggers matching an event type."""
    return (
        session.query(WebhookTrigger)
        .filter(WebhookTrigger.event_type == event_type, WebhookTrigger.is_enabled == True)
        .all()
    )


def create_trigger(session: Session, name: str, event_type: str, webhook_url: str,
                   filter_value: str | None = None) -> WebhookTrigger:
    """Create a new webhook trigger."""
    trigger = WebhookTrigger(
        name=name,
        event_type=event_type,
        webhook_url=webhook_url,
        filter_value=filter_value,
    )
    session.add(trigger)
    session.commit()
    return trigger


def update_trigger(session: Session, trigger_id: int, **kwargs) -> WebhookTrigger | None:
    """Update an existing trigger."""
    trigger = session.query(WebhookTrigger).filter(WebhookTrigger.id == trigger_id).first()
    if not trigger:
        return None
    for key, value in kwargs.items():
        if hasattr(trigger, key):
            setattr(trigger, key, value)
    session.commit()
    return trigger


def delete_trigger(session: Session, trigger_id: int) -> bool:
    """Delete a trigger."""
    trigger = session.query(WebhookTrigger).filter(WebhookTrigger.id == trigger_id).first()
    if trigger:
        session.delete(trigger)
        session.commit()
        return True
    return False


# --- Fire Logic ---

def fire_event(event_type: str, payload: dict) -> list[dict]:
    """
    Fire all enabled triggers matching the event type.

    Args:
        event_type: One of the EVENT_TYPES keys
        payload: Event data to send in the webhook body

    Returns:
        List of results: [{"trigger": str, "success": bool, "error": str|None}]
    """
    session = SessionLocal()
    results = []
    try:
        triggers = get_triggers_for_event(session, event_type)

        for trigger in triggers:
            # Apply filter if set
            if trigger.filter_value:
                # Simple string matching on any payload value
                filter_match = any(
                    trigger.filter_value.lower() in str(v).lower()
                    for v in payload.values()
                )
                if not filter_match:
                    continue

            # Build webhook payload
            webhook_data = {
                "event": event_type,
                "trigger_name": trigger.name,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "Home Lab Manager",
                **payload,
            }

            # Format for specific platforms
            url = trigger.webhook_url
            if "discord.com/api/webhooks" in url:
                # Discord expects {"content": "text"}
                text_parts = [f"**[{event_type}]** {trigger.name}"]
                for k, v in payload.items():
                    if v is not None:
                        text_parts.append(f"• {k}: {v}")
                send_data = {"content": "\n".join(text_parts)}
            elif "hooks.slack.com" in url:
                # Slack expects {"text": "text"}
                text_parts = [f"*[{event_type}]* {trigger.name}"]
                for k, v in payload.items():
                    if v is not None:
                        text_parts.append(f"• {k}: {v}")
                send_data = {"text": "\n".join(text_parts)}
            else:
                send_data = webhook_data

            # Send webhook
            try:
                r = httpx.post(url, json=send_data, timeout=10.0)
                r.raise_for_status()
                results.append({"trigger": trigger.name, "success": True, "error": None})
            except Exception as e:
                results.append({"trigger": trigger.name, "success": False, "error": str(e)})

            # Update trigger stats
            trigger.last_fired = datetime.now(timezone.utc)
            trigger.fire_count += 1

        session.commit()
    except Exception as e:
        session.rollback()
        results.append({"trigger": "system", "success": False, "error": str(e)})
    finally:
        session.close()

    return results


def test_trigger(session: Session, trigger_id: int) -> dict:
    """Send a test payload to a trigger's webhook URL."""
    trigger = session.query(WebhookTrigger).filter(WebhookTrigger.id == trigger_id).first()
    if not trigger:
        return {"success": False, "error": "Trigger not found"}

    test_payload = {
        "event": trigger.event_type,
        "trigger_name": trigger.name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "Home Lab Manager",
        "test": True,
        "message": f"Test webhook for trigger '{trigger.name}' ({trigger.event_type})",
    }

    # Format for specific platforms
    url = trigger.webhook_url
    if "discord.com/api/webhooks" in url:
        send_data = {"content": f"✅ **Test** — Trigger: {trigger.name} ({trigger.event_type})"}
    elif "hooks.slack.com" in url:
        send_data = {"text": f"✅ *Test* — Trigger: {trigger.name} ({trigger.event_type})"}
    else:
        send_data = test_payload

    try:
        r = httpx.post(url, json=send_data, timeout=10.0)
        r.raise_for_status()
        return {"success": True, "error": None, "status_code": r.status_code}
    except Exception as e:
        return {"success": False, "error": str(e)}
