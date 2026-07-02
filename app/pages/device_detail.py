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

        # Storage
        if health.get("storage"):
            ui.separator().classes("my-3")
            ui.label("Storage").classes("text-md font-semibold mb-2")
            with ui.row().classes("w-full gap-4 flex-wrap"):
                for vol in health["storage"]:
                    size_gb = vol.get("size", 0) / 1024 / 1024 / 1024
                    used_gb = vol.get("used", 0) / 1024 / 1024 / 1024
                    pct = (used_gb / size_gb * 100) if size_gb > 0 else 0
                    disk_color = "green" if pct < 70 else "orange" if pct < 90 else "red"

                    with ui.column().classes("min-w-[150px]"):
                        with ui.row().classes("items-center gap-1"):
                            ui.icon("hard_drive" if "emmc" not in vol.get("type", "").lower() else "sd_card").classes("text-gray-500")
                            ui.label(vol.get("name", vol.get("mount_point", "—"))).classes("font-semibold text-sm")
                        ui.linear_progress(value=pct / 100, show_value=False).classes("w-full").props(
                            f'color="{disk_color}"'
                        )
                        ui.label(
                            f"{used_gb:.1f} / {size_gb:.1f} GB ({pct:.0f}%)"
                        ).classes("text-xs text-gray-500")
                        ui.label(
                            f"Mount: {vol.get('mount_point', '—')} · Type: {vol.get('type', '—')}"
                        ).classes("text-xs text-gray-400")
