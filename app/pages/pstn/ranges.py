"""Number Ranges page — list, add, delete, view detail."""

from nicegui import ui

from app.database.pstn_db import get_pstn_session_direct as get_session
from app.models.pstn.number_range import NumberRange
from app.models.pstn.phone_number import PhoneNumber
from app.services.pstn_service import (
    create_range,
    get_all_ranges,
    get_range_by_id,
    delete_range,
    get_range_utilization,
    get_numbers_by_range,
)
from app.pages.layout import page_layout


def render_ranges():
    """Render the Number Ranges list page."""
    page_layout()

    session = get_session()

    with ui.column().classes("page-container w-full"):
        with ui.row().classes("w-full items-center justify-between"):
            ui.label("Number Ranges").classes("text-3xl font-bold")
            ui.button("Add Range", icon="add", on_click=lambda: add_dialog.open()).props(
                "color=primary"
            )

        ui.separator().classes("my-4")

        ranges_container = ui.column().classes("w-full gap-3")

        def refresh_ranges():
            ranges_container.clear()
            ranges = get_all_ranges(session)
            with ranges_container:
                if not ranges:
                    ui.label("No number ranges defined yet.").classes("text-gray-500 italic")
                    return

                for nr in ranges:
                    util = get_range_utilization(session, nr.id)
                    with ui.card().classes("w-full cursor-pointer").on(
                        "click", lambda e, r=nr: ui.navigate.to(f"/pstn/ranges/{r.id}")
                    ):
                        with ui.row().classes("w-full items-center justify-between"):
                            with ui.column().classes("gap-0"):
                                with ui.row().classes("items-center gap-2"):
                                    ui.label(nr.name).classes("text-lg font-semibold")
                                    _status_badge(nr.status)
                                    if nr.range_type == "sub":
                                        ui.badge("SUB").props("color=purple outline")
                                ui.label(
                                    f"{nr.range_start} → {nr.range_end}"
                                ).classes("text-sm font-mono text-gray-500")
                                if nr.provider:
                                    ui.label(f"Provider: {nr.provider}").classes(
                                        "text-xs text-gray-400"
                                    )

                            with ui.column().classes("items-end gap-1"):
                                ui.label(
                                    f"{util['allocated']} / {util['total']} allocated"
                                ).classes("text-sm")
                                ui.linear_progress(
                                    value=util["utilization_percent"] / 100,
                                    show_value=False,
                                ).classes("w-40")
                                with ui.row().classes("gap-1"):
                                    ui.button(
                                        icon="delete",
                                        on_click=lambda e, r=nr: _confirm_delete(r),
                                    ).props("flat round size=sm color=red")

        def _confirm_delete(nr: NumberRange):
            with ui.dialog() as confirm, ui.card():
                ui.label(f"Delete range '{nr.name}'?").classes("text-lg")
                ui.label(
                    "Numbers in this range will be unlinked (not deleted)."
                ).classes("text-sm text-gray-500")
                with ui.row().classes("justify-end gap-2 mt-2"):
                    ui.button("Cancel", on_click=confirm.close).props("flat")

                    def do_delete():
                        # Unlink numbers from this range
                        numbers = get_numbers_by_range(session, nr.id)
                        for pn in numbers:
                            pn.range_id = None
                        session.commit()
                        delete_range(session, nr.id)
                        ui.notify("Range deleted", type="warning")
                        confirm.close()
                        refresh_ranges()

                    ui.button("Delete", on_click=do_delete).props("color=red")
            confirm.open()

        refresh_ranges()

    # Add Range dialog
    with ui.dialog() as add_dialog, ui.card().classes("w-96"):
        ui.label("New Number Range").classes("text-xl font-bold mb-2")
        f_name = ui.input("Range Name *", placeholder="e.g. Main DID Block").classes("w-full")
        f_description = ui.input("Description", placeholder="Optional").classes("w-full")
        with ui.row().classes("w-full gap-2"):
            f_start = ui.input("Range Start *", placeholder="+15550100").classes("flex-1")
            f_end = ui.input("Range End *", placeholder="+15550199").classes("flex-1")
        with ui.row().classes("w-full gap-2"):
            f_country = ui.input("Country Code", placeholder="1").classes("w-20")
            f_area = ui.input("Area Code", placeholder="555").classes("w-24")
            f_prefix = ui.input("Prefix", placeholder="010").classes("w-24")
        f_provider = ui.input("Provider", placeholder="e.g. AT&T").classes("w-full")
        with ui.row().classes("w-full gap-2"):
            f_type = ui.select(
                {"master": "Master", "sub": "Sub-range"},
                value="master",
                label="Type",
            ).classes("flex-1")
            f_status = ui.select(
                {"active": "Active", "inactive": "Inactive", "reserved": "Reserved"},
                value="active",
                label="Status",
            ).classes("flex-1")
        f_total = ui.number("Total Numbers", value=0, min=0).classes("w-full")

        def save_new_range():
            if not f_name.value or not f_start.value or not f_end.value:
                ui.notify("Name, Start, and End are required", type="warning")
                return
            create_range(
                session,
                name=f_name.value.strip(),
                description=f_description.value.strip() or None,
                range_start=f_start.value.strip(),
                range_end=f_end.value.strip(),
                country_code=f_country.value.strip() or None,
                area_code=f_area.value.strip() or None,
                prefix=f_prefix.value.strip() or None,
                provider=f_provider.value.strip() or None,
                range_type=f_type.value,
                status=f_status.value,
                total_numbers=int(f_total.value) if f_total.value else 0,
            )
            ui.notify("Range created!", type="positive")
            add_dialog.close()
            refresh_ranges()

        with ui.row().classes("justify-end gap-2 mt-2"):
            ui.button("Cancel", on_click=add_dialog.close).props("flat")
            ui.button("Save", on_click=save_new_range).props("color=primary")

    session.close()


