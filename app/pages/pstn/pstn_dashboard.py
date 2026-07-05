"""PSTN Dashboard — overview of telephony resources."""

from nicegui import ui

from app.database.pstn_db import get_pstn_session_direct as get_session
from app.models.pstn.number_range import NumberRange
from app.models.pstn.phone_number import PhoneNumber
from app.pages.layout import page_layout


def render_pstn_dashboard():
    """Render the PSTN overview dashboard."""
    page_layout()

    session = get_session()

    with ui.column().classes("page-container w-full"):
        ui.label("Telephony Dashboard").classes("text-3xl font-bold")
        ui.label("PSTN number management overview").classes("text-gray-500 mb-4")

        # Stats cards
        total_ranges = session.query(NumberRange).count()
        total_numbers = session.query(PhoneNumber).count()
        active_numbers = session.query(PhoneNumber).filter(PhoneNumber.status == "active").count()
        reserved_numbers = session.query(PhoneNumber).filter(PhoneNumber.status == "reserved").count()
        future_numbers = session.query(PhoneNumber).filter(PhoneNumber.status == "future_use").count()
        inactive_numbers = session.query(PhoneNumber).filter(PhoneNumber.status == "inactive").count()

        with ui.row().classes("w-full gap-4 flex-wrap"):
            _stat_card("Number Ranges", total_ranges, "view_list", "blue")
            _stat_card("Total Numbers", total_numbers, "phone", "purple")
            _stat_card("Active", active_numbers, "check_circle", "green")
            _stat_card("Reserved", reserved_numbers, "schedule", "orange")
            _stat_card("Future Use", future_numbers, "upcoming", "blue")
            _stat_card("Inactive", inactive_numbers, "cancel", "gray")

        ui.separator().classes("my-6")

        # Quick navigation
        with ui.row().classes("gap-4"):
            ui.button(
                "Manage Ranges",
                icon="view_list",
                on_click=lambda: ui.navigate.to("/pstn/ranges"),
            ).props("color=primary")
            ui.button(
                "Manage Numbers",
                icon="phone",
                on_click=lambda: ui.navigate.to("/pstn/numbers"),
            ).props("color=secondary")

        # Recent additions
        ui.separator().classes("my-6")
        ui.label("Recent Numbers").classes("text-xl font-semibold")

        recent = (
            session.query(PhoneNumber)
            .order_by(PhoneNumber.created_at.desc())
            .limit(10)
            .all()
        )

        if recent:
            columns = [
                {"name": "number", "label": "Number", "field": "number", "align": "left"},
                {"name": "extension", "label": "Ext", "field": "extension", "align": "left"},
                {"name": "type", "label": "Type", "field": "type", "align": "center"},
                {"name": "status", "label": "Status", "field": "status", "align": "center"},
                {"name": "assigned_to", "label": "Assigned To", "field": "assigned_to", "align": "left"},
            ]
            rows = [
                {
                    "id": pn.id,
                    "number": pn.number,
                    "extension": pn.extension or "—",
                    "type": pn.number_type,
                    "status": pn.status,
                    "assigned_to": pn.assigned_to or "—",
                }
                for pn in recent
            ]
            ui.table(columns=columns, rows=rows, row_key="id").classes("w-full").props(
                "flat bordered dense"
            )
        else:
            ui.label("No numbers tracked yet.").classes("text-gray-500 italic")

    session.close()


def _stat_card(label: str, value: int, icon: str, color: str):
    """Render a small stat card."""
    with ui.card().classes("w-44 text-center"):
        with ui.column().classes("items-center gap-1"):
            ui.icon(icon).classes(f"text-3xl text-{color}")
            ui.label(str(value)).classes("text-2xl font-bold")
            ui.label(label).classes("text-xs text-gray-500")
