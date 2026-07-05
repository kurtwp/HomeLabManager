"""PSTN Audit Trail page — view recent changes across the PSTN module."""

from nicegui import ui

from app.database.pstn_db import get_pstn_session_direct as get_session
from app.services.pstn_service import get_pstn_audit_log
from app.pages.layout import page_layout


ACTION_COLORS = {
    "created": "green",
    "updated": "blue",
    "deleted": "red",
}

ENTITY_ICONS = {
    "range": "view_list",
    "number": "phone",
    "customer": "person",
}


def render_pstn_audit():
    """Render the PSTN Audit Trail page."""
    page_layout()

    session = get_session()

    with ui.column().classes("page-container w-full"):
        ui.label("PSTN Audit Trail").classes("text-3xl font-bold")
        ui.label("Recent changes across customers, ranges, and numbers.").classes(
            "text-sm text-gray-500 mb-2"
        )

        ui.separator().classes("my-4")

        # Filter row
        with ui.row().classes("w-full gap-3 items-end"):
            filter_type = ui.select(
                {"": "All Types", "customer": "Customer", "range": "Range", "number": "Number"},
                value="",
                label="Entity Type",
            ).classes("w-44")
            filter_limit = ui.select(
                {50: "Last 50", 100: "Last 100", 200: "Last 200"},
                value=50,
                label="Limit",
            ).classes("w-32")
            ui.button("Refresh", icon="refresh", on_click=lambda: refresh_audit()).props(
                "flat color=primary"
            )

        audit_container = ui.column().classes("w-full mt-4")

        def refresh_audit():
            audit_container.clear()
            entity_type = filter_type.value if filter_type.value else None
            limit = int(filter_limit.value)
            entries = get_pstn_audit_log(session, entity_type=entity_type, limit=limit)

            with audit_container:
                if not entries:
                    ui.label("No audit entries found.").classes("text-gray-500 italic")
                    return

                ui.label(f"{len(entries)} entries").classes("text-sm text-gray-400 mb-2")

                columns = [
                    {"name": "timestamp", "label": "Timestamp", "field": "timestamp", "align": "left", "sortable": True},
                    {"name": "action", "label": "Action", "field": "action", "align": "center"},
                    {"name": "entity_type", "label": "Entity", "field": "entity_type", "align": "center"},
                    {"name": "entity_id", "label": "ID", "field": "entity_id", "align": "center"},
                    {"name": "details", "label": "Details", "field": "details", "align": "left"},
                ]
                rows = [
                    {
                        "id": e.id,
                        "timestamp": e.timestamp.strftime("%Y-%m-%d %H:%M:%S") if e.timestamp else "—",
                        "action": e.action,
                        "entity_type": e.entity_type,
                        "entity_id": e.entity_id,
                        "details": (e.details or "—")[:80],
                    }
                    for e in entries
                ]

                table = ui.table(
                    columns=columns, rows=rows, row_key="id"
                ).classes("w-full").props("flat bordered dense")

                table.add_slot(
                    "body-cell-action",
                    '''
                    <q-td :props="props">
                        <q-badge :color="
                            props.value === 'created' ? 'green' :
                            props.value === 'updated' ? 'blue' :
                            props.value === 'deleted' ? 'red' : 'grey'
                        ">
                            {{ props.value }}
                        </q-badge>
                    </q-td>
                    ''',
                )

                table.add_slot(
                    "body-cell-entity_type",
                    '''
                    <q-td :props="props">
                        <q-badge color="grey-7" outline>
                            {{ props.value }}
                        </q-badge>
                    </q-td>
                    ''',
                )

        refresh_audit()

    session.close()
