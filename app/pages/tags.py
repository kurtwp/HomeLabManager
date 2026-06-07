"""Tag management page — CRUD for tags/labels."""

from nicegui import ui

from app.database.db import get_session_direct as get_session
from app.models.tag import Tag
from app.pages.layout import page_layout


def render_tags():
    """Render the tag management page."""
    page_layout()

    session = get_session()

    with ui.column().classes("page-container w-full"):
        with ui.row().classes("w-full items-center justify-between"):
            ui.label("Tags & Labels").classes("text-3xl font-bold")
            ui.button("New Tag", on_click=lambda: add_dialog.open()).props(
                "color=primary icon=add"
            )

        ui.separator().classes("my-4")

        tags_container = ui.column().classes("w-full gap-2")

        def refresh_tags():
            tags_container.clear()
            tags = session.query(Tag).order_by(Tag.name).all()
            with tags_container:
                if not tags:
                    ui.label("No tags yet.").classes("text-gray-500")
                    return

                with ui.row().classes("w-full flex-wrap gap-3"):
                    for tag in tags:
                        with ui.card().classes("w-64"):
                            with ui.row().classes("items-center justify-between w-full"):
                                with ui.row().classes("items-center gap-2"):
                                    ui.html(
                                        f'<div style="width:20px; height:20px; '
                                        f'border-radius:50%; background:{tag.color};"></div>'
                                    )
                                    ui.label(tag.name).classes("font-semibold")

                                with ui.row().classes("gap-1"):
                                    ui.button(
                                        icon="edit",
                                        on_click=lambda t=tag: open_edit(t),
                                    ).props("flat round size=sm")
                                    ui.button(
                                        icon="delete",
                                        on_click=lambda t=tag: confirm_delete(t),
                                    ).props("flat round size=sm color=red")

                            # Usage counts
                            ip_count = len(tag.ip_addresses)
                            dev_count = len(tag.devices)
                            net_count = len(tag.networks)
                            ui.label(
                                f"{ip_count} IPs · {dev_count} devices · {net_count} networks"
                            ).classes("text-xs text-gray-500")

        def open_edit(tag: Tag):
            edit_name.value = tag.name
            edit_color.value = tag.color
            edit_dialog.tag_id = tag.id
            edit_dialog.open()

        def confirm_delete(tag: Tag):
            with ui.dialog() as confirm, ui.card():
                ui.label(f"Delete tag '{tag.name}'?").classes("text-lg")
                ui.label(
                    "It will be removed from all associated items."
                ).classes("text-sm text-gray-500")
                with ui.row().classes("justify-end gap-2 mt-2"):
                    ui.button("Cancel", on_click=confirm.close).props("flat")
                    ui.button(
                        "Delete",
                        on_click=lambda: (
                            _delete_tag(tag.id),
                            confirm.close(),
                        ),
                    ).props("color=red")
            confirm.open()

        def _delete_tag(tag_id: int):
            tag = session.query(Tag).filter(Tag.id == tag_id).first()
            if tag:
                session.delete(tag)
                session.commit()
                ui.notify("Tag deleted", type="warning")
                refresh_tags()

        refresh_tags()

    # Add tag dialog
    with ui.dialog() as add_dialog, ui.card().classes("w-80"):
        ui.label("New Tag").classes("text-xl font-bold mb-2")
        new_name = ui.input("Tag Name *", placeholder="e.g. production").classes("w-full")
        new_color = ui.color_input("Color", value="#1976d2").classes("w-full")

        def save_new_tag():
            if not new_name.value:
                ui.notify("Name is required", type="warning")
                return
            existing = session.query(Tag).filter(Tag.name == new_name.value).first()
            if existing:
                ui.notify("Tag already exists", type="negative")
                return
            tag = Tag(name=new_name.value.strip().lower(), color=new_color.value)
            session.add(tag)
            session.commit()
            ui.notify("Tag created!", type="positive")
            new_name.value = ""
            add_dialog.close()
            refresh_tags()

        with ui.row().classes("justify-end gap-2 mt-2"):
            ui.button("Cancel", on_click=add_dialog.close).props("flat")
            ui.button("Save", on_click=save_new_tag).props("color=primary")

    # Edit tag dialog
    with ui.dialog() as edit_dialog, ui.card().classes("w-80"):
        edit_dialog.tag_id = None
        ui.label("Edit Tag").classes("text-xl font-bold mb-2")
        edit_name = ui.input("Tag Name").classes("w-full")
        edit_color = ui.color_input("Color").classes("w-full")

        def save_edit():
            tag = session.query(Tag).filter(Tag.id == edit_dialog.tag_id).first()
            if tag:
                tag.name = edit_name.value.strip().lower()
                tag.color = edit_color.value
                session.commit()
                ui.notify("Tag updated!", type="positive")
                edit_dialog.close()
                refresh_tags()

        with ui.row().classes("justify-end gap-2 mt-2"):
            ui.button("Cancel", on_click=edit_dialog.close).props("flat")
            ui.button("Save", on_click=save_edit).props("color=primary")

    session.close()
