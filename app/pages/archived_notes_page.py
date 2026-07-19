"""Archived Notes page — browse and search notes from deleted IPs/devices."""

from nicegui import ui

from app.database.db import get_session_direct as get_session
from app.models.note import Note
from app.pages.layout import page_layout


def render_archived_notes():
    """Render the archived notes page."""
    page_layout()

    session = get_session()

    with ui.column().classes("page-container w-full"):
        ui.label("Archived Notes").classes("text-3xl font-bold")
        ui.label(
            "Notes preserved from deleted IPs and devices. Search by IP address or hostname."
        ).classes("text-gray-500 mb-4")

        ui.separator()

        # Search
        with ui.row().classes("w-full gap-4 items-end mt-4"):
            search_input = ui.input(
                "Search", placeholder="IP address, hostname, or note content..."
            ).classes("w-96")
            search_input.on("keydown.enter", lambda: refresh_notes())
            ui.button("Search", icon="search", on_click=lambda: refresh_notes()).props(
                "color=primary"
            )
            ui.button("Show All", on_click=lambda: (setattr(search_input, 'value', ''), refresh_notes())).props(
                "flat"
            )

        notes_container = ui.column().classes("w-full mt-4 gap-3")

        def refresh_notes():
            notes_container.clear()

            query = session.query(Note).filter(Note.is_archived == 1)

            # Apply search filter
            if search_input.value:
                search_term = f"%{search_input.value}%"
                query = query.filter(
                    (Note.archived_ip.ilike(search_term))
                    | (Note.archived_hostname.ilike(search_term))
                    | (Note.title.ilike(search_term))
                    | (Note.body.ilike(search_term))
                )

            notes = query.order_by(Note.created_at.desc()).limit(100).all()

            with notes_container:
                if not notes:
                    ui.label("No archived notes found.").classes("text-gray-500 italic")
                    return

                ui.label(f"{len(notes)} archived note(s)").classes("text-sm text-gray-400 mb-2")

                for note in notes:
                    with ui.card().classes("w-full"):
                        with ui.row().classes("w-full items-center justify-between"):
                            with ui.row().classes("items-center gap-3"):
                                ui.icon("archive").classes("text-gray-400")
                                with ui.column().classes("gap-0"):
                                    ui.label(note.title).classes("font-semibold")
                                    with ui.row().classes("gap-3"):
                                        if note.archived_ip:
                                            ui.badge(note.archived_ip).props("color=blue outline").classes("text-xs")
                                        if note.archived_hostname:
                                            ui.badge(note.archived_hostname).props("color=gray outline").classes("text-xs")
                                        ui.label(
                                            note.created_at.strftime("%Y-%m-%d %H:%M") if note.created_at else "—"
                                        ).classes("text-xs text-gray-400")

                            ui.button(
                                icon="delete",
                                on_click=lambda n=note: confirm_delete(n),
                            ).props("flat round size=sm color=red").tooltip("Permanently delete")

                        # Note body (collapsible for long notes)
                        if note.body:
                            if len(note.body) > 200:
                                with ui.expansion("View Content", icon="article").classes("w-full mt-2"):
                                    ui.markdown(note.body).classes("w-full text-sm")
                            else:
                                ui.markdown(note.body).classes("w-full text-sm mt-2")

        def confirm_delete(note):
            with ui.dialog() as dlg, ui.card():
                ui.label("Permanently delete this archived note?").classes("text-lg")
                ui.label(f"'{note.title}' — {note.archived_ip or ''} {note.archived_hostname or ''}").classes(
                    "text-sm text-gray-500"
                )
                ui.label("This cannot be undone.").classes("text-sm text-red")
                with ui.row().classes("justify-end gap-2 mt-2"):
                    ui.button("Cancel", on_click=dlg.close).props("flat")
                    ui.button("Delete", on_click=lambda: (
                        _delete_note(note.id),
                        dlg.close(),
                        refresh_notes(),
                    )).props("color=red")
            dlg.open()

        def _delete_note(note_id):
            n = session.query(Note).filter(Note.id == note_id).first()
            if n:
                session.delete(n)
                session.commit()
                ui.notify("Note permanently deleted", type="warning")

        refresh_notes()

    session.close()
