"""Webhook Triggers page — create and manage event-driven webhooks."""

from nicegui import ui

from app.database.db import get_session_direct as get_session
from app.services.webhook_trigger_service import (
    get_all_triggers,
    create_trigger,
    update_trigger,
    delete_trigger,
    test_trigger,
    EVENT_TYPES,
)
from app.pages.layout import page_layout


def render_webhook_triggers():
    """Render the webhook triggers management page."""
    page_layout()

    session = get_session()

    with ui.column().classes("page-container w-full"):
        with ui.row().classes("w-full items-center justify-between"):
            ui.label("Webhook Triggers").classes("text-3xl font-bold")
            ui.button("Add Trigger", icon="add", on_click=lambda: add_dialog.open()).props(
                "color=primary"
            )

        ui.label(
            "Fire webhooks automatically when system events occur. "
            "Integrates with Slack, Discord, Home Assistant, n8n, or any HTTP endpoint."
        ).classes("text-gray-500 mb-4")

        ui.separator()

        # Triggers list
        triggers_container = ui.column().classes("w-full mt-4 gap-3")

        def refresh_triggers():
            triggers_container.clear()
            triggers = get_all_triggers(session)
            with triggers_container:
                if not triggers:
                    ui.label("No webhook triggers configured. Click 'Add Trigger' to create one.").classes(
                        "text-gray-500 italic"
                    )
                    return

                for trigger in triggers:
                    with ui.card().classes("w-full"):
                        with ui.row().classes("w-full items-center justify-between"):
                            with ui.row().classes("items-center gap-3"):
                                status_color = "green" if trigger.is_enabled else "gray"
                                ui.icon("webhook").classes(f"text-xl text-{status_color}")
                                with ui.column().classes("gap-0"):
                                    ui.label(trigger.name).classes("font-semibold text-lg")
                                    with ui.row().classes("items-center gap-2"):
                                        ui.badge(
                                            EVENT_TYPES.get(trigger.event_type, trigger.event_type)
                                        ).props("color=blue outline").classes("text-xs")
                                        if trigger.filter_value:
                                            ui.badge(f"filter: {trigger.filter_value}").props(
                                                "color=gray outline"
                                            ).classes("text-xs")
                                        if not trigger.is_enabled:
                                            ui.badge("DISABLED").props("color=gray")

                            with ui.row().classes("items-center gap-3"):
                                with ui.column().classes("items-end gap-0"):
                                    ui.label(f"Fired: {trigger.fire_count}x").classes("text-xs text-gray-400")
                                    if trigger.last_fired:
                                        ui.label(
                                            f"Last: {trigger.last_fired.strftime('%Y-%m-%d %H:%M')}"
                                        ).classes("text-xs text-gray-400")

                                ui.button(
                                    icon="send",
                                    on_click=lambda t=trigger: do_test(t.id),
                                ).props("flat round size=sm color=blue").tooltip("Send test webhook")
                                ui.button(
                                    icon="edit",
                                    on_click=lambda t=trigger: open_edit(t),
                                ).props("flat round size=sm").tooltip("Edit")
                                ui.button(
                                    icon="delete",
                                    on_click=lambda t=trigger: confirm_delete(t),
                                ).props("flat round size=sm color=red").tooltip("Delete")

                        # Show URL (truncated)
                        url_display = trigger.webhook_url[:60] + "..." if len(trigger.webhook_url) > 60 else trigger.webhook_url
                        ui.label(f"→ {url_display}").classes("text-xs text-gray-400 font-mono mt-1")

        def do_test(trigger_id):
            result = test_trigger(session, trigger_id)
            if result["success"]:
                ui.notify("Test webhook sent successfully!", type="positive")
            else:
                ui.notify(f"Test failed: {result['error']}", type="negative")

        def open_edit(trigger):
            edit_name.value = trigger.name
            edit_event.value = trigger.event_type
            edit_url.value = trigger.webhook_url
            edit_filter.value = trigger.filter_value or ""
            edit_enabled.value = trigger.is_enabled
            edit_dialog.trigger_id = trigger.id
            edit_dialog.open()

        def confirm_delete(trigger):
            with ui.dialog() as dlg, ui.card():
                ui.label(f"Delete trigger '{trigger.name}'?").classes("text-lg")
                with ui.row().classes("justify-end gap-2 mt-2"):
                    ui.button("Cancel", on_click=dlg.close).props("flat")
                    ui.button("Delete", on_click=lambda: (
                        delete_trigger(session, trigger.id),
                        dlg.close(),
                        refresh_triggers(),
                        ui.notify("Trigger deleted", type="warning"),
                    )).props("color=red")
            dlg.open()

        refresh_triggers()

        # Event types reference
        ui.separator().classes("my-4")
        with ui.expansion("Available Events", icon="info").classes("w-full"):
            columns = [
                {"name": "event", "label": "Event", "field": "event", "align": "left"},
                {"name": "description", "label": "Description", "field": "description", "align": "left"},
            ]
            rows = [{"event": k, "description": v} for k, v in EVENT_TYPES.items()]
            ui.table(columns=columns, rows=rows, row_key="event").classes("w-full").props(
                "flat bordered dense"
            )

    # Add trigger dialog
    with ui.dialog() as add_dialog, ui.card().classes("w-[500px]"):
        ui.label("New Webhook Trigger").classes("text-xl font-bold mb-2")
        add_name = ui.input("Name *", placeholder="e.g. Slack alert on down").classes("w-full")
        add_event = ui.select(
            EVENT_TYPES, label="Event *"
        ).classes("w-full")
        add_url = ui.input(
            "Webhook URL *", placeholder="https://hooks.slack.com/services/..."
        ).classes("w-full")
        add_filter = ui.input(
            "Filter (optional)",
            placeholder="e.g. network name, IP prefix, device name",
        ).classes("w-full")
        ui.label(
            "Filter narrows which events fire this trigger. "
            "Leave empty to fire on all matching events."
        ).classes("text-xs text-gray-400")

        def save_new():
            if not add_name.value or not add_event.value or not add_url.value:
                ui.notify("Name, Event, and URL are required", type="warning")
                return
            create_trigger(
                session,
                name=add_name.value.strip(),
                event_type=add_event.value,
                webhook_url=add_url.value.strip(),
                filter_value=add_filter.value.strip() or None,
            )
            ui.notify("Trigger created!", type="positive")
            add_dialog.close()
            refresh_triggers()

        with ui.row().classes("justify-end gap-2 mt-2"):
            ui.button("Cancel", on_click=add_dialog.close).props("flat")
            ui.button("Save", on_click=save_new).props("color=primary")

    # Edit trigger dialog
    with ui.dialog() as edit_dialog, ui.card().classes("w-[500px]"):
        edit_dialog.trigger_id = None
        ui.label("Edit Trigger").classes("text-xl font-bold mb-2")
        edit_name = ui.input("Name *").classes("w-full")
        edit_event = ui.select(EVENT_TYPES, label="Event *").classes("w-full")
        edit_url = ui.input("Webhook URL *").classes("w-full")
        edit_filter = ui.input("Filter (optional)").classes("w-full")
        edit_enabled = ui.switch("Enabled", value=True)

        def save_edit():
            if not edit_name.value or not edit_event.value or not edit_url.value:
                ui.notify("Name, Event, and URL are required", type="warning")
                return
            update_trigger(
                session,
                edit_dialog.trigger_id,
                name=edit_name.value.strip(),
                event_type=edit_event.value,
                webhook_url=edit_url.value.strip(),
                filter_value=edit_filter.value.strip() or None,
                is_enabled=edit_enabled.value,
            )
            ui.notify("Trigger updated!", type="positive")
            edit_dialog.close()
            refresh_triggers()

        with ui.row().classes("justify-end gap-2 mt-2"):
            ui.button("Cancel", on_click=edit_dialog.close).props("flat")
            ui.button("Save", on_click=save_edit).props("color=primary")

    session.close()
