"""Firmware tracking page — view and check UniFi device firmware versions."""

from nicegui import ui

from app.services.firmware_service import (
    sync_firmware_info,
    get_all_firmware,
    get_devices_with_updates,
)
from app.services.unifi_service import is_configured
from app.database.db import get_session_direct as get_session
from app.pages.layout import page_layout


def render_firmware():
    """Render the firmware tracking page."""
    page_layout()

    with ui.column().classes("page-container w-full"):
        with ui.row().classes("w-full items-center justify-between"):
            ui.label("Firmware Tracker").classes("text-3xl font-bold")
            ui.button(
                "Check for Updates", icon="refresh",
                on_click=lambda: run_firmware_check(),
            ).props("color=primary")

        ui.label(
            "Track firmware versions across your UniFi devices and get notified of updates."
        ).classes("text-gray-500 mb-4")

        ui.separator()

        if not is_configured():
            with ui.card().classes("w-full mt-4"):
                ui.label(
                    "⚠️ UniFi integration not configured. "
                    "Set UNIFI_API_KEY, UNIFI_BASE_URL, and UNIFI_SITE_ID in .env."
                ).classes("text-orange")
            return

        # Results container
        check_result = ui.label("").classes("text-sm text-gray-500 mt-2")
        firmware_container = ui.column().classes("w-full mt-4 gap-4")

        def run_firmware_check():
            check_result.text = "Checking..."
            ui.notify("Checking firmware versions...", type="info")
            result = sync_firmware_info()
            if result["errors"]:
                for err in result["errors"][:3]:
                    ui.notify(f"Error: {err}", type="negative")
            check_result.text = (
                f"Checked {result['checked']} devices — "
                f"{result['updates_available']} updates available"
            )
            if result["updates_available"]:
                ui.notify(
                    f"{result['updates_available']} firmware update(s) available!",
                    type="warning",
                )
            else:
                ui.notify("All devices up to date", type="positive")
            refresh_firmware_list()

        def refresh_firmware_list():
            firmware_container.clear()
            all_fw = get_all_firmware()

            with firmware_container:
                if not all_fw:
                    ui.label(
                        "No firmware data yet. Click 'Check for Updates' to scan your devices."
                    ).classes("text-gray-500 italic")
                    return

                # Summary
                total = len(all_fw)
                with_updates = [f for f in all_fw if f.update_available]
                up_to_date = [f for f in all_fw if not f.update_available and f.current_version]

                with ui.row().classes("gap-4 mb-4"):
                    with ui.card().classes("p-3"):
                        ui.label(str(total)).classes("text-2xl font-bold text-primary")
                        ui.label("Tracked").classes("text-xs text-gray-500")
                    with ui.card().classes("p-3"):
                        ui.label(str(len(up_to_date))).classes("text-2xl font-bold text-green")
                        ui.label("Up to Date").classes("text-xs text-gray-500")
                    with ui.card().classes("p-3"):
                        ui.label(str(len(with_updates))).classes("text-2xl font-bold text-orange")
                        ui.label("Updates Available").classes("text-xs text-gray-500")

                # Updates available section
                if with_updates:
                    ui.label("Updates Available").classes("text-xl font-semibold mt-2")
                    for fw in with_updates:
                        with ui.card().classes("w-full"):
                            with ui.row().classes("w-full items-center justify-between"):
                                with ui.row().classes("items-center gap-3"):
                                    ui.icon("system_update").classes("text-2xl text-orange")
                                    with ui.column().classes("gap-0"):
                                        ui.label(fw.device_name).classes("font-semibold text-lg")
                                        ui.label(fw.model or "").classes("text-xs text-gray-500")
                                with ui.row().classes("items-center gap-4"):
                                    with ui.column().classes("items-end gap-0"):
                                        ui.label(f"Current: {fw.current_version or '?'}").classes(
                                            "text-sm text-gray-500"
                                        )
                                        ui.label(f"Available: {fw.available_version or '?'}").classes(
                                            "text-sm font-semibold text-orange"
                                        )
                                    ui.badge("UPDATE").props("color=orange")

                # Up to date section
                if up_to_date:
                    ui.label("Up to Date").classes("text-xl font-semibold mt-4")

                    columns = [
                        {"name": "name", "label": "Device", "field": "name", "align": "left"},
                        {"name": "model", "label": "Model", "field": "model", "align": "left"},
                        {"name": "version", "label": "Firmware", "field": "version", "align": "left"},
                        {"name": "checked", "label": "Last Checked", "field": "checked", "align": "left"},
                    ]
                    rows = [
                        {
                            "id": fw.id,
                            "name": fw.device_name,
                            "model": fw.model or "—",
                            "version": fw.current_version or "—",
                            "checked": (
                                fw.last_checked.strftime("%Y-%m-%d %H:%M")
                                if fw.last_checked else "Never"
                            ),
                        }
                        for fw in up_to_date
                    ]
                    ui.table(columns=columns, rows=rows, row_key="id").classes(
                        "w-full"
                    ).props("flat bordered dense")

                # Devices with unknown firmware
                unknown = [f for f in all_fw if not f.current_version]
                if unknown:
                    ui.label("Unknown Firmware").classes("text-xl font-semibold mt-4")
                    for fw in unknown:
                        with ui.row().classes("items-center gap-2"):
                            ui.icon("help").classes("text-gray-400")
                            ui.label(f"{fw.device_name} ({fw.model or 'Unknown model'})").classes(
                                "text-sm text-gray-500"
                            )

        refresh_firmware_list()
