"""Device detail page."""

from nicegui import ui

from app.database.db import get_session_direct as get_session
from app.services.device_service import get_device_by_id, update_device
from app.utils.formatters import format_timestamp, format_mac
from app.pages.layout import page_layout
from app.pages.tag_assignment import render_tag_assignment


def render_device_detail(device_id: int):
    """Render a single device's detail page."""
    page_layout()

    session = get_session()
    device = get_device_by_id(session, device_id)

    if not device:
        with ui.column().classes("page-container"):
            ui.label("Device not found").classes("text-xl text-red")
        session.close()
        return

    with ui.column().classes("page-container w-full"):
        # Header
        with ui.row().classes("items-center gap-4"):
            ui.button(icon="arrow_back", on_click=lambda: ui.navigate.to("/devices")).props(
                "flat round"
            )
            icon_name = device.device_type.icon if device.device_type and device.device_type.icon else "devices_other"
            ui.icon(icon_name).classes("text-3xl")
            ui.label(device.name).classes("text-3xl font-bold")
            if device.device_type:
                ui.badge(device.device_type.name).props("color=blue outline")

        ui.separator().classes("my-4")

        with ui.row().classes("w-full gap-4 flex-wrap"):
            # Info panel
            with ui.card().classes("w-80"):
                ui.label("Details").classes("text-lg font-semibold mb-2")
                ui.label(f"Manufacturer: {device.manufacturer or '—'}")
                ui.label(f"Model: {device.model or '—'}")
                ui.label(f"Serial: {device.serial_number or '—'}")
                ui.label(f"MAC: {format_mac(device.mac_address) or '—'}")
                ui.label(f"Created: {format_timestamp(device.created_at)}")

                # Associated IPs
                if device.ip_addresses:
                    ui.label("IP Addresses:").classes("font-semibold mt-2")
                    for ip in device.ip_addresses:
                        ui.link(
                            f"{ip.address} ({ip.hostname or '—'})",
                            f"/ips/{ip.id}"
                        ).classes("font-mono text-sm")

            # Notes editor
            with ui.card().classes("flex-1 min-w-[400px]"):
                ui.label("Notes (Markdown)").classes("text-lg font-semibold mb-2")

                with ui.tabs().classes("w-full") as tabs:
                    edit_tab = ui.tab("Edit")
                    preview_tab = ui.tab("Preview")

                with ui.tab_panels(tabs, value=edit_tab).classes("w-full"):
                    with ui.tab_panel(edit_tab):
                        notes_editor = ui.textarea(
                            value=device.notes or ""
                        ).classes("w-full").props('rows="12"')

                        def save_notes():
                            update_device(session, device.id, notes=notes_editor.value)
                            ui.notify("Notes saved!", type="positive")

                        ui.button("Save Notes", on_click=save_notes).props(
                            "color=primary"
                        )

                    with ui.tab_panel(preview_tab):
                        ui.markdown(device.notes or "*No notes yet*").classes("w-full")

        # Tags
        render_tag_assignment(session, device)

    session.close()
