"""Device detail page."""

from nicegui import ui

from app.database.db import get_session_direct as get_session
from app.services.device_service import get_device_by_id, update_device
from app.utils.formatters import format_timestamp, format_mac
from app.pages.layout import page_layout
from app.pages.tag_assignment import render_tag_assignment
from app.pages.custom_fields import render_custom_fields_for_entity


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

        # Health stats for Ubiquiti devices
        if device.manufacturer and "ubiquiti" in device.manufacturer.lower():
            _render_unifi_health(device)

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

            # Notes
            with ui.column().classes("flex-1 min-w-[400px]"):
                from app.pages.notes_component import render_notes
                render_notes(session, "device", device.id)

        # Tags
        render_tag_assignment(session, device)

        # Physical Location
        with ui.card().classes("w-full mt-4"):
            ui.label("Physical Location").classes("text-lg font-semibold mb-2")
            with ui.row().classes("gap-4 items-end"):
                loc_input = ui.input(
                    "Location (Room/Building)", value=device.location or ""
                ).classes("w-64")
                rack_input = ui.input(
                    "Rack Position", value=device.rack_position or ""
                ).classes("w-48")
                shelf_input = ui.input(
                    "Shelf", value=device.shelf or ""
                ).classes("w-48")

            def save_location():
                update_device(
                    session,
                    device.id,
                    location=loc_input.value or None,
                    rack_position=rack_input.value or None,
                    shelf=shelf_input.value or None,
                )
                ui.notify("Location saved!", type="positive")

            ui.button("Save Location", on_click=save_location).props(
                "color=primary size=sm"
            ).classes("mt-2")

        # Custom Fields
        render_custom_fields_for_entity(session, "device", device.id)

    session.close()


def _render_unifi_health(device):
    """Render UniFi device health stats (CPU, RAM, temp, uptime)."""
    from app.services.unifi_device_stats import get_device_health

    if not device.mac_address:
        return

    health = get_device_health(device.mac_address)
    if not health:
        return

    with ui.card().classes("w-full mb-4"):
        ui.label("Device Health").classes("text-lg font-semibold mb-3")

        with ui.row().classes("w-full gap-6 flex-wrap"):
            # Uptime
            with ui.column().classes("items-center gap-0"):
                ui.icon("schedule").classes("text-2xl text-green")
                ui.label(health["uptime_str"]).classes("text-lg font-bold")
                ui.label("Uptime").classes("text-xs text-gray-500")

            # CPU
            with ui.column().classes("items-center gap-0 min-w-[100px]"):
                cpu = health["cpu_percent"]
                cpu_color = "green" if cpu < 50 else "orange" if cpu < 80 else "red"
                ui.icon("memory").classes(f"text-2xl text-{cpu_color}")
                ui.label(f"{cpu:.1f}%").classes("text-lg font-bold")
                ui.label("CPU").classes("text-xs text-gray-500")
                ui.linear_progress(value=cpu / 100, show_value=False).classes("w-24").props(
                    f'color="{cpu_color}"'
                )

            # Memory
            with ui.column().classes("items-center gap-0 min-w-[100px]"):
                mem = health["mem_percent"]
                mem_color = "green" if mem < 60 else "orange" if mem < 85 else "red"
                ui.icon("storage").classes(f"text-2xl text-{mem_color}")
                ui.label(f"{mem:.1f}%").classes("text-lg font-bold")
                ui.label(f"RAM ({health['mem_used_mb']}/{health['mem_total_mb']} MB)").classes("text-xs text-gray-500")
                ui.linear_progress(value=mem / 100, show_value=False).classes("w-24").props(
                    f'color="{mem_color}"'
                )

            # Load Average
            with ui.column().classes("items-center gap-0"):
                ui.icon("speed").classes("text-2xl text-blue")
                ui.label(f"{health['load_1']:.2f}").classes("text-lg font-bold")
                ui.label(f"Load (1/5/15: {health['load_1']:.1f}/{health['load_5']:.1f}/{health['load_15']:.1f})").classes("text-xs text-gray-500")

            # Temperatures
            if health["temperatures"]:
                for temp in health["temperatures"]:
                    temp_val = temp.get("value", 0)
                    temp_color = "green" if temp_val < 60 else "orange" if temp_val < 80 else "red"
                    with ui.column().classes("items-center gap-0"):
                        ui.icon("thermostat").classes(f"text-2xl text-{temp_color}")
                        ui.label(f"{temp_val:.1f}°C").classes("text-lg font-bold")
                        ui.label(temp.get("name", "Temp")).classes("text-xs text-gray-500")

        # PoE Power
        if health.get("poe_max_power") and health["poe_max_power"] > 0:
            ui.separator().classes("my-3")
            ui.label("PoE Power").classes("text-md font-semibold mb-2")

            used = health["poe_used_power"]
            max_pwr = health["poe_max_power"]
            pct = (used / max_pwr * 100) if max_pwr > 0 else 0
            poe_color = "green" if pct < 60 else "orange" if pct < 85 else "red"

            with ui.row().classes("items-center gap-4 mb-2"):
                ui.icon("bolt").classes(f"text-2xl text-{poe_color}")
                ui.label(f"{used:.1f}W / {max_pwr:.0f}W ({pct:.0f}%)").classes("font-semibold")
                ui.linear_progress(value=pct / 100, show_value=False).classes("w-48").props(
                    f'color="{poe_color}"'
                )

            # Per-port table
            active_ports = [p for p in health.get("poe_ports", []) if p["active"]]
            if active_ports:
                # Look up device types from DB
                from app.models.device import Device as DeviceModel
                from app.database.db import get_session_direct
                db = get_session_direct()

                columns = [
                    {"name": "port", "label": "Port", "field": "port", "align": "center"},
                    {"name": "device", "label": "Connected Device", "field": "device", "align": "left"},
                    {"name": "type", "label": "Type", "field": "type", "align": "center"},
                    {"name": "power", "label": "Power (W)", "field": "power", "align": "right"},
                    {"name": "voltage", "label": "Voltage (V)", "field": "voltage", "align": "right"},
                    {"name": "current", "label": "Current (mA)", "field": "current", "align": "right"},
                    {"name": "class", "label": "Class", "field": "class", "align": "center"},
                ]
                rows = []
                for p in active_ports:
                    # Try to find device type from DB
                    dev_type = "—"
                    dev_name = p.get("connected_device") or p.get("name", "—")
                    if dev_name and dev_name != "—":
                        db_device = db.query(DeviceModel).filter(DeviceModel.name == dev_name).first()
                        if db_device and db_device.device_type:
                            dev_type = db_device.device_type.name

                    rows.append({
                        "port": p["port"],
                        "device": dev_name,
                        "type": dev_type,
                        "power": f"{p['power_w']:.2f}",
                        "voltage": f"{p['voltage']:.1f}",
                        "current": f"{p['current_ma']:.0f}",
                        "class": p["class"],
                    })

                db.close()
                ui.table(columns=columns, rows=rows, row_key="port").classes(
                    "w-full"
                ).props("flat bordered dense")
