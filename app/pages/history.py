"""Changelog / history page."""

import json
from nicegui import ui

from app.database.db import get_session_direct as get_session
from app.models.changelog import Changelog, EntityType, ActionType
from app.services.changelog_service import get_changelog
from app.utils.formatters import format_timestamp
from app.pages.layout import page_layout


def render_history():
    """Render the changelog/history page."""
    page_layout()

    session = get_session()

    with ui.column().classes("page-container w-full"):
        ui.label("Change History").classes("text-3xl font-bold")
        ui.separator().classes("my-4")

        # Filters
        with ui.row().classes("gap-2 mb-4"):
            entity_filter = ui.select(
                {"all": "All", **{e.value: e.value.replace("_", " ").title() for e in EntityType}},
                value="all",
                label="Entity Type",
            ).classes("w-48")
            ui.button("Filter", on_click=lambda: refresh_history()).props("flat")

        history_container = ui.column().classes("w-full gap-2")

        def refresh_history():
            history_container.clear()
            with history_container:
                entity_type = None
                if entity_filter.value != "all":
                    entity_type = EntityType(entity_filter.value)
                entries = get_changelog(session, entity_type=entity_type, limit=100)

                if not entries:
                    ui.label("No changes recorded yet.").classes("text-gray-500")
                    return

                for entry in entries:
                    action_colors = {
                        ActionType.CREATED: "green",
                        ActionType.UPDATED: "blue",
                        ActionType.DELETED: "red",
                    }
                    action_icons = {
                        ActionType.CREATED: "add_circle",
                        ActionType.UPDATED: "edit",
                        ActionType.DELETED: "remove_circle",
                    }

                    with ui.row().classes("w-full items-start gap-3 changelog-entry"):
                        ui.icon(
                            action_icons.get(entry.action, "info")
                        ).classes(f"text-{action_colors.get(entry.action, 'gray')} mt-1")

                        with ui.column().classes("gap-0 flex-1"):
                            with ui.row().classes("items-center gap-2"):
                                ui.label(
                                    f"{entry.action.value.title()} "
                                    f"{entry.entity_type.value.replace('_', ' ').title()}"
                                ).classes("font-semibold")
                                if entry.entity_name:
                                    ui.label(f"— {entry.entity_name}").classes(
                                        "text-gray-600"
                                    )
                            ui.label(format_timestamp(entry.timestamp)).classes(
                                "text-xs text-gray-400"
                            )
                            if entry.comment:
                                ui.label(entry.comment).classes(
                                    "text-sm text-gray-500 italic"
                                )
                            # Show diff for updates
                            if entry.old_values and entry.new_values:
                                try:
                                    old = json.loads(entry.old_values)
                                    new = json.loads(entry.new_values)
                                    diff_parts = []
                                    for key in new:
                                        old_val = old.get(key, "—")
                                        new_val = new[key]
                                        if old_val != new_val:
                                            diff_parts.append(
                                                f"{key}: {old_val} → {new_val}"
                                            )
                                    if diff_parts:
                                        ui.label(
                                            " | ".join(diff_parts)
                                        ).classes("text-xs font-mono text-gray-500")
                                except (json.JSONDecodeError, TypeError):
                                    pass

        refresh_history()

    session.close()
