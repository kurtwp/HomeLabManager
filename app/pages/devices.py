"""Devices management page."""

from nicegui import ui

from app.database.db import get_session_direct as get_session
from app.models.device import Device, DeviceType
from app.models.tag import Tag
from app.services.device_service import (
    create_device,
    get_all_devices,
    get_all_device_types,
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
            with ui.row().classes("gap-2"):
                ui.button("Add Device", on_click=lambda: add_dialog.open()).props(
                    "color=primary icon=add"
                )
                ui.button("Delete All", on_click=lambda: confirm_delete_all_devices()).props(
                    "color=red icon=delete_sweep outline"
                )

        ui.separator().classes("my-4")

        # Filter controls
        device_types = get_all_device_types(session)
        type_options = {0: "All Types"}
        type_options.update({dt.id: dt.name for dt in device_types})

        all_tags = session.query(Tag).order_by(Tag.name).all()
        tag_options = {0: "All Tags"}
        tag_options.update({t.id: t.name for t in all_tags})

        with ui.row().classes("w-full gap-2 items-center flex-wrap"):
            type_filter = ui.select(
                type_options, value=0, label="Device Type"
            ).classes("w-48")
            tag_filter = ui.select(
                tag_options, value=0, label="Tag"
            ).classes("w-44")
            ui.button("Filter", on_click=lambda: refresh_devices()).props("flat")

        # Devices list
        devices_container = ui.column().classes("w-full mt-4 gap-2")

        def refresh_devices():
            devices_container.clear()
            with devices_container:
                query = session.query(Device)
                if type_filter.value and type_filter.value != 0:
                    query = query.filter(Device.device_type_id == type_filter.value)
                if tag_filter.value and tag_filter.value != 0:
                    query = query.filter(
                        Device.tags.any(Tag.id == tag_filter.value)
                    )
                devices = query.order_by(Device.name).all()

                if not devices:
                    ui.label("No devices found.").classes("text-gray-500")
                    return

                for d in devices:
                    with ui.card().classes("w-full cursor-pointer").on(
                        "click", lambda dev=d: ui.navigate.to(f"/devices/{dev.id}")
                    ):
                        with ui.row().classes("w-full items-center justify-between"):
                            with ui.row().classes("items-center gap-3"):
                                # Device type icon
                                icon_name = d.device_type.icon if d.device_type and d.device_type.icon else "devices_other"
                                ui.icon(icon_name).classes("text-xl text-gray-600")
                                ui.label(d.name).classes("font-semibold")
                                if d.device_type:
                                    ui.badge(d.device_type.name).props("color=gray outline").classes("text-xs")
                                # Tag chips
                                for tag in d.tags:
                                    ui.html(
                                        f'<span style="font-size:0.65rem; padding:1px 8px; '
                                        f'border-radius:10px; background:{tag.color}20; '
                                        f'color:{tag.color}; border:1px solid {tag.color}40; '
                                        f'font-weight:500;">{tag.name}</span>'
                                    )

                            with ui.row().classes("items-center gap-4"):
                                info_parts = []
                                if d.manufacturer:
                                    info_parts.append(d.manufacturer)
                                if d.model:
                                    info_parts.append(d.model)
                                if info_parts:
                                    ui.label(" · ".join(info_parts)).classes(
                                        "text-sm text-gray-400"
                                    )
                                if d.mac_address:
                                    ui.label(format_mac(d.mac_address)).classes(
                                        "text-xs font-mono text-gray-400"
                                    )
                                ui.badge(f"{len(d.ip_addresses)} IPs").props(
                                    "color=blue outline"
                                ).classes("text-xs")
                                ui.button(
                                    icon="delete",
                                    on_click=lambda dev=d: confirm_delete_device(dev),
                                ).props("flat round size=sm color=red")

        def confirm_delete_device(dev):
            with ui.dialog() as dlg, ui.card():
                ui.label(f"Delete device '{dev.name}'?").classes("text-lg font-semibold")
                with ui.row().classes("justify-end gap-2 mt-3"):
                    ui.button("Cancel", on_click=dlg.close).props("flat")
                    ui.button("Delete", on_click=lambda: (
                        delete_device(session, dev.id),
                        dlg.close(),
                        refresh_devices(),
                        ui.notify(f"Deleted {dev.name}", type="warning"),
                    )).props("color=red")
            dlg.open()

        def confirm_delete_all_devices():
            with ui.dialog() as dlg, ui.card():
                total = session.query(Device).count()
                ui.label(f"Delete ALL {total} devices?").classes("text-lg font-semibold")
                ui.label("This cannot be undone.").classes("text-sm text-red")
                with ui.row().classes("justify-end gap-2 mt-3"):
                    ui.button("Cancel", on_click=dlg.close).props("flat")
                    ui.button("Delete All", on_click=lambda: (
                        _delete_all_devices(),
                        dlg.close(),
                    )).props("color=red")
            dlg.open()

        def _delete_all_devices():
            count = session.query(Device).count()
            session.query(Device).delete()
            session.commit()
            refresh_devices()
            ui.notify(f"Deleted {count} devices", type="warning")

        refresh_devices()

    # Add device dialog
    with ui.dialog() as add_dialog, ui.card().classes("w-96"):
        ui.label("Add Device").classes("text-xl font-bold mb-2")

        dt_options = {dt.id: dt.name for dt in device_types}

        name_input = ui.input("Name *", placeholder="e.g. Office Printer").classes("w-full")
        type_select = ui.select(
            dt_options, label="Device Type"
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
