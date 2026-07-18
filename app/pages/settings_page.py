"""Settings page — edit .env configuration from the UI."""

import os
from pathlib import Path

from nicegui import ui

from app.pages.layout import page_layout

ENV_FILE = Path(__file__).parent.parent.parent / ".env"

# Define settings groups with their keys, labels, types, and descriptions
SETTINGS_SCHEMA = [
    {
        "group": "Application",
        "icon": "settings",
        "fields": [
            {"key": "APP_TITLE", "label": "App Title", "type": "text", "desc": "Application name shown in the browser tab"},
            {"key": "APP_PORT", "label": "Port", "type": "number", "desc": "HTTP port the app listens on"},
            {"key": "DATABASE_URL", "label": "Database URL", "type": "text", "desc": "SQLAlchemy database connection string"},
        ],
    },
    {
        "group": "UniFi Integration",
        "icon": "router",
        "fields": [
            {"key": "UNIFI_API_KEY", "label": "API Key", "type": "password", "desc": "Local console Integration API key"},
            {"key": "UNIFI_BASE_URL", "label": "Base URL", "type": "text", "desc": "Console URL (e.g. https://192.168.2.254)"},
            {"key": "UNIFI_SITE_ID", "label": "Site ID", "type": "text", "desc": "UUID of the UniFi site"},
            {"key": "UNIFI_CLOUD_API_KEY", "label": "Cloud API Key", "type": "password", "desc": "Site Manager API key (for cloud features)"},
        ],
    },
    {
        "group": "Notifications — General",
        "icon": "notifications",
        "fields": [
            {"key": "NOTIFICATIONS_ENABLED", "label": "Enable Notifications", "type": "toggle", "desc": "Master switch for all notification channels"},
        ],
    },
    {
        "group": "Notifications — Email (SMTP)",
        "icon": "email",
        "fields": [
            {"key": "NOTIFY_EMAIL_ENABLED", "label": "Enable Email", "type": "toggle", "desc": "Send alerts via email"},
            {"key": "NOTIFY_SMTP_HOST", "label": "SMTP Host", "type": "text", "desc": "e.g. smtp.gmail.com"},
            {"key": "NOTIFY_SMTP_PORT", "label": "SMTP Port", "type": "number", "desc": "Usually 587 (TLS) or 465 (SSL)"},
            {"key": "NOTIFY_SMTP_USER", "label": "SMTP Username", "type": "text", "desc": "Login username"},
            {"key": "NOTIFY_SMTP_PASS", "label": "SMTP Password", "type": "password", "desc": "Login password or app password"},
            {"key": "NOTIFY_SMTP_FROM", "label": "From Address", "type": "text", "desc": "Sender email address"},
            {"key": "NOTIFY_SMTP_TO", "label": "To Address(es)", "type": "text", "desc": "Recipient(s), comma-separated"},
            {"key": "NOTIFY_SMTP_TLS", "label": "Use TLS", "type": "toggle", "desc": "Enable STARTTLS encryption"},
        ],
    },
    {
        "group": "Notifications — Webhook",
        "icon": "webhook",
        "fields": [
            {"key": "NOTIFY_WEBHOOK_ENABLED", "label": "Enable Webhook", "type": "toggle", "desc": "Send alerts via HTTP POST"},
            {"key": "NOTIFY_WEBHOOK_URL", "label": "Webhook URL", "type": "text", "desc": "Endpoint URL (Slack, Discord, custom)"},
        ],
    },
    {
        "group": "Notifications — Pushover",
        "icon": "phone_android",
        "fields": [
            {"key": "NOTIFY_PUSHOVER_ENABLED", "label": "Enable Pushover", "type": "toggle", "desc": "Send push notifications via Pushover"},
            {"key": "NOTIFY_PUSHOVER_TOKEN", "label": "App Token", "type": "password", "desc": "Pushover application API token"},
            {"key": "NOTIFY_PUSHOVER_USER", "label": "User Key", "type": "password", "desc": "Pushover user/group key"},
        ],
    },
    {
        "group": "Notifications — Telegram",
        "icon": "telegram",
        "fields": [
            {"key": "NOTIFY_TELEGRAM_ENABLED", "label": "Enable Telegram", "type": "toggle", "desc": "Send notifications via Telegram Bot"},
            {"key": "NOTIFY_TELEGRAM_BOT_TOKEN", "label": "Bot Token", "type": "password", "desc": "Token from @BotFather (e.g. 123456:ABC-xyz)"},
            {"key": "NOTIFY_TELEGRAM_CHAT_ID", "label": "Chat ID", "type": "text", "desc": "Your chat or group ID"},
        ],
    },
]


