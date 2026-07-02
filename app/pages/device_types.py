"""Device Types management page — add, edit, delete device type categories."""

from nicegui import ui

from app.database.db import get_session_direct as get_session
from app.models.device import DeviceType, Device
from app.pages.layout import page_layout


def render_device_types():
    """Render the device types management page."""
    page_layout()

    session = get_session()

    with ui.column().classes("page-container w-full"):
        with ui.row().classes("w-full items-center justify-between"):
            ui.label("Manage Device Types").classes("text-3xl font-bold")
            ui.button("Add Type", on_click=lambda: add_dialog.open()).props(
                "color=primary icon=add"
            )

        ui.separator().classes("my-4")

        types_container = ui.column().classes("w-full gap-2")

        def refresh_types():
            types_container.clear()
            device_types = session.query(DeviceType).order_by(DeviceType.name).all()
            with types_container:
                if not device_types:
                    ui.label("No device types defined.").classes("text-gray-500")
                    return

                for dt in device_types:
                    device_count = session.query(Device).filter(Device.device_type_id == dt.id).count()
                    with ui.card().classes("w-full"):
                        with ui.row().classes("w-full items-center justify-between"):
                            with ui.row().classes("items-center gap-3"):
                                ui.icon(dt.icon or "devices_other").classes("text-xl text-gray-500")
                                ui.label(dt.name).classes("font-semibold text-lg")
                                ui.badge(f"{device_count} devices").props("color=blue outline").classes("text-xs")
                                if dt.description:
                                    ui.label(dt.description).classes("text-sm text-gray-500")

                            with ui.row().classes("gap-1"):
                                ui.button(
                                    icon="edit",
                                    on_click=lambda d=dt: open_edit(d),
                                ).props("flat round size=sm")
                                ui.button(
                                    icon="delete",
                                    on_click=lambda d=dt, c=device_count: confirm_delete(d, c),
                                ).props("flat round size=sm color=red")

        def open_edit(dt):
            edit_name.value = dt.name
            edit_icon.value = dt.icon or ""
            edit_desc.value = dt.description or ""
            edit_dialog.dt_id = dt.id
            edit_dialog.open()

        def confirm_delete(dt, count):
            with ui.dialog() as dlg, ui.card():
                ui.label(f"Delete device type '{dt.name}'?").classes("text-lg font-semibold")
                if count > 0:
                    ui.label(
                        f"⚠️ {count} device(s) use this type. They will be set to 'no type'."
                    ).classes("text-sm text-orange")
                with ui.row().classes("justify-end gap-2 mt-3"):
                    ui.button("Cancel", on_click=dlg.close).props("flat")
                    ui.button("Delete", on_click=lambda: (
                        _delete_type(dt.id),
                        dlg.close(),
                    )).props("color=red")
            dlg.open()

        def _delete_type(type_id):
            # Unassign devices from this type
            session.query(Device).filter(Device.device_type_id == type_id).update(
                {Device.device_type_id: None}
            )
            dt = session.query(DeviceType).filter(DeviceType.id == type_id).first()
            if dt:
                session.delete(dt)
            session.commit()
            ui.notify("Device type deleted", type="warning")
            refresh_types()

        refresh_types()

    # Add type dialog
    with ui.dialog() as add_dialog, ui.card().classes("w-96"):
        ui.label("New Device Type").classes("text-xl font-bold mb-2")
        new_name = ui.input("Name *", placeholder="e.g. Firewall").classes("w-full")
        new_icon = ui.input(
            "Icon (Material icon name)", placeholder="e.g. security, router, wifi"
        ).classes("w-full")
        ui.label("Browse icons at fonts.google.com/icons").classes("text-xs text-gray-500")
        new_desc = ui.input("Description (optional)").classes("w-full")

        def save_new_type():
            if not new_name.value:
                ui.notify("Name is required", type="warning")
                return
            existing = session.query(DeviceType).filter(DeviceType.name == new_name.value).first()
            if existing:
                ui.notify("Type already exists", type="negative")
                return
            dt = DeviceType(
                name=new_name.value.strip(),
                icon=new_icon.value.strip() or None,
                description=new_desc.value.strip() or None,
            )
            session.add(dt)
            session.commit()
            ui.notify(f"Created '{dt.name}'", type="positive")
            new_name.value = ""
            new_icon.value = ""
            new_desc.value = ""
            add_dialog.close()
            refresh_types()

        with ui.row().classes("justify-end gap-2 mt-3"):
            ui.button("Cancel", on_click=add_dialog.close).props("flat")
            ui.button("Save", on_click=save_new_type).props("color=primary")

    # Edit type dialog
    with ui.dialog() as edit_dialog, ui.card().classes("w-96"):
        edit_dialog.dt_id = None
        ui.label("Edit Device Type").classes("text-xl font-bold mb-2")
        edit_name = ui.input("Name").classes("w-full")
        edit_icon = ui.input("Icon").classes("w-full")
        edit_desc = ui.input("Description").classes("w-full")

        def save_edit():
            dt = session.query(DeviceType).filter(DeviceType.id == edit_dialog.dt_id).first()
            if dt:
                dt.name = edit_name.value.strip()
                dt.icon = edit_icon.value.strip() or None
                dt.description = edit_desc.value.strip() or None
                session.commit()
                ui.notify("Updated!", type="positive")
                edit_dialog.close()
                refresh_types()

        with ui.row().classes("justify-end gap-2 mt-3"):
            ui.button("Cancel", on_click=edit_dialog.close).props("flat")
            ui.button("Save", on_click=save_edit).props("color=primary")

    session.close()
