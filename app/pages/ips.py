"""IP address listing and detail pages."""

from nicegui import ui

from app.database.db import get_session_direct as get_session
from app.models.ip_address import IPAddress, AssignmentType, IPStatus
from app.models.network import Network
from app.services.ip_service import create_ip, get_ips_for_network, get_ip_by_id, update_ip
from app.services.network_service import get_all_networks
from app.utils.formatters import format_timestamp
from app.pages.layout import page_layout


def render_ips():
    """Render the IP address list page."""
    page_layout()

    session = get_session()

    with ui.column().classes("page-container w-full"):
        with ui.row().classes("w-full items-center justify-between"):
            ui.label("IP Addresses").classes("text-3xl font-bold")
            ui.button("Add IP", on_click=lambda: add_dialog.open()).props(
                "color=primary icon=add"
            )

        ui.separator().classes("my-4")

        # Filter controls
        networks = get_all_networks(session)
        network_options = {0: "All Networks"}
        network_options.update({n.id: f"{n.name} ({n.cidr})" for n in networks})

        with ui.row().classes("w-full gap-2 items-center"):
            network_filter = ui.select(
                network_options, value=0, label="Network"
            ).classes("w-64")
            status_filter = ui.select(
                {"all": "All", "active": "Active", "inactive": "Inactive"},
                value="all",
                label="Status",
            ).classes("w-40")
            ui.button("Filter", on_click=lambda: refresh_ips()).props("flat")

        # IP table
        ip_container = ui.column().classes("w-full mt-4")

        def refresh_ips():
            ip_container.clear()
            with ip_container:
                query = session.query(IPAddress)
                if network_filter.value and network_filter.value != 0:
                    query = query.filter(IPAddress.network_id == network_filter.value)
                if status_filter.value != "all":
                    query = query.filter(
                        IPAddress.status == IPStatus(status_filter.value)
                    )
                ips = query.order_by(IPAddress.address).all()

                if not ips:
                    ui.label("No IP addresses found.").classes("text-gray-500")
                    return

                columns = [
                    {"name": "status", "label": "", "field": "status", "align": "center"},
                    {"name": "address", "label": "IP Address", "field": "address", "align": "left"},
                    {"name": "hostname", "label": "Hostname", "field": "hostname", "align": "left"},
                    {"name": "type", "label": "Type", "field": "type", "align": "center"},
                    {"name": "network", "label": "Network", "field": "network", "align": "left"},
                    {"name": "last_seen", "label": "Last Seen", "field": "last_seen", "align": "left"},
                ]

                rows = []
                for ip in ips:
                    rows.append({
                        "id": ip.id,
                        "status": "🟢" if ip.status == IPStatus.ACTIVE else "🔴" if ip.status == IPStatus.INACTIVE else "⚪",
                        "address": ip.address,
                        "hostname": ip.hostname or "—",
                        "type": ip.assignment_type.value.upper(),
                        "network": ip.network.name if ip.network else "—",
                        "last_seen": format_timestamp(ip.last_seen),
                    })

                table = ui.table(columns=columns, rows=rows, row_key="id").classes("w-full")
                table.props("flat bordered dense")

        refresh_ips()

    # Add IP dialog
    with ui.dialog() as add_dialog, ui.card().classes("w-96"):
        ui.label("Add IP Address").classes("text-xl font-bold mb-2")

        net_options = {n.id: f"{n.name} ({n.cidr})" for n in networks}
        addr_input = ui.input("IP Address *", placeholder="e.g. 192.168.1.100").classes("w-full")
        net_select = ui.select(net_options, label="Network *").classes("w-full")
        host_input = ui.input("Hostname", placeholder="e.g. my-server").classes("w-full")
        mac_input = ui.input("MAC Address", placeholder="AA:BB:CC:DD:EE:FF").classes("w-full")
        type_select = ui.select(
            {t.value: t.value.upper() for t in AssignmentType},
            value=AssignmentType.STATIC.value,
            label="Assignment Type",
        ).classes("w-full")
        notes_input = ui.textarea("Notes (markdown)").classes("w-full")

        def save_ip():
            if not addr_input.value or not net_select.value:
                ui.notify("IP address and network are required", type="warning")
                return
            try:
                create_ip(
                    session,
                    address=addr_input.value,
                    network_id=net_select.value,
                    hostname=host_input.value or None,
                    mac_address=mac_input.value or None,
                    assignment_type=AssignmentType(type_select.value),
                    notes=notes_input.value or None,
                )
                ui.notify("IP added!", type="positive")
                add_dialog.close()
                refresh_ips()
            except Exception as e:
                ui.notify(f"Error: {e}", type="negative")

        with ui.row().classes("justify-end gap-2 mt-2"):
            ui.button("Cancel", on_click=add_dialog.close).props("flat")
            ui.button("Save", on_click=save_ip).props("color=primary")

    session.close()


def render_ip_detail(ip_id: int):
    """Render a single IP's detail page with notes editor."""
    page_layout()

    session = get_session()
    ip = get_ip_by_id(session, ip_id)

    if not ip:
        with ui.column().classes("page-container"):
            ui.label("IP not found").classes("text-xl text-red")
        session.close()
        return

    with ui.column().classes("page-container w-full"):
        # Header
        with ui.row().classes("items-center gap-4"):
            ui.button(icon="arrow_back", on_click=lambda: ui.navigate.to("/ips")).props(
                "flat round"
            )
            ui.label(ip.address).classes("text-3xl font-bold font-mono")
            status_color = "green" if ip.status == IPStatus.ACTIVE else "red"
            ui.badge(ip.status.value.upper()).props(f"color={status_color}")
            ui.badge(ip.assignment_type.value.upper()).props("color=blue outline")

        ui.separator().classes("my-4")

        with ui.row().classes("w-full gap-4"):
            # Info panel
            with ui.card().classes("w-80"):
                ui.label("Details").classes("text-lg font-semibold mb-2")
                ui.label(f"Hostname: {ip.hostname or '—'}")
                ui.label(f"MAC: {ip.mac_address or '—'}")
                ui.label(f"Network: {ip.network.name if ip.network else '—'}")
                ui.label(f"Last Seen: {format_timestamp(ip.last_seen)}")
                ui.label(f"Created: {format_timestamp(ip.created_at)}")
                if ip.device:
                    ui.label(f"Device: {ip.device.name}")

            # Notes editor
            with ui.card().classes("flex-1"):
                ui.label("Notes (Markdown)").classes("text-lg font-semibold mb-2")

                with ui.tabs().classes("w-full") as tabs:
                    edit_tab = ui.tab("Edit")
                    preview_tab = ui.tab("Preview")

                with ui.tab_panels(tabs, value=edit_tab).classes("w-full"):
                    with ui.tab_panel(edit_tab):
                        notes_editor = ui.textarea(
                            value=ip.notes or ""
                        ).classes("w-full").props('rows="12"')

                        def save_notes():
                            update_ip(session, ip.id, notes=notes_editor.value)
                            ui.notify("Notes saved!", type="positive")

                        ui.button("Save Notes", on_click=save_notes).props(
                            "color=primary"
                        )

                    with ui.tab_panel(preview_tab):
                        ui.markdown(ip.notes or "*No notes yet*").classes("w-full")

    session.close()
