"""Notifications settings and history page."""

from nicegui import ui

from app.services.notification_service import (
    is_notifications_enabled,
    get_enabled_channels,
    get_notification_history,
    send_notification,
)
from app.pages.layout import page_layout


def render_notifications():
    """Render the notifications settings and history page."""
    page_layout()

    with ui.column().classes("page-container w-full"):
        ui.label("Notifications").classes("text-3xl font-bold")
        ui.label("Configure alerts for uptime events and firmware updates.").classes(
            "text-gray-500 mb-4"
        )

        ui.separator()

        # Status overview
        with ui.card().classes("w-full mt-4"):
            ui.label("Status").classes("text-lg font-semibold mb-2")

            enabled = is_notifications_enabled()
            channels = get_enabled_channels()

            with ui.row().classes("items-center gap-4"):
                if enabled:
                    ui.badge("Enabled").props("color=green")
                    if channels:
                        for ch in channels:
                            ui.badge(ch.title()).props("color=blue outline")
                    else:
                        ui.label("No channels configured").classes("text-orange text-sm")
                else:
                    ui.badge("Disabled").props("color=gray")
                    ui.label(
                        "Set NOTIFICATIONS_ENABLED=true in .env to activate"
                    ).classes("text-sm text-gray-500")

        # Configuration reference
        with ui.card().classes("w-full mt-4"):
            ui.label("Configuration").classes("text-lg font-semibold mb-2")
            ui.label(
                "Notifications are configured via environment variables in your .env file."
            ).classes("text-sm text-gray-500 mb-3")

            with ui.expansion("Environment Variables Reference", icon="settings").classes("w-full"):
                ui.code("""# Enable notifications globally
NOTIFICATIONS_ENABLED=true

# Email (SMTP)
NOTIFY_EMAIL_ENABLED=true
NOTIFY_SMTP_HOST=smtp.gmail.com
NOTIFY_SMTP_PORT=587
NOTIFY_SMTP_USER=you@gmail.com
NOTIFY_SMTP_PASS=your_app_password
NOTIFY_SMTP_FROM=homelab@yourdomain.com
NOTIFY_SMTP_TO=admin@yourdomain.com
NOTIFY_SMTP_TLS=true

# Webhook (generic JSON POST)
NOTIFY_WEBHOOK_ENABLED=true
NOTIFY_WEBHOOK_URL=https://hooks.slack.com/services/xxx

# Pushover
NOTIFY_PUSHOVER_ENABLED=true
NOTIFY_PUSHOVER_TOKEN=your_app_token
NOTIFY_PUSHOVER_USER=your_user_key""", language="bash").classes("w-full")

        # Test notification
        with ui.card().classes("w-full mt-4"):
            ui.label("Test Notification").classes("text-lg font-semibold mb-2")
            ui.label("Send a test message through all enabled channels.").classes(
                "text-sm text-gray-500 mb-3"
            )

            test_result = ui.label("").classes("text-sm mt-2")

            def send_test():
                if not is_notifications_enabled():
                    ui.notify("Notifications are disabled", type="warning")
                    return
                results = send_notification(
                    subject="Test Notification",
                    message="This is a test notification from Home Lab Manager.",
                    priority="normal",
                )
                if not results:
                    test_result.text = "No channels enabled"
                    ui.notify("No notification channels enabled", type="warning")
                else:
                    successes = [r for r in results if r["success"]]
                    failures = [r for r in results if not r["success"]]
                    if successes:
                        ui.notify(
                            f"Sent via: {', '.join(r['channel'] for r in successes)}",
                            type="positive",
                        )
                    if failures:
                        for f in failures:
                            ui.notify(
                                f"{f['channel']} failed: {f['error']}",
                                type="negative",
                            )
                    test_result.text = f"{len(successes)} sent, {len(failures)} failed"

            ui.button("Send Test", icon="send", on_click=send_test).props("color=primary")

        # Notification triggers
        with ui.card().classes("w-full mt-4"):
            ui.label("Alert Triggers").classes("text-lg font-semibold mb-2")
            ui.label("The following events trigger notifications automatically:").classes(
                "text-sm text-gray-500 mb-3"
            )

            triggers = [
                ("🔴 Host Down", "When an uptime-monitored host stops responding", "High"),
                ("🟢 Host Recovered", "When a previously-down host comes back online", "Normal"),
                ("📦 Firmware Update", "When a new firmware version is detected for a UniFi device", "Low"),
            ]

            columns = [
                {"name": "event", "label": "Event", "field": "event", "align": "left"},
                {"name": "description", "label": "Description", "field": "description", "align": "left"},
                {"name": "priority", "label": "Priority", "field": "priority", "align": "center"},
            ]
            rows = [
                {"event": t[0], "description": t[1], "priority": t[2]}
                for t in triggers
            ]
            ui.table(columns=columns, rows=rows, row_key="event").classes("w-full").props(
                "flat bordered dense"
            )

        # History
        ui.separator().classes("my-4")
        ui.label("Notification History").classes("text-xl font-semibold mb-2")

        history = get_notification_history(limit=30)

        if history:
            columns = [
                {"name": "time", "label": "Time", "field": "time", "align": "left"},
                {"name": "channel", "label": "Channel", "field": "channel", "align": "center"},
                {"name": "subject", "label": "Subject", "field": "subject", "align": "left"},
                {"name": "status", "label": "Status", "field": "status", "align": "center"},
            ]
            rows = [
                {
                    "id": log.id,
                    "time": log.timestamp.strftime("%Y-%m-%d %H:%M:%S") if log.timestamp else "—",
                    "channel": log.channel,
                    "subject": log.subject[:60],
                    "status": "✅" if log.success else f"❌ {log.error or ''}",
                }
                for log in history
            ]
            ui.table(columns=columns, rows=rows, row_key="id").classes("w-full").props(
                "flat bordered dense"
            )
        else:
            ui.label("No notifications sent yet.").classes("text-gray-500 italic")
