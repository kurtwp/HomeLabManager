"""Backup and Restore page — manage database backups from the UI."""

from nicegui import ui

from app.services.backup_service import (
    create_backup,
    restore_backup,
    list_backups,
    delete_backup,
    get_db_size,
)
from app.pages.layout import page_layout


def render_backup():
    """Render the backup and restore page."""
    page_layout()

    with ui.column().classes("page-container w-full"):
        ui.label("Backup & Restore").classes("text-3xl font-bold")
        ui.label("Create and manage database backups.").classes("text-gray-500 mb-4")

        ui.separator()

        # Current database info
        with ui.card().classes("w-full mt-4"):
            ui.label("Current Database").classes("text-lg font-semibold mb-2")
            db_size = get_db_size()
            ui.label(f"Size: {db_size / (1024 * 1024):.2f} MB ({db_size:,} bytes)").classes(
                "text-sm text-gray-500"
            )

            def do_backup():
                result = create_backup()
                if result["success"]:
                    ui.notify(
                        f"Backup created: {result['filename']} ({result['size_bytes'] / 1024:.0f} KB)",
                        type="positive",
                    )
                    refresh_backups()
                else:
                    ui.notify(f"Backup failed: {result['error']}", type="negative")

            ui.button("Create Backup Now", icon="backup", on_click=do_backup).props(
                "color=primary"
            ).classes("mt-2")

        # Backup list
        ui.separator().classes("my-4")
        ui.label("Available Backups").classes("text-xl font-semibold")

        backups_container = ui.column().classes("w-full mt-2 gap-2")

        def refresh_backups():
            backups_container.clear()
            backups = list_backups()
            with backups_container:
                if not backups:
                    ui.label("No backups found. Create one above.").classes(
                        "text-gray-500 italic"
                    )
                    return

                for backup in backups:
                    with ui.card().classes("w-full"):
                        with ui.row().classes("w-full items-center justify-between"):
                            with ui.column().classes("gap-0"):
                                ui.label(backup["filename"]).classes("font-semibold font-mono")
                                ui.label(
                                    f"{backup['size_mb']} MB · "
                                    f"Created: {backup['created'].strftime('%Y-%m-%d %H:%M:%S UTC')}"
                                ).classes("text-xs text-gray-500")

                            with ui.row().classes("gap-2"):
                                ui.button(
                                    icon="restore",
                                    on_click=lambda b=backup: confirm_restore(b["filename"]),
                                ).props("flat round color=orange").tooltip("Restore this backup")
                                ui.button(
                                    icon="delete",
                                    on_click=lambda b=backup: confirm_delete(b["filename"]),
                                ).props("flat round color=red").tooltip("Delete this backup")

        def confirm_restore(filename: str):
            with ui.dialog() as dlg, ui.card():
                ui.label(f"Restore from '{filename}'?").classes("text-lg font-semibold")
                ui.label(
                    "This will replace the current database with this backup. "
                    "A safety backup will be created first."
                ).classes("text-sm text-orange")
                ui.label(
                    "The application must be restarted after restore."
                ).classes("text-sm text-red font-semibold mt-1")
                with ui.row().classes("justify-end gap-2 mt-3"):
                    ui.button("Cancel", on_click=dlg.close).props("flat")
                    ui.button("Restore", on_click=lambda: (
                        do_restore(filename),
                        dlg.close(),
                    )).props("color=orange")
            dlg.open()

        def do_restore(filename: str):
            result = restore_backup(filename)
            if result["success"]:
                ui.notify(
                    "Database restored! Restart the application for changes to take effect.",
                    type="positive",
                )
            else:
                ui.notify(f"Restore failed: {result['error']}", type="negative")

        def confirm_delete(filename: str):
            with ui.dialog() as dlg, ui.card():
                ui.label(f"Delete backup '{filename}'?").classes("text-lg")
                with ui.row().classes("justify-end gap-2 mt-2"):
                    ui.button("Cancel", on_click=dlg.close).props("flat")
                    ui.button("Delete", on_click=lambda: (
                        delete_backup(filename),
                        dlg.close(),
                        refresh_backups(),
                        ui.notify("Backup deleted", type="warning"),
                    )).props("color=red")
            dlg.open()

        refresh_backups()

        # Tips
        with ui.card().classes("w-full mt-4"):
            ui.label("Tips").classes("text-lg font-semibold mb-2")
            tips = [
                "Create a backup before major changes (bulk imports, upgrades)",
                "Backups are stored in the 'backups/' directory alongside your app",
                "Restoring creates a safety backup of the current database first",
                "A restart is required after restoring for the app to use the restored data",
                "Backups include the full database: networks, IPs, devices, history, uptime data",
            ]
            for tip in tips:
                with ui.row().classes("items-start gap-2"):
                    ui.icon("lightbulb").classes("text-sm text-blue mt-0.5")
                    ui.label(tip).classes("text-sm text-gray-500")