def _read_env() -> dict[str, str]:
    """Read the .env file and return key-value pairs."""
    values = {}
    if not ENV_FILE.exists():
        return values
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            values[key.strip()] = value.strip()
    return values


def _write_env(values: dict[str, str]):
    """Write key-value pairs back to .env, preserving comments and order."""
    if not ENV_FILE.exists():
        # Create fresh file
        lines = []
        for key, val in values.items():
            lines.append(f"{key}={val}")
        ENV_FILE.write_text("\n".join(lines) + "\n")
        return

    # Preserve existing structure — update values in-place, append new ones
    existing_lines = ENV_FILE.read_text().splitlines()
    written_keys = set()
    new_lines = []

    for line in existing_lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key = stripped.split("=", 1)[0].strip()
            if key in values:
                new_lines.append(f"{key}={values[key]}")
                written_keys.add(key)
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    # Append any new keys not already in the file
    for key, val in values.items():
        if key not in written_keys:
            new_lines.append(f"{key}={val}")

    ENV_FILE.write_text("\n".join(new_lines) + "\n")


def render_settings():
    """Render the settings page."""
    page_layout()

    env_values = _read_env()

    with ui.column().classes("page-container w-full"):
        ui.label("Settings").classes("text-3xl font-bold")
        ui.label("Configure application settings. Changes are saved to the .env file.").classes(
            "text-gray-500 mb-2"
        )
        with ui.row().classes("items-center gap-2 mb-4"):
            ui.icon("info").classes("text-blue")
            ui.label(
                "Notification settings take effect immediately. "
                "App, database, and UniFi settings require a restart."
            ).classes("text-sm text-blue")

        ui.separator()

        # Build form inputs
        field_inputs: dict[str, any] = {}

        for group in SETTINGS_SCHEMA:
            with ui.card().classes("w-full mt-4"):
                with ui.row().classes("items-center gap-2 mb-3"):
                    ui.icon(group["icon"]).classes("text-xl text-primary")
                    ui.label(group["group"]).classes("text-lg font-semibold")

                for field in group["fields"]:
                    key = field["key"]
                    current_value = env_values.get(key, "")
                    field_type = field["type"]

                    with ui.row().classes("w-full items-center gap-4"):
                        with ui.column().classes("flex-1 gap-0"):
                            if field_type == "toggle":
                                is_true = current_value.lower() == "true"
                                inp = ui.switch(field["label"], value=is_true)
                            elif field_type == "password":
                                inp = ui.input(
                                    field["label"],
                                    value=current_value,
                                    password=True,
                                    password_toggle_button=True,
                                ).classes("w-full")
                            elif field_type == "number":
                                inp = ui.input(
                                    field["label"],
                                    value=current_value,
                                ).classes("w-full")
                            else:
                                inp = ui.input(
                                    field["label"],
                                    value=current_value,
                                ).classes("w-full")

                            ui.label(field["desc"]).classes("text-xs text-gray-400 -mt-1")

                        field_inputs[key] = (inp, field_type)

        # Save button
        ui.separator().classes("my-4")

        with ui.row().classes("w-full justify-end gap-4"):
            def save_settings():
                new_values = {}
                for key, (inp, ftype) in field_inputs.items():
                    if ftype == "toggle":
                        new_values[key] = "true" if inp.value else "false"
                    else:
                        new_values[key] = str(inp.value) if inp.value else ""

                try:
                    _write_env(new_values)
                    # Reload .env into os.environ so changes take effect immediately
                    # for services that read from os.getenv (notifications read from file directly)
                    from dotenv import load_dotenv
                    load_dotenv(ENV_FILE, override=True)
                    ui.notify(
                        "Settings saved! Notification settings take effect immediately. "
                        "App/UniFi/database changes require a restart.",
                        type="positive",
                    )
                except Exception as e:
                    ui.notify(f"Error saving settings: {e}", type="negative")

            def reset_form():
                fresh_values = _read_env()
                for key, (inp, ftype) in field_inputs.items():
                    val = fresh_values.get(key, "")
                    if ftype == "toggle":
                        inp.value = val.lower() == "true"
                    else:
                        inp.value = val
                ui.notify("Form reset to saved values", type="info")

            ui.button("Reset", icon="undo", on_click=reset_form).props("flat")
            ui.button("Save Settings", icon="save", on_click=save_settings).props("color=primary")

        # Change password section (if auth is enabled)
        from app.services.auth_service import is_auth_enabled
        if is_auth_enabled():
            ui.separator().classes("my-4")
            from app.pages.login_page import render_change_password
            render_change_password()
