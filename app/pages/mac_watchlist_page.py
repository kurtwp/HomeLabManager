"""MAC Watchlist page — manage known MACs and view unknown devices."""

from nicegui import ui

from app.database.db import get_session_direct as get_session
from app.services.mac_watchlist_service import (
    get_all_known_macs,
    add_known_mac,
    remove_known_mac,
    approve_all_current_macs,
    detect_unknown_macs,
)
from app.services.oui_service import lookup_manufacturer
from app.pages.layout import page_layout


def render_mac_watchlist():
    """Render the MAC watchlist page."""
    page_layout()

    session = get_session()

    with ui.column().classes("page-container w-full"):
        with ui.row().classes("w-full items-center justify-between"):
            ui.label("MAC Watchlist").classes("text-3xl font-bold")
            with ui.row().classes("gap-2"):
                ui.button("Add MAC", icon="add", on_click=lambda: add_dialog.open()).props(
                    "color=primary"
                )
                ui.button(
                    "Approve All Current",
                    icon="done_all",
                    on_click=lambda: do_approve_all(),
                ).props("color=green outline").tooltip(
                    "Add all currently active MACs to the known list"
                )

        ui.label(
            "Track known devices by MAC address. Unknown MACs are flagged on the dashboard."
        ).classes("text-gray-500 mb-4")

        ui.separator()

        # Unknown devices section
        ui.label("Unknown Devices").classes("text-xl font-semibold mt-4")
        unknown_container = ui.column().classes("w-full mt-2 gap-2")

        # Known MACs section
        ui.separator().classes("my-4")
        ui.label("Known MACs").classes("text-xl font-semibold")
        known_container = ui.column().classes("w-full mt-2 gap-2")

        def refresh_all():
            refresh_unknown()
            refresh_known()

        def refresh_unknown():
            unknown_container.clear()
            unknown = detect_unknown_macs(session)
            with unknown_container:
                if not unknown:
                    ui.label("No unknown MACs — all active devices are recognized.").classes(
                        "text-green text-sm italic"
                    )
                    return

                ui.label(f"{len(unknown)} unrecognized device(s) on the network").classes(
                    "text-sm text-orange mb-2"
                )

                columns = [
                    {"name": "mac", "label": "MAC Address", "field": "mac", "align": "left"},
                    {"name": "manufacturer", "label": "Manufacturer", "field": "manufacturer", "align": "left"},
                    {"name": "address", "label": "IP", "field": "address", "align": "left"},
                    {"name": "hostname", "label": "Hostname", "field": "hostname", "align": "left"},
                    {"name": "network", "label": "Network", "field": "network", "align": "left"},
                    {"name": "source", "label": "Source", "field": "source", "align": "center"},
                    {"name": "actions", "label": "Actions", "field": "actions", "align": "center"},
                ]
                rows = []
                for u in unknown:
                    try:
                        mfg = lookup_manufacturer(u["mac"]) or "—"
                    except Exception:
                        mfg = "—"
                    rows.append({
                        "id": u["ip_id"],
                        "mac": u["mac"],
                        "manufacturer": mfg,
                        "address": u["address"],
                        "hostname": u["hostname"],
                        "network": u["network"],
                        "source": u["source"],
                    })

                table = ui.table(columns=columns, rows=rows, row_key="id").classes(
                    "w-full"
                ).props("flat bordered dense")

                table.add_slot(
                    "body-cell-actions",
                    '''
                    <q-td :props="props">
                        <q-btn flat dense icon="check" color="green" size="sm"
                            @click="$parent.$emit('approve', props.row)"
                            label="Approve" />
                    </q-td>
                    ''',
                )

                def handle_approve(e):
                    row = e.args
                    mac = row["mac"]
                    name = row["hostname"] if row["hostname"] != "—" else row["address"]
                    add_known_mac(session, mac, name)
                    ui.notify(f"Approved {mac}", type="positive")
                    refresh_all()

                table.on("approve", handle_approve)

        def refresh_known():
            known_container.clear()
            known = get_all_known_macs(session)
            with known_container:
                if not known:
                    ui.label("No known MACs defined. Add them manually or click 'Approve All Current'.").classes(
                        "text-gray-500 italic"
                    )
                    return

                ui.label(f"{len(known)} known device(s)").classes("text-sm text-gray-400 mb-2")

                columns = [
                    {"name": "mac", "label": "MAC Address", "field": "mac", "align": "left"},
                    {"name": "name", "label": "Name", "field": "name", "align": "left"},
                    {"name": "notes", "label": "Notes", "field": "notes", "align": "left"},
                    {"name": "added", "label": "Added", "field": "added", "align": "left"},
                    {"name": "actions", "label": "", "field": "actions", "align": "center"},
                ]
                rows = [
                    {
                        "id": km.id,
                        "mac": km.mac_address,
                        "name": km.name,
                        "notes": km.notes or "—",
                        "added": km.added_at.strftime("%Y-%m-%d") if km.added_at else "—",
                    }
                    for km in known
                ]
                table = ui.table(columns=columns, rows=rows, row_key="id").classes(
                    "w-full"
                ).props("flat bordered dense")

                table.add_slot(
                    "body-cell-actions",
                    '''
                    <q-td :props="props">
                        <q-btn flat dense icon="delete" color="red" size="sm"
                            @click="$parent.$emit('remove', props.row)" />
                    </q-td>
                    ''',
                )

                def handle_remove(e):
                    row = e.args
                    remove_known_mac(session, row["id"])
                    ui.notify(f"Removed {row['mac']}", type="warning")
                    refresh_all()

                table.on("remove", handle_remove)

        def do_approve_all():
            count = approve_all_current_macs(session)
            ui.notify(f"Approved {count} new MAC(s)", type="positive")
            refresh_all()

        refresh_all()

    # Add MAC dialog
    with ui.dialog() as add_dialog, ui.card().classes("w-96"):
        ui.label("Add Known MAC").classes("text-xl font-bold mb-2")
        add_mac_input = ui.input("MAC Address *", placeholder="AA:BB:CC:DD:EE:FF").classes("w-full")
        add_name_input = ui.input("Name *", placeholder="e.g. Living Room TV").classes("w-full")
        add_notes_input = ui.input("Notes (optional)").classes("w-full")

        def save_new_mac():
            if not add_mac_input.value or not add_name_input.value:
                ui.notify("MAC and Name are required", type="warning")
                return
            add_known_mac(session, add_mac_input.value.strip(), add_name_input.value.strip(),
                         add_notes_input.value.strip() or None)
            ui.notify("MAC added to known list!", type="positive")
            add_dialog.close()
            refresh_all()

        with ui.row().classes("justify-end gap-2 mt-2"):
            ui.button("Cancel", on_click=add_dialog.close).props("flat")
            ui.button("Save", on_click=save_new_mac).props("color=primary")

    session.close()
