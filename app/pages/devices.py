"""Devices management page."""

from nicegui import ui

from app.database.db import get_session_direct as get_session
from app.services.device_service import (
    create_device,
    get_all_devices,
    get_all_device_types,
    create_device_type,
    delete_device,
)
from app.utils.validators import is_valid_mac
from app.utils.formatters import format_mac
from app.pages.layout import page_layout


def render_devices():
    """Render the devices management page."""
    page_layout()

    session = get_session()

    with ui.column().classes("page-container w-full"):
        with ui.row().classes("w-full items-center justify-between"):
            ui.label("Devices").classes("text-3xl font-bold")
            ui.button("Add Device", on_click=lambda: add_dialog.open()).props(
                "color=primary icon=add"
            )

        ui.separator().classes("my-4")

        # Devices table
        devices_container = ui.column().classes("w-full")

        def refresh_devices():
            devices_container.clear()
            devices = get_all_devices(session)
            with devices_container:
                if not devices:
                    ui.label("No devices tracked yet.").classes("text-gray-500")
                    return

                columns = [
                    {"name": "name", "label": "Name", "field": "name", "align": "left"},
                    {"name": "type", "label": "Type", "field": "type", "align": "left"},
                    {"name": "manufacturer", "label": "Manufacturer", "field": "manufacturer", "align": "left"},
                    {"name": "model", "label": "Model", "field": "model", "align": "left"},
                    {"name": "mac", "label": "MAC Address", "field": "mac", "align": "left"},
                    {"name": "ips", "label": "IPs", "field": "ips", "align": "center"},
                ]

                rows = []
                for d in devices:
                    rows.append({
                        "id": d.id,
                        "name": d.name,
                        "type": d.device_type.name if d.device_type else "—",
                        "manufacturer": d.manufacturer or "—",
                        "model": d.model or "—",
                        "mac": format_mac(d.mac_address) or "—",
                        "ips": len(d.ip_addresses),
                    })

                table = ui.table(
                    columns=columns, rows=rows, row_key="id"
                ).classes("w-full")
                table.props("flat bordered dense")

        refresh_devices()

    # Add device dialog
    with ui.dialog() as add_dialog, ui.card().classes("w-96"):
        ui.label("Add Device").classes("text-xl font-bold mb-2")

        device_types = get_all_device_types(session)
        type_options = {dt.id: dt.name for dt in device_types}

        name_input = ui.input("Name *", placeholder="e.g. Office Printer").classes("w-full")
        type_select = ui.select(
            type_options, label="Device Type"
        ).classes("w-full")
        manufacturer_input = ui.input("Manufacturer", placeholder="e.g. HP").classes("w-full")
        model_input = ui.input("Model", placeholder="e.g. LaserJet Pro").classes("w-full")
        serial_input = ui.input("Serial Number").classes("w-full")
        mac_input = ui.input("MAC Address", placeholder="AA:BB:CC:DD:EE:FF").classes("w-full")
        notes_input = ui.textarea("Notes").classes("w-full")

        def save_device():
            if not name_input.value:
                ui.notify("Name is required", type="warning")
                return
            if mac_input.value and not is_valid_mac(mac_input.value):
                ui.notify("Invalid MAC address format", type="negative")
                return

            try:
                create_device(
                    session,
                    name=name_input.value,
                    device_type_id=type_select.value,
                    manufacturer=manufacturer_input.value or None,
                    model=model_input.value or None,
                    serial_number=serial_input.value or None,
                    mac_address=mac_input.value or None,
                    notes=notes_input.value or None,
                )
                ui.notify("Device added!", type="positive")
                add_dialog.close()
                refresh_devices()
            except Exception as e:
                ui.notify(f"Error: {e}", type="negative")

        with ui.row().classes("justify-end gap-2 mt-2"):
            ui.button("Cancel", on_click=add_dialog.close).props("flat")
            ui.button("Save", on_click=save_device).props("color=primary")

    session.close()
