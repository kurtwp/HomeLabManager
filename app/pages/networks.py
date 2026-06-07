"""Networks management page."""

from nicegui import ui

from app.database.db import get_session_direct as get_session
from app.models.tag import Tag
from app.models.network import Network
from app.services.network_service import (
    create_network,
    get_all_networks,
    get_network_by_id,
    update_network,
    delete_network,
    get_network_utilization,
)
from app.services.scanner import scan_network
from app.utils.validators import is_valid_cidr, is_valid_vlan_id
from app.pages.layout import page_layout


def render_networks():
    """Render the networks management page."""
    page_layout()

    session = get_session()

    with ui.column().classes("page-container w-full"):
        with ui.row().classes("w-full items-center justify-between"):
            ui.label("Networks & VLANs").classes("text-3xl font-bold")
            with ui.row().classes("gap-2"):
                ui.button("Add Network", on_click=lambda: add_dialog.open()).props(
                    "color=primary icon=add"
                )
                ui.button("Delete All", on_click=lambda: confirm_delete_all_networks()).props(
                    "color=red icon=delete_sweep outline"
                )

        ui.separator().classes("my-4")

        # Filter controls
        all_tags = session.query(Tag).order_by(Tag.name).all()
        tag_options = {0: "All Tags"}
        tag_options.update({t.id: t.name for t in all_tags})

        with ui.row().classes("w-full gap-2 items-center"):
            tag_filter = ui.select(
                tag_options, value=0, label="Filter by Tag"
            ).classes("w-44")
            ui.button("Filter", on_click=lambda: refresh_networks()).props("flat")

        # Network list
        networks_container = ui.column().classes("w-full gap-3 mt-2")

        def refresh_networks():
            networks_container.clear()
            networks = get_all_networks(session)
            # Apply tag filter
            if tag_filter.value and tag_filter.value != 0:
                networks = [n for n in networks if any(t.id == tag_filter.value for t in n.tags)]
            with networks_container:
                if not networks:
                    ui.label("No networks found.").classes("text-gray-500")
                    return

                for net in networks:
                    util = get_network_utilization(session, net.id)
                    with ui.card().classes("w-full"):
                        with ui.row().classes("w-full items-center justify-between"):
                            with ui.column().classes("gap-1"):
                                with ui.row().classes("items-center gap-2"):
                                    ui.label(net.name).classes("text-lg font-semibold")
                                    if net.vlan_id:
                                        ui.badge(f"VLAN {net.vlan_id}").props(
                                            "color=blue outline"
                                        )
                                    # Tag chips
                                    for tag in net.tags:
                                        ui.html(
                                            f'<span style="font-size:0.65rem; padding:1px 8px; '
                                            f'border-radius:10px; background:{tag.color}20; '
                                            f'color:{tag.color}; border:1px solid {tag.color}40; '
                                            f'font-weight:500;">{tag.name}</span>'
                                        )
                                ui.label(net.cidr).classes("font-mono text-sm")
                                if net.description:
                                    ui.label(net.description).classes(
                                        "text-sm text-gray-500"
                                    )

                            with ui.row().classes("items-center gap-2"):
                                # Utilization
                                with ui.column().classes("items-center gap-0"):
                                    ui.label(
                                        f"{util.get('utilization_percent', 0)}%"
                                    ).classes("text-sm font-bold")
                                    ui.label(
                                        f"{util.get('used', 0)}/{util.get('total', 0)} IPs"
                                    ).classes("text-xs text-gray-500")

                                ui.button(
                                    icon="radar",
                                    on_click=lambda n=net: run_scan(n.id),
                                ).props("flat round").tooltip("Scan network")
                                ui.button(
                                    icon="visibility",
                                    on_click=lambda n=net: ui.navigate.to(
                                        f"/networks/{n.id}"
                                    ),
                                ).props("flat round").tooltip("View details")
                                ui.button(
                                    icon="delete",
                                    on_click=lambda n=net: confirm_delete(n),
                                ).props("flat round color=red").tooltip("Delete")

        def run_scan(network_id: int):
            ui.notify("Scanning network...", type="info")
            try:
                result = scan_network(session, network_id)
                ui.notify(
                    f"Scan complete: {result.hosts_found} hosts found, "
                    f"{result.hosts_added} added, {result.hosts_removed} marked inactive",
                    type="positive",
                )
                refresh_networks()
            except Exception as e:
                ui.notify(f"Scan failed: {e}", type="negative")

        def confirm_delete(net):
            with ui.dialog() as confirm, ui.card():
                ui.label(f"Delete network '{net.name}' ({net.cidr})?").classes("text-lg")
                ui.label(
                    "This will also remove all associated IP addresses."
                ).classes("text-red text-sm")
                with ui.row().classes("justify-end gap-2 mt-2"):
                    ui.button("Cancel", on_click=confirm.close).props("flat")
                    ui.button(
                        "Delete",
                        on_click=lambda: (
                            delete_network(session, net.id),
                            confirm.close(),
                            refresh_networks(),
                            ui.notify("Network deleted", type="warning"),
                        ),
                    ).props("color=red")
            confirm.open()

        def confirm_delete_all_networks():
            with ui.dialog() as dlg, ui.card():
                total = session.query(Network).count()
                ui.label(f"Delete ALL {total} networks?").classes("text-lg font-semibold")
                ui.label(
                    "This will delete all networks and their associated IP addresses. "
                    "This cannot be undone."
                ).classes("text-sm text-red")
                with ui.row().classes("justify-end gap-2 mt-3"):
                    ui.button("Cancel", on_click=dlg.close).props("flat")
                    ui.button("Delete All", on_click=lambda: (
                        _delete_all_networks(),
                        dlg.close(),
                    )).props("color=red")
            dlg.open()

        def _delete_all_networks():
            from app.models.ip_address import IPAddress
            count = session.query(Network).count()
            session.query(IPAddress).delete()
            session.query(Network).delete()
            session.commit()
            refresh_networks()
            ui.notify(f"Deleted {count} networks and all IPs", type="warning")

        refresh_networks()

    # Add network dialog
    with ui.dialog() as add_dialog, ui.card().classes("w-96"):
        ui.label("Add Network").classes("text-xl font-bold mb-2")
        name_input = ui.input("Name", placeholder="e.g. Main LAN").classes("w-full")
        cidr_input = ui.input("CIDR", placeholder="e.g. 192.168.1.0/24").classes("w-full")
        vlan_input = ui.input("VLAN ID (optional)", placeholder="e.g. 10").classes("w-full")
        gateway_input = ui.input("Gateway (optional)", placeholder="e.g. 192.168.1.1").classes(
            "w-full"
        )
        dns_input = ui.input("DNS Servers (optional)", placeholder="e.g. 1.1.1.1, 8.8.8.8").classes(
            "w-full"
        )
        desc_input = ui.textarea("Description (optional)").classes("w-full")

        def save_network():
            if not name_input.value or not cidr_input.value:
                ui.notify("Name and CIDR are required", type="warning")
                return
            if not is_valid_cidr(cidr_input.value):
                ui.notify("Invalid CIDR format", type="negative")
                return
            vlan_id = None
            if vlan_input.value:
                try:
                    vlan_id = int(vlan_input.value)
                    if not is_valid_vlan_id(vlan_id):
                        ui.notify("VLAN ID must be 1-4094", type="negative")
                        return
                except ValueError:
                    ui.notify("VLAN ID must be a number", type="negative")
                    return

            try:
                create_network(
                    session,
                    name=name_input.value,
                    cidr=cidr_input.value,
                    vlan_id=vlan_id,
                    gateway=gateway_input.value or None,
                    dns_servers=dns_input.value or None,
                    description=desc_input.value or None,
                )
                ui.notify("Network created!", type="positive")
                add_dialog.close()
                refresh_networks()
            except Exception as e:
                ui.notify(f"Error: {e}", type="negative")

        with ui.row().classes("justify-end gap-2 mt-2"):
            ui.button("Cancel", on_click=add_dialog.close).props("flat")
            ui.button("Save", on_click=save_network).props("color=primary")

    session.close()
