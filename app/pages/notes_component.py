"""Reusable notes component — multiple titled, collapsible notes per entity."""

from datetime import datetime, timezone
from nicegui import ui
from sqlalchemy.orm import Session

from app.models.note import Note


def render_notes(session: Session, entity_type: str, entity_id: int):
    """
    Render a notes section with multiple titled, collapsible notes.

    Args:
        session: Active DB session (will use fresh sessions for saves)
        entity_type: "ip" or "device"
        entity_id: ID of the IP or device
    """
    with ui.card().classes("w-full"):
        with ui.row().classes("w-full items-center justify-between mb-2"):
            ui.label("Notes").classes("text-lg font-semibold")
            ui.button("Add Note", icon="note_add", on_click=lambda: add_dialog.open()).props(
                "color=primary size=sm"
            )

        notes_container = ui.column().classes("w-full gap-2")

        def refresh_notes():
            notes_container.clear()
            from app.database.db import get_session_direct
            s = get_session_direct()
            notes = (
                s.query(Note)
                .filter(
                    Note.entity_type == entity_type,
                    Note.entity_id == entity_id,
                    Note.is_archived == 0,
                )
                .order_by(Note.created_at.desc())
                .all()
            )
            with notes_container:
                if not notes:
                    ui.label("No notes yet.").classes("text-sm text-gray-500 italic")
                else:
                    for note in notes:
                        timestamp = note.created_at.strftime("%Y-%m-%d %H:%M") if note.created_at else ""
                        with ui.expansion(
                            f"{timestamp} — {note.title}",
                            icon="description",
                        ).classes("w-full"):
                            ui.markdown(note.body).classes("w-full")
                            with ui.row().classes("gap-2 mt-2"):
                                ui.button(
                                    "Edit", icon="edit",
                                    on_click=lambda n=note: open_edit(n),
                                ).props("flat size=xs color=primary")
                                ui.button(
                                    "Delete", icon="delete",
                                    on_click=lambda n=note: confirm_delete(n),
                                ).props("flat size=xs color=red")
            s.close()

        def open_edit(note):
            edit_title.value = note.title
            edit_body.value = note.body
            edit_dialog.note_id = note.id
            edit_dialog.open()

        def confirm_delete(note):
            with ui.dialog() as dlg, ui.card():
                ui.label(f"Delete note '{note.title}'?").classes("text-lg")
                with ui.row().classes("justify-end gap-2 mt-2"):
                    ui.button("Cancel", on_click=dlg.close).props("flat")
                    ui.button("Delete", on_click=lambda: (
                        _delete_note(note.id),
                        dlg.close(),
                    )).props("color=red")
            dlg.open()

        def _delete_note(note_id):
            from app.database.db import get_session_direct
            s = get_session_direct()
            n = s.query(Note).filter(Note.id == note_id).first()
            if n:
                s.delete(n)
                s.commit()
            s.close()
            ui.notify("Note deleted", type="warning")
            refresh_notes()

        refresh_notes()

    # Add note dialog
    with ui.dialog() as add_dialog, ui.card().classes("w-[600px]"):
        ui.label("Add Note").classes("text-xl font-bold mb-2")
        new_title = ui.input("Title *", placeholder="e.g. Configuration change").classes("w-full")

        with ui.tabs().classes("w-full") as add_tabs:
            add_edit_tab = ui.tab("Edit")
            add_preview_tab = ui.tab("Preview")

        with ui.tab_panels(add_tabs, value=add_edit_tab).classes("w-full"):
            with ui.tab_panel(add_edit_tab):
                new_body = ui.textarea(
                    "Note (Markdown)", placeholder="Write your note..."
                ).classes("w-full").props('rows="8"')
            with ui.tab_panel(add_preview_tab):
                add_preview_md = ui.markdown("*Start writing...*").classes("w-full")

        add_tabs.on("update:model-value", lambda: add_preview_md.set_content(new_body.value or "*Start writing...*"))

        def save_new_note():
            if not new_title.value:
                ui.notify("Title is required", type="warning")
                return
            from app.database.db import get_session_direct
            s = get_session_direct()
            note = Note(
                title=new_title.value.strip(),
                body=new_body.value or "",
                entity_type=entity_type,
                entity_id=entity_id,
            )
            s.add(note)
            s.commit()
            s.close()
            ui.notify("Note saved!", type="positive")
            new_title.value = ""
            new_body.value = ""
            add_dialog.close()
            refresh_notes()

        with ui.row().classes("justify-end gap-2 mt-2"):
            ui.button("Cancel", on_click=add_dialog.close).props("flat")
            ui.button("Save", on_click=save_new_note).props("color=primary")

    # Edit note dialog
    with ui.dialog() as edit_dialog, ui.card().classes("w-[600px]"):
        edit_dialog.note_id = None
        ui.label("Edit Note").classes("text-xl font-bold mb-2")
        edit_title = ui.input("Title").classes("w-full")

        with ui.tabs().classes("w-full") as edit_tabs:
            edit_edit_tab = ui.tab("Edit")
            edit_preview_tab = ui.tab("Preview")

        with ui.tab_panels(edit_tabs, value=edit_edit_tab).classes("w-full"):
            with ui.tab_panel(edit_edit_tab):
                edit_body = ui.textarea("Note (Markdown)").classes("w-full").props('rows="8"')
            with ui.tab_panel(edit_preview_tab):
                edit_preview_md = ui.markdown("").classes("w-full")

        edit_tabs.on("update:model-value", lambda: edit_preview_md.set_content(edit_body.value or ""))

        def save_edit_note():
            from app.database.db import get_session_direct
            s = get_session_direct()
            note = s.query(Note).filter(Note.id == edit_dialog.note_id).first()
            if note:
                note.title = edit_title.value.strip()
                note.body = edit_body.value or ""
                note.updated_at = datetime.now(timezone.utc)
                s.commit()
            s.close()
            ui.notify("Note updated!", type="positive")
            edit_dialog.close()
            refresh_notes()

        with ui.row().classes("justify-end gap-2 mt-2"):
            ui.button("Cancel", on_click=edit_dialog.close).props("flat")
            ui.button("Save", on_click=save_edit_note).props("color=primary")
