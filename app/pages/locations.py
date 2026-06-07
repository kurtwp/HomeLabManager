"""Physical location tracking page for devices."""

from nicegui import ui

from app.database.db import get_session_direct as get_session
from app.models.device import Device
from app.pages.layout import page_layout


def render_locations():
    """Render the physical locations overview page."""
    page_layout()

    session = get_session()

    with ui.column().classes("page-container w-full"):
        ui.label("Physical Locations").classes("text-3xl font-bold")
        ui.label("Track where your devices are physically located.").classes(
            "text-sm text-gray-500"
        )
        ui.separator().classes("my-4")

        # Get all devices that have location info
        all_devices = session.query(Device).order_by(Device.name).all()
        located_devices = [
            d for d in all_devices
            if d.location or d.rack_position or d.shelf
        ]
        unlocated_devices = [
            d for d in all_devices
            if not d.location and not d.rack_position and not d.shelf
        ]

        # Group by location
        locations = {}
        for dev in located_devices:
            loc = dev.location or "Unspecified Location"
            if loc not in locations:
                locations[loc] = []
            locations[loc].append(dev)

        # Summary stats
        with ui.row().classes("gap-4 mb-4"):
            with ui.card().classes("p-4"):
                ui.label(str(len(all_devices))).classes("text-3xl font-bold text-primary")
                ui.label("Total Devices").classes("text-sm text-gray-500")
            with ui.card().classes("p-4"):
                ui.label(str(len(located_devices))).classes("text-3xl font-bold text-green")
                ui.label("Located").classes("text-sm text-gray-500")
            with ui.card().classes("p-4"):
                ui.label(str(len(unlocated_devices))).classes("text-3xl font-bold text-orange")
                ui.label("No Location Set").classes("text-sm text-gray-500")
            with ui.card().classes("p-4"):
                ui.label(str(len(locations))).classes("text-3xl font-bold text-blue")
                ui.label("Locations").classes("text-sm text-gray-500")

        # Location groups
        if locations:
            for loc_name, devices in sorted(locations.items()):
                with ui.card().classes("w-full mb-4"):
                    with ui.row().classes("items-center gap-2"):
                        ui.icon("location_on").classes("text-primary text-xl")
                        ui.label(loc_name).classes("text-xl font-semibold")
                        ui.badge(str(len(devices))).props("color=primary")

                    columns = [
                        {"name": "name", "label": "Device", "field": "name", "align": "left"},
                        {"name": "rack", "label": "Rack Position", "field": "rack", "align": "center"},
                        {"name": "shelf", "label": "Shelf", "field": "shelf", "align": "center"},
                        {"name": "type", "label": "Type", "field": "type", "align": "center"},
                        {"name": "mac", "label": "MAC", "field": "mac", "align": "left"},
                    ]
                    rows = [
                        {
                            "id": d.id,
                            "name": d.name,
                            "rack": d.rack_position or "—",
                            "shelf": d.shelf or "—",
                            "type": d.device_type.name if d.device_type else "—",
                            "mac": d.mac_address or "—",
                        }
                        for d in devices
                    ]
                    table = ui.table(columns=columns, rows=rows, row_key="id").classes(
                        "w-full mt-2"
                    ).props("flat bordered dense")

                    table.add_slot(
                        "body-cell-name",
                        """
                        <q-td :props="props">
                            <a :href="'/devices/' + props.row.id"
                               class="text-primary cursor-pointer">
                                {{ props.row.name }}
                            </a>
                        </q-td>
                        """,
                    )

        # Devices without location
        if unlocated_devices:
            with ui.card().classes("w-full mt-4"):
                with ui.row().classes("items-center gap-2"):
                    ui.icon("location_off").classes("text-orange text-xl")
                    ui.label("Devices Without Location").classes("text-xl font-semibold")
                    ui.badge(str(len(unlocated_devices))).props("color=orange")

                for dev in unlocated_devices[:20]:
                    with ui.row().classes("items-center gap-2 ml-4 my-1"):
                        ui.label(f"• {dev.name}").classes("text-sm")
                        ui.button(
                            "Set Location",
                            on_click=lambda d=dev: ui.navigate.to(f"/devices/{d.id}"),
                        ).props("flat size=xs color=primary")

                if len(unlocated_devices) > 20:
                    ui.label(
                        f"... and {len(unlocated_devices) - 20} more"
                    ).classes("text-sm text-gray-500 ml-4")

    session.close()
