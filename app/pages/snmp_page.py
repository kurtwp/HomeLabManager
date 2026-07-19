"""SNMP Discovery and Device Info page."""

from nicegui import ui

from app.database.db import get_session_direct as get_session
from app.models.ip_address import IPAddress
from app.models.device import Device
from app.models.network import Network
from app.services.snmp_service import get_device_info, scan_network_snmp
from app.services.snmp_profiles import (
    get_all_profiles, create_profile, delete_profile,
    identify_device_type, identify_manufacturer,
)
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

            with ui.row().classes("gap-4 items-end flex-wrap"):
                version_select = ui.select(
                    {"1": "SNMPv1", "2c": "SNMPv2c", "3": "SNMPv3"},
                    value="2c",
                    label="SNMP Version",
                ).classes("w-36")
                community_input = ui.input(
                    "Community String", value="public", placeholder="public"
                ).classes("w-48")
                timeout_input = ui.number(
                    "Timeout (seconds)", value=2, min=1, max=10
                ).classes("w-36")

            # SNMPv3 credentials (shown only when v3 is selected)
            v3_container = ui.column().classes("w-full mt-3 gap-2")

            def toggle_v3_fields():
                v3_container.clear()
                if version_select.value == "3":
                    with v3_container:
                        ui.label("SNMPv3 Credentials").classes("text-sm font-semibold text-gray-400")
                        with ui.row().classes("gap-4 items-end flex-wrap"):
                            v3_user_input.set_visibility(True)
                            v3_auth_proto_select.set_visibility(True)
                            v3_auth_pass_input.set_visibility(True)
                            v3_priv_proto_select.set_visibility(True)
                            v3_priv_pass_input.set_visibility(True)
                            v3_sec_level_select.set_visibility(True)

            v3_user_input = ui.input("Username", placeholder="snmpuser").classes("w-44")
            v3_sec_level_select = ui.select(
                {"noAuthNoPriv": "No Auth/No Priv", "authNoPriv": "Auth/No Priv", "authPriv": "Auth + Priv"},
                value="authPriv",
                label="Security Level",
            ).classes("w-48")
            v3_auth_proto_select = ui.select(
                {"MD5": "MD5", "SHA": "SHA"},
                value="SHA",
                label="Auth Protocol",
            ).classes("w-36")
            v3_auth_pass_input = ui.input(
                "Auth Password", password=True, placeholder="auth passphrase"
            ).classes("w-48")
            v3_priv_proto_select = ui.select(
                {"DES": "DES", "AES": "AES"},
                value="AES",
                label="Privacy Protocol",
            ).classes("w-36")
            v3_priv_pass_input = ui.input(
                "Privacy Password", password=True, placeholder="priv passphrase"
            ).classes("w-48")

            # Initially hide v3 fields
            def update_v3_visibility():
                is_v3 = version_select.value == "3"
                v3_user_input.set_visibility(is_v3)
                v3_sec_level_select.set_visibility(is_v3)
                v3_auth_proto_select.set_visibility(is_v3)
                v3_auth_pass_input.set_visibility(is_v3)
                v3_priv_proto_select.set_visibility(is_v3)
                v3_priv_pass_input.set_visibility(is_v3)
                # Show/hide community for v1/v2c
                community_input.set_visibility(not is_v3)

            version_select.on("update:model-value", lambda: update_v3_visibility())
            update_v3_visibility()

            def get_snmp_args() -> dict:
                """Build SNMP arguments dict from the UI settings."""
                return {
                    "version": version_select.value,
                    "community": community_input.value or "public",
                    "timeout": int(timeout_input.value or 2),
                    "v3_user": v3_user_input.value or "",
                    "v3_sec_level": v3_sec_level_select.value,
                    "v3_auth_proto": v3_auth_proto_select.value,
                    "v3_auth_pass": v3_auth_pass_input.value or "",
                    "v3_priv_proto": v3_priv_proto_select.value,
                    "v3_priv_pass": v3_priv_pass_input.value or "",
                }

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

                        args = get_snmp_args()
                        info = get_device_info(ip_input.value, **args)

                        single_result.clear()
                        with single_result:
                            _render_device_info(info)
                            if info.reachable:
                                _render_save_snmp_button(info)

                    ui.button("Query", icon="search", on_click=query_single).props(
                        "color=primary"
                    )

            # --- Network Scan ---
            with ui.tab_panel(network_tab):
                with ui.card().classes("w-full"):
                    ui.label("SNMP Network Scan").classes("text-lg font-semibold mb-2")
                    ui.label(
                        "Scan all IPs in a network's subnet for SNMP-enabled devices."
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

                        # Get the network CIDR and generate all host IPs
                        import ipaddress as ipa
                        import threading
                        net_obj = session.query(Network).filter(Network.id == net_select.value).first()
                        if not net_obj:
                            ui.notify("Network not found", type="warning")
                            return

                        try:
                            network = ipa.ip_network(net_obj.cidr, strict=False)
                            ip_list = [str(ip) for ip in network.hosts()]
                        except ValueError:
                            ui.notify("Invalid network CIDR", type="negative")
                            return

                        # Limit to /24 max (254 hosts) to avoid very long scans
                        if len(ip_list) > 254:
                            ip_list = ip_list[:254]

                        network_results.clear()
                        with network_results:
                            with ui.row().classes("items-center gap-3"):
                                ui.spinner(size="lg")
                                ui.label(
                                    f"Scanning {len(ip_list)} IPs in {net_obj.cidr} for SNMP... "
                                    f"(~{len(ip_list) * int(timeout_input.value or 2) // 20 + 1} seconds)"
                                ).classes("text-sm text-gray-500")

                        args = get_snmp_args()

                        def _run_scan():
                            results = scan_network_snmp(ip_list, **args)

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
                                        _render_save_snmp_button(info)

                        thread = threading.Thread(target=_run_scan, daemon=True)
                        thread.start()

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
                        # Query ALL known IPs, not just device-linked ones
                        all_ips = session.query(IPAddress).all()
                        if not all_ips:
                            ui.notify("No IPs found. Run a scan first.", type="warning")
                            return

                        # Build IP list and map to device names
                        ip_list = []
                        ip_to_label = {}
                        for ip in all_ips:
                            ip_list.append(ip.address)
                            label = ip.hostname or ""
                            if ip.device:
                                label = ip.device.name
                            ip_to_label[ip.address] = label

                        known_results.clear()
                        with known_results:
                            with ui.row().classes("items-center gap-3"):
                                ui.spinner(size="lg")
                                ui.label(
                                    f"Querying {len(ip_list)} IPs via SNMP... "
                                    f"This may take up to {len(ip_list) * int(timeout_input.value or 2) // 20 + 1} seconds."
                                ).classes("text-sm text-gray-500")

                        args = get_snmp_args()

                        # Run queries in parallel to avoid blocking the event loop
                        from concurrent.futures import ThreadPoolExecutor, as_completed

                        results = []
                        with ThreadPoolExecutor(max_workers=20) as executor:
                            futures = {
                                executor.submit(get_device_info, ip, **args): ip
                                for ip in ip_list
                            }
                            for future in as_completed(futures):
                                ip = futures[future]
                                info = future.result()
                                results.append((ip_to_label.get(ip, ""), info))

                        known_results.clear()
                        with known_results:
                            responding = [(lbl, i) for lbl, i in results if i.reachable]
                            not_responding = [(lbl, i) for lbl, i in results if not i.reachable]

                            ui.notify(
                                f"Done: {len(responding)} responding, {len(not_responding)} not responding",
                                type="positive" if responding else "warning",
                            )
                            ui.label(
                                f"{len(responding)} responding, {len(not_responding)} not responding"
                            ).classes("text-sm mb-4")

                            if responding:
                                for label, info in sorted(responding, key=lambda x: x[1].ip):
                                    display = f"{info.ip}"
                                    if label:
                                        display += f" ({label})"
                                    if info.sys_name:
                                        display += f" — {info.sys_name}"
                                    with ui.expansion(
                                        display,
                                        icon="check_circle",
                                    ).classes("w-full"):
                                        _render_device_info(info)
                                        _render_save_snmp_button(info)

                            if not_responding:
                                with ui.expansion(
                                    f"Not responding ({len(not_responding)})", icon="cancel"
                                ).classes("w-full"):
                                    for label, info in sorted(not_responding, key=lambda x: x[1].ip):
                                        name_part = f" ({label})" if label else ""
                                        ui.label(f"• {info.ip}{name_part}").classes(
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


def _render_save_snmp_button(info):
    """Render a 'Save to Database' button that saves SNMP results as a Note on the IP."""

    def save_snmp_to_db():
        from app.database.db import get_session_direct
        from app.models.ip_address import IPAddress as IP
        from app.models.note import Note

        s = get_session_direct()
        ip_entry = s.query(IP).filter(IP.address == info.ip).first()

        if not ip_entry:
            ui.notify(f"IP {info.ip} not found in database. Run a scan first.", type="warning")
            s.close()
            return

        # Build note body
        note_body = ""
        if info.sys_name:
            note_body += f"**System Name:** {info.sys_name}\n\n"
        if info.sys_descr:
            note_body += f"**Description:** {info.sys_descr}\n\n"
        if info.sys_location:
            note_body += f"**Location:** {info.sys_location}\n\n"
        if info.sys_contact:
            note_body += f"**Contact:** {info.sys_contact}\n\n"
        if info.sys_uptime:
            note_body += f"**Uptime:** {info.sys_uptime}\n\n"
        if info.sys_object_id:
            note_body += f"**Object ID:** {info.sys_object_id}\n\n"

        if info.interfaces:
            note_body += f"**Interfaces ({info.interface_count}):**\n\n"
            note_body += "| Name | Status | Speed | MAC |\n|------|--------|-------|-----|\n"
            for iface in info.interfaces[:20]:
                status = "🟢 Up" if iface["status"] == "up" else "🔴 Down" if iface["status"] == "down" else iface["status"]
                note_body += f"| {iface['name']} | {status} | {iface['speed'] or '—'} | {iface['mac'] or '—'} |\n"

        # Save as a Note
        note = Note(
            title=f"SNMP Query — {info.sys_name or info.ip}",
            body=note_body,
            entity_type="ip",
            entity_id=ip_entry.id,
        )
        s.add(note)

        # Also update hostname if not set
        if info.sys_name and not ip_entry.hostname:
            ip_entry.hostname = info.sys_name

        s.commit()
        s.close()
        ui.notify(f"SNMP results saved to {info.ip}", type="positive")

    def create_device_from_snmp():
        """Auto-create a Device record from SNMP data."""
        from app.database.db import get_session_direct
        from app.models.ip_address import IPAddress as IP
        from app.models.device import Device as DevModel, DeviceType as DTModel

        s = get_session_direct()
        ip_entry = s.query(IP).filter(IP.address == info.ip).first()

        # Identify device type and manufacturer from SNMP
        dev_type_name = identify_device_type(info.sys_object_id)
        manufacturer = identify_manufacturer(info.sys_object_id, info.sys_descr)

        # Find or create the device type
        device_type_id = None
        if dev_type_name:
            dt = s.query(DTModel).filter(DTModel.name == dev_type_name).first()
            if not dt:
                dt = DTModel(name=dev_type_name)
                s.add(dt)
                s.flush()
            device_type_id = dt.id

        # Check if device already exists (by name or IP link)
        device_name = info.sys_name or f"SNMP-{info.ip}"
        existing = None
        if ip_entry and ip_entry.device_id:
            existing = s.query(DevModel).filter(DevModel.id == ip_entry.device_id).first()
        if not existing:
            existing = s.query(DevModel).filter(DevModel.name == device_name).first()

        if existing:
            # Update existing device
            if manufacturer and not existing.manufacturer:
                existing.manufacturer = manufacturer
            if device_type_id and not existing.device_type_id:
                existing.device_type_id = device_type_id
            if info.sys_location and not existing.location:
                existing.location = info.sys_location
            existing_name = existing.name
            s.commit()
            s.close()
            ui.notify(f"Updated existing device '{existing_name}'", type="positive")
        else:
            # Create new device
            new_dev = DevModel(
                name=device_name,
                manufacturer=manufacturer,
                device_type_id=device_type_id,
                location=info.sys_location or None,
                notes=f"Discovered via SNMP\nDescription: {info.sys_descr or '—'}\nObject ID: {info.sys_object_id or '—'}",
            )
            s.add(new_dev)
            s.flush()

            # Link to IP
            if ip_entry:
                ip_entry.device_id = new_dev.id
                if info.sys_name and not ip_entry.hostname:
                    ip_entry.hostname = info.sys_name

            s.commit()
            s.close()
            ui.notify(f"Created device '{device_name}' ({manufacturer or 'Unknown'} {dev_type_name or ''})", type="positive")

    with ui.row().classes("gap-2 mt-3"):
        ui.button(
            "Save as Note", icon="note_add", on_click=save_snmp_to_db
        ).props("color=primary outline")
        ui.button(
            "Create/Update Device", icon="add_circle", on_click=create_device_from_snmp
        ).props("color=green outline").tooltip(
            "Auto-create a device record from SNMP data (type, manufacturer, location)"
        )
