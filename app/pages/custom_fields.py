"""Custom fields management page."""

from nicegui import ui

from app.database.db import get_session_direct as get_session
from app.models.custom_field import CustomFieldDefinition, FieldType, EntityType
from app.services.custom_field_service import (
    create_field_definition,
    get_all_field_definitions,
    get_field_definitions_for_entity,
    get_field_values_for_entity,
    set_field_value,
    delete_field_definition,
)
from app.pages.layout import page_layout


def render_custom_fields():
    """Render the custom fields management page."""
    page_layout()

    session = get_session()

    with ui.column().classes("page-container w-full"):
        with ui.row().classes("w-full items-center justify-between"):
            ui.label("Custom Fields").classes("text-3xl font-bold")
            ui.button("New Field", on_click=lambda: add_dialog.open()).props(
                "color=primary icon=add"
            )

        ui.separator().classes("my-4")

        # Filter by entity type
        with ui.row().classes("gap-2 mb-4"):
            entity_filter = ui.select(
                {"all": "All", "ip": "IP Addresses", "device": "Devices", "network": "Networks"},
                value="all",
                label="Entity Type",
            ).classes("w-48")
            entity_filter.on("update:model-value", lambda: refresh_fields())

        # Fields table
        fields_container = ui.column().classes("w-full gap-3")

        def refresh_fields():
            fields_container.clear()
            with fields_container:
                if entity_filter.value == "all":
                    fields = get_all_field_definitions(session)
                else:
                    fields = get_field_definitions_for_entity(session, entity_filter.value)

                if not fields:
                    ui.label("No custom fields defined yet.").classes("text-gray-500")
                    return

                columns = [
                    {"name": "name", "label": "Name", "field": "name", "align": "left"},
                    {"name": "field_type", "label": "Type", "field": "field_type", "align": "center"},
                    {"name": "entity_type", "label": "Entity", "field": "entity_type", "align": "center"},
                    {"name": "required", "label": "Required", "field": "required", "align": "center"},
                    {"name": "default", "label": "Default", "field": "default", "align": "left"},
                    {"name": "actions", "label": "Actions", "field": "actions", "align": "center"},
                ]
                rows = [
                    {
                        "id": f.id,
                        "name": f.name,
                        "field_type": f.field_type,
                        "entity_type": f.entity_type,
                        "required": "Yes" if f.required else "No",
                        "default": f.default_value or "—",
                    }
                    for f in fields
                ]

                table = ui.table(columns=columns, rows=rows, row_key="id").classes(
                    "w-full"
                ).props("flat bordered dense")

                table.add_slot(
                    "body-cell-actions",
                    """
                    <q-td :props="props">
                        <q-btn flat round dense icon="delete" color="negative"
                            @click="$parent.$emit('delete', props.row)" />
                    </q-td>
                    """,
                )

                def handle_delete(e):
                    row = e.args
                    delete_field_definition(session, row["id"])
                    ui.notify(f"Deleted field: {row['name']}", type="positive")
                    refresh_fields()

                table.on("delete", handle_delete)

        refresh_fields()

    # Add field dialog
    with ui.dialog() as add_dialog, ui.card().classes("w-96"):
        ui.label("New Custom Field").classes("text-xl font-bold mb-2")

        name_input = ui.input("Field Name *", placeholder="e.g. Purchase Date").classes("w-full")
        type_select = ui.select(
            {t.value: t.value.title() for t in FieldType},
            value=FieldType.TEXT.value,
            label="Field Type",
        ).classes("w-full")
        entity_select = ui.select(
            {e.value: e.value.title() for e in EntityType},
            value=EntityType.DEVICE.value,
            label="Entity Type",
        ).classes("w-full")
        options_input = ui.input(
            "Options (comma-separated, for Select type)",
            placeholder="option1, option2, option3",
        ).classes("w-full")
        default_input = ui.input("Default Value", placeholder="Optional").classes("w-full")
        required_switch = ui.switch("Required")

        def save_field():
            if not name_input.value:
                ui.notify("Name is required", type="warning")
                return

            options = None
            if type_select.value == "select" and options_input.value:
                options = {"choices": [o.strip() for o in options_input.value.split(",")]}

            create_field_definition(
                session,
                name=name_input.value,
                field_type=type_select.value,
                entity_type=entity_select.value,
                options=options,
                required=required_switch.value,
                default_value=default_input.value or None,
            )
            ui.notify(f"Field '{name_input.value}' created!", type="positive")
            add_dialog.close()
            # Reset form
            name_input.value = ""
            options_input.value = ""
            default_input.value = ""
            required_switch.value = False
            refresh_fields()

        with ui.row().classes("justify-end gap-2 mt-4"):
            ui.button("Cancel", on_click=add_dialog.close).props("flat")
            ui.button("Save", on_click=save_field).props("color=primary")

    session.close()


def render_custom_fields_for_entity(session, entity_type: str, entity_id: int):
    """Reusable component to render custom fields on entity detail pages.

    Call this within an existing page layout to show/edit custom fields for an entity.
    """
    field_defs = get_field_definitions_for_entity(session, entity_type)
    if not field_defs:
        return

    existing_values = get_field_values_for_entity(session, entity_type, entity_id)
    value_map = {v.field_definition_id: v.value for v in existing_values}

    with ui.card().classes("w-full mt-4"):
        ui.label("Custom Fields").classes("text-lg font-semibold mb-2")

        field_inputs = {}
        for field_def in field_defs:
            current_value = value_map.get(field_def.id, field_def.default_value or "")

            if field_def.field_type == "text":
                inp = ui.input(
                    field_def.name, value=current_value
                ).classes("w-full")
                field_inputs[field_def.id] = inp
            elif field_def.field_type == "number":
                inp = ui.number(
                    field_def.name, value=float(current_value) if current_value else None
                ).classes("w-full")
                field_inputs[field_def.id] = inp
            elif field_def.field_type == "date":
                inp = ui.input(
                    field_def.name, value=current_value, placeholder="YYYY-MM-DD"
                ).classes("w-full")
                field_inputs[field_def.id] = inp
            elif field_def.field_type == "select":
                choices = field_def.options.get("choices", []) if field_def.options else []
                inp = ui.select(
                    choices, value=current_value if current_value in choices else None,
                    label=field_def.name,
                ).classes("w-full")
                field_inputs[field_def.id] = inp
            elif field_def.field_type == "checkbox":
                inp = ui.checkbox(
                    field_def.name, value=current_value == "true"
                )
                field_inputs[field_def.id] = inp

        def save_custom_fields():
            for fid, inp in field_inputs.items():
                val = inp.value
                if isinstance(val, bool):
                    val = "true" if val else "false"
                elif val is not None:
                    val = str(val)
                set_field_value(session, fid, entity_type, entity_id, val)
            ui.notify("Custom fields saved!", type="positive")

        ui.button("Save Custom Fields", on_click=save_custom_fields).props(
            "color=primary size=sm"
        ).classes("mt-2")
