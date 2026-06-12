"""SNMP Discovery and Device Info page."""

from nicegui import ui

from app.database.db import get_session_direct as get_session
from app.models.ip_address import IPAddress
from app.models.device import Device
from app.models.network import Network
from app.services.snmp_service import get_device_info, scan_network_snmp
from app.services.network_service import get_all_networks
from app.services.device_service import update_device
from app.pages.layout import page_layout


def render_snmp():
    """Render the SNMP discovery page."""
    page_layout()

    session = get_session()

    with ui.column().classes("page-container w-full"):
        ui.label("SNMP Discovery").classes("text-3xl font-bold")
        ui.label(
            "Query devices via SNMP to gather system info, interfaces, and uptime."
        ).classes("text-gray-500 mb-4")

        ui.separator()

        # SNMP Settings
        with ui.card().classes("w-full mt-4"):
            ui.label("SNMP Settings").classes("text-lg font-semibold mb-2")
            with ui.row().classes("gap-4 items-end"):
                community_input = ui.input(
                    "Community String", value="public", placeholder="public"
                ).classes("w-48")
                timeout_input = ui.number(
                    "Timeout (seconds)", value=2, min=1, max=10
                ).classes("w-36")

        ui.separator().classes("my-4")

        with ui.tabs().classes("w-full") as tabs:
            single_tab = ui.tab("Query Single Device")
            network_tab = ui.tab("Scan Network")
            known_tab = ui.tab("Query Known Devices")

        with ui.tab_panels(tabs, value=single_tab).classes("w-full"):
            # --- Single Device Query ---
            with ui.tab_panel(single_tab):
                with ui.card().classes("w-full"):
                    ui.label("Query a Single IP").classes("text-lg font-semibold mb-2")

                    ip_input = ui.input(
                        "IP Address", placeholder="e.g. 192.168.2.1"
                    ).classes("w-64")

                    single_result = ui.column().classes("w-full mt-4")

                    def query_single():
                        if not ip_input.value:
                            ui.notify("Enter an IP address", type="warning")
                            return
                        single_result.clear()
                        with single_result:
                            ui.spinner(size="lg")

                        info = get_device_info(
                            ip_input.value,
                            community_input.value or "public",
                            int(timeout_input.value or 2),
                        )

                        single_result.clear()
                        with single_result:
                            _render_device_info(info)

                    ui.button("Query", icon="search", on_click=query_single).props(
                        "color=primary"
                    )

            # --- Network Scan ---
            with ui.tab_panel(network_tab):
                with ui.card().classes("w-full"):
                    ui.label("SNMP Network Scan").classes("text-lg font-semibold mb-2")
                    ui.label(
                        "Probe all known IPs in a network for SNMP-enabled devices."
                    ).classes("text-sm text-gray-500 mb-4")

                    networks = get_all_networks(session)
                    net_options = {n.id: f"{n.name} ({n.cidr})" for n in networks}

                    net_select = ui.select(
                        net_options, label="Network"
                    ).classes("w-64")

                    network_results = ui.column().classes("w-full mt-4")

                    def scan_network_for_snmp():
                        if not net_select.value:
                            ui.notify("Select a network", type="warning")
                            return

                        # Get all IPs in that network
                        ips = (
                            session.query(IPAddress)
                            .filter(IPAddress.network_id == net_select.value)
                            .all()
                        )
                        if not ips:
                            ui.notify("No IPs in this network. Run a ping scan first.", type="warning")
                            return

                        ip_list = [ip.address for ip in ips]
                        network_results.clear()
                        with network_results:
                            with ui.row().classes("items-center gap-3"):
                                ui.spinner(size="lg")
                                ui.label(
                                    f"Scanning {len(ip_list)} IPs for SNMP... "
                                    f"This may take up to {len(ip_list) * int(timeout_input.value or 2) // 20 + 1} seconds."
                                ).classes("text-sm text-gray-500")

                        results = scan_network_snmp(
                            ip_list,
                            community_input.value or "public",
                            int(timeout_input.value or 2),
                        )

                        network_results.clear()
                        with network_results:
                            if not results:
                                ui.label(
                                    "No SNMP-enabled devices found. Check community string."
                                ).classes("text-orange")
                                ui.notify("Scan complete — no SNMP devices found", type="warning")
                                return

                            ui.notify(f"Scan complete — {len(results)} SNMP devices found", type="positive")
                            ui.label(
                                f"Found {len(results)} SNMP-enabled devices out of {len(ip_list)} probed"
                            ).classes("text-lg font-semibold text-green mb-4")

                            for info in sorted(results, key=lambda x: x.ip):
                                with ui.expansion(
                                    f"{info.ip} — {info.sys_name or info.sys_descr[:60] or 'Unknown'}",
                                    icon="router",
                                ).classes("w-full"):
                                    _render_device_info(info)
                                    # Option to update device record
                                    _render_update_button(session, info)

                    ui.button(
                        "Scan for SNMP Devices", icon="radar", on_click=scan_network_for_snmp
                    ).props("color=primary")

            # --- Query Known Devices ---
            with ui.tab_panel(known_tab):
                with ui.card().classes("w-full"):
                    ui.label("Query Known Devices").classes("text-lg font-semibold mb-2")
                    ui.label(
                        "Run SNMP queries against all devices that have IP addresses assigned."
                    ).classes("text-sm text-gray-500 mb-4")

                    known_results = ui.column().classes("w-full mt-4")

                    def query_known_devices():
                        devices = session.query(Device).all()
                        device_ips = []
                        for d in devices:
                            for ip in d.ip_addresses:
                                device_ips.append((d, ip.address))

                        if not device_ips:
                            ui.notify("No devices with IPs found", type="warning")
                            return

                        known_results.clear()
                        with known_results:
                            with ui.row().classes("items-center gap-3"):
                                ui.spinner(size="lg")
                                ui.label(
                                    f"Querying {len(device_ips)} device IPs via SNMP... "
                                    f"This may take up to {len(device_ips) * int(timeout_input.value or 2) // 20 + 1} seconds."
                                ).classes("text-sm text-gray-500")

                        results = []
                        for device, ip in device_ips:
                            info = get_device_info(
                                ip,
                                community_input.value or "public",
                                int(timeout_input.value or 2),
                            )
                            results.append((device, info))

                        known_results.clear()
                        with known_results:
                            responding = [(d, i) for d, i in results if i.reachable]
                            not_responding = [(d, i) for d, i in results if not i.reachable]

                            ui.label(
                                f"{len(responding)} responding, {len(not_responding)} not responding"
                            ).classes("text-sm mb-4")

                            if responding:
                                for device, info in responding:
                                    with ui.expansion(
                                        f"{device.name} ({info.ip}) — {info.sys_name}",
                                        icon="check_circle",
                                    ).classes("w-full"):
                                        _render_device_info(info)
                                        _render_update_button(session, info)

                            if not_responding:
                                ui.label("Not responding to SNMP:").classes(
                                    "text-md font-semibold mt-4 text-orange"
                                )
                                for device, info in not_responding:
                                    ui.label(f"  • {device.name} ({info.ip})").classes(
                                        "text-sm text-gray-500"
                                    )

                    ui.button(
                        "Query All Devices", icon="device_hub", on_click=query_known_devices
                    ).props("color=primary")

    session.close()


