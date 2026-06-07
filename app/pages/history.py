"""Changelog / history page."""

import json
from datetime import datetime, timezone, timedelta
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
        with ui.row().classes("gap-4 mb-4 items-end"):
            entity_filter = ui.select(
                {"all": "All", **{e.value: e.value.replace("_", " ").title() for e in EntityType}},
                value="all",
                label="Entity Type",
            ).classes("w-48")

            action_filter = ui.select(
                {"all": "All", **{a.value: a.value.title() for a in ActionType}},
                value="all",
                label="Action",
            ).classes("w-40")

            # Auto-refresh when filters change
            entity_filter.on("update:model-value", lambda: refresh_history())
            action_filter.on("update:model-value", lambda: refresh_history())

        # Retention controls
        with ui.row().classes("gap-2 mb-4 items-center"):
            ui.label("Retention:").classes("text-sm text-gray-500")
            retention_options = {
                0: "Keep all",
                30: "30 days",
                60: "60 days",
                90: "90 days",
                180: "6 months",
                365: "1 year",
            }
            retention_select = ui.select(
                retention_options, value=0, label="Auto-delete older than"
            ).classes("w-48")

            def purge_old_history():
                days = retention_select.value
                if not days:
                    ui.notify("Set a retention period first", type="warning")
                    return
                cutoff = datetime.now(timezone.utc) - timedelta(days=days)
                deleted = (
                    session.query(Changelog)
                    .filter(Changelog.timestamp < cutoff)
                    .delete()
                )
                session.commit()
                ui.notify(f"Purged {deleted} entries older than {days} days", type="positive")
                refresh_history()

            ui.button("Purge Now", on_click=purge_old_history).props(
                "flat color=orange size=sm"
            )

            # Clear all
            def confirm_clear_all():
                with ui.dialog() as dlg, ui.card():
                    total = session.query(Changelog).count()
                    ui.label(f"Delete ALL {total} changelog entries?").classes("text-lg font-semibold")
                    ui.label("This cannot be undone.").classes("text-sm text-red")
                    with ui.row().classes("justify-end gap-2 mt-3"):
                        ui.button("Cancel", on_click=dlg.close).props("flat")
                        ui.button("Delete All", on_click=lambda: (
                            session.query(Changelog).delete(),
                            session.commit(),
                            dlg.close(),
                            refresh_history(),
                            ui.notify("All history cleared", type="warning"),
                        )).props("color=red")
                dlg.open()

            ui.button("Clear All", on_click=confirm_clear_all).props(
                "flat color=red size=sm"
            )

        # Entry count
        count_label = ui.label("").classes("text-sm text-gray-400 mb-2")

        history_container = ui.column().classes("w-full gap-2")

        def refresh_history():
            history_container.clear()
            with history_container:
                entity_type = None
                if entity_filter.value != "all":
                    entity_type = EntityType(entity_filter.value)

                entries = get_changelog(session, entity_type=entity_type, limit=200)

                # Filter by action type client-side
                if action_filter.value != "all":
                    target_action = ActionType(action_filter.value)
                    entries = [e for e in entries if e.action == target_action]

                count_label.text = f"{len(entries)} entries"

                if not entries:
                    ui.label("No changes recorded for the selected filters.").classes(
                        "text-gray-500"
                    )
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
                                        "text-gray-400"
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