def render_range_detail(range_id: int):
    """Render the detail view for a single number range."""
    page_layout()

    session = get_session()
    nr = get_range_by_id(session, range_id)

    if not nr:
        with ui.column().classes("page-container"):
            ui.label("Range not found").classes("text-xl text-red")
        session.close()
        return

    util = get_range_utilization(session, range_id)
    numbers = get_numbers_by_range(session, range_id)

    with ui.column().classes("page-container w-full"):
        with ui.row().classes("items-center gap-4"):
            ui.button(icon="arrow_back", on_click=lambda: ui.navigate.to("/pstn/ranges")).props(
                "flat round"
            )
            ui.label(nr.name).classes("text-3xl font-bold")
            _status_badge(nr.status)
            if nr.range_type == "sub":
                ui.badge("SUB-RANGE").props("color=purple outline")

        ui.separator().classes("my-4")

        # Range info
        with ui.card().classes("w-full"):
            with ui.row().classes("gap-8 flex-wrap"):
                with ui.column().classes("gap-1"):
                    ui.label("Range").classes("text-xs text-gray-400")
                    ui.label(f"{nr.range_start} → {nr.range_end}").classes("font-mono")
                with ui.column().classes("gap-1"):
                    ui.label("Provider").classes("text-xs text-gray-400")
                    ui.label(nr.provider or "—")
                with ui.column().classes("gap-1"):
                    ui.label("Country/Area/Prefix").classes("text-xs text-gray-400")
                    ui.label(
                        f"+{nr.country_code or '?'} ({nr.area_code or '?'}) {nr.prefix or '?'}"
                    ).classes("font-mono")
                if nr.description:
                    with ui.column().classes("gap-1"):
                        ui.label("Description").classes("text-xs text-gray-400")
                        ui.label(nr.description)

        # Utilization
        with ui.card().classes("w-full mt-4"):
            ui.label("Utilization").classes("text-lg font-semibold")
            ui.linear_progress(
                value=util["utilization_percent"] / 100,
                show_value=False,
            ).classes("w-full mt-2")
            ui.label(
                f"{util['allocated']} allocated / {util['total']} total — "
                f"{util['utilization_percent']}%"
            ).classes("text-sm text-gray-500")
            with ui.row().classes("gap-4 mt-2"):
                ui.label(f"🟢 Active: {util['active']}").classes("text-sm")
                ui.label(f"🟠 Reserved: {util['reserved']}").classes("text-sm")
                ui.label(f"🔵 Future: {util['future_use']}").classes("text-sm")
                ui.label(f"⚫ Inactive: {util['inactive']}").classes("text-sm")

        # Numbers table
        ui.label("Numbers in this Range").classes("text-xl font-semibold mt-6")

        if numbers:
            # Natural sort
            import re

            def natural_key(pn):
                return [
                    int(c) if c.isdigit() else c.lower()
                    for c in re.split(r"(\d+)", pn.number)
                ]

            numbers_sorted = sorted(numbers, key=natural_key)

            columns = [
                {"name": "number", "label": "Number", "field": "number", "align": "left"},
                {"name": "extension", "label": "Ext", "field": "extension", "align": "left"},
                {"name": "type", "label": "Type", "field": "type", "align": "center"},
                {"name": "status", "label": "Status", "field": "status", "align": "center"},
                {"name": "assigned_to", "label": "Assigned To", "field": "assigned_to", "align": "left"},
                {"name": "department", "label": "Department", "field": "department", "align": "left"},
                {"name": "description", "label": "Description", "field": "description", "align": "left"},
            ]
            rows = [
                {
                    "id": pn.id,
                    "number": pn.number,
                    "extension": pn.extension or "—",
                    "type": pn.number_type,
                    "status": pn.status,
                    "assigned_to": pn.assigned_to or "—",
                    "department": pn.department or "—",
                    "description": pn.description or "—",
                }
                for pn in numbers_sorted
            ]
            ui.table(columns=columns, rows=rows, row_key="id").classes("w-full").props(
                "flat bordered dense"
            )
        else:
            ui.label("No numbers assigned to this range yet.").classes("text-gray-500 italic")

    session.close()


def _status_badge(status: str):
    """Render a colored status badge."""
    colors = {
        "active": "green",
        "inactive": "gray",
        "reserved": "orange",
    }
    color = colors.get(status, "gray")
    ui.badge(status.capitalize()).props(f"color={color}")