def _render_device_info(info):
    """Render SNMP device info as a card."""
    if not info.reachable:
        with ui.card().classes("w-full bg-red-50 dark:bg-red-900"):
            ui.label(f"❌ {info.ip}: {info.error}").classes("text-red")
        return

    with ui.card().classes("w-full"):
        # System info table
        sys_data = [
            ("IP Address", info.ip),
            ("System Name", info.sys_name or "—"),
            ("Description", info.sys_descr or "—"),
            ("Location", info.sys_location or "—"),
            ("Contact", info.sys_contact or "—"),
            ("Uptime", info.sys_uptime or "—"),
            ("Object ID", info.sys_object_id or "—"),
            ("Interfaces", str(info.interface_count)),
        ]

        columns = [
            {"name": "prop", "label": "Property", "field": "prop", "align": "left"},
            {"name": "val", "label": "Value", "field": "val", "align": "left"},
        ]
        rows = [{"prop": k, "val": v} for k, v in sys_data]
        ui.table(columns=columns, rows=rows, row_key="prop").classes(
            "w-full"
        ).props("flat dense hide-header")

        # Interfaces
        if info.interfaces:
            ui.label("Interfaces").classes("text-md font-semibold mt-3 mb-1")
            iface_cols = [
                {"name": "name", "label": "Name", "field": "name", "align": "left"},
                {"name": "status", "label": "Status", "field": "status", "align": "center"},
                {"name": "speed", "label": "Speed", "field": "speed", "align": "right"},
                {"name": "mac", "label": "MAC", "field": "mac", "align": "left"},
            ]
            iface_rows = [
                {
                    "name": iface["name"],
                    "status": "🟢 Up" if iface["status"] == "up" else "🔴 Down" if iface["status"] == "down" else iface["status"],
                    "speed": iface["speed"] or "—",
                    "mac": iface["mac"] or "—",
                }
                for iface in info.interfaces[:20]  # Limit display
            ]
            ui.table(columns=iface_cols, rows=iface_rows, row_key="name").classes(
                "w-full"
            ).props("flat bordered dense")

            if len(info.interfaces) > 20:
                ui.label(f"... and {len(info.interfaces) - 20} more interfaces").classes(
                    "text-xs text-gray-500"
                )


def _render_update_button(session, info):
    """Render a button to update the device record with SNMP data."""
    # Find device by IP
    ip_entry = session.query(IPAddress).filter(IPAddress.address == info.ip).first()
    if not ip_entry or not ip_entry.device_id:
        return

    device = session.query(Device).filter(Device.id == ip_entry.device_id).first()
    if not device:
        return

    def apply_snmp_data():
        updates = {}
        if info.sys_name and not device.name.startswith(info.sys_name):
            # Don't overwrite name, just add to notes
            pass
        if info.sys_location and device.location != info.sys_location:
            updates["location"] = info.sys_location
        if info.sys_descr:
            # Append SNMP description to notes
            snmp_note = f"\n\n---\n**SNMP Info:**\n- {info.sys_descr}\n- Uptime: {info.sys_uptime}\n- Interfaces: {info.interface_count}"
            current_notes = device.notes or ""
            if "SNMP Info:" not in current_notes:
                updates["notes"] = current_notes + snmp_note

        if updates:
            update_device(session, device.id, **updates)
            ui.notify(f"Updated {device.name} with SNMP data", type="positive")
        else:
            ui.notify("No new data to update", type="info")

    ui.button(
        f"Apply SNMP data to '{device.name}'",
        icon="save",
        on_click=apply_snmp_data,
    ).props("flat color=primary size=sm").classes("mt-2")
